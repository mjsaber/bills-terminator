from bs4 import BeautifulSoup
from twilio.rest import Client
import credentials
import utils
import pprint
import argparse

soup = BeautifulSoup(open('printBill.htm'), 'html.parser')
pp = pprint.PrettyPrinter(indent=4)
GROUP_HOLDER = '310-600-0358'


def get_all_billing_info():
    '''
    Get billing information for all users
    Return user_monthly_fee {xxx-xxx-xxxx: base_fee}, regular_data_fee
    '''
    user_monthly_fee = {}
    regular_data_fee = 0.0
    all_info_blobs = soup.find_all("div", {"class": "ng-scope", "ng-repeat": "ctn in ctnList"})
    for info_blob in all_info_blobs:
        is_mobile_share_data_fee = False
        user = None
        cell_blobs = info_blob.find_all("div", {"class": "faux-table-cell"})
        for cell_blob in cell_blobs:
            # print cell_blob.prettify()
            if is_user_blob(cell_blob):
                user = get_user(cell_blob)
                user_monthly_fee[user] = 0.0
                continue
            if user is not None:
                charges = get_monthly_charges(cell_blob)
                user_monthly_fee[user] += charges
                user = None
                continue
            if is_mobile_share_data(cell_blob):
                is_mobile_share_data_fee = True
                continue
            if is_mobile_share_data_fee:
                data_fee = utils.extract_fee(cell_blob.stripped_strings.next())
                regular_data_fee = data_fee
                # Group holder monthly charge includes data_fee for everyone
                user_monthly_fee[GROUP_HOLDER] -= data_fee
                is_mobile_share_data_fee = False
                continue
    return user_monthly_fee, regular_data_fee


def generate_billing_details(user_monthly_fee, regular_data_fee):
    billing_details = {}
    data_fee_per_person = regular_data_fee / len(user_monthly_fee.keys())
    for user, monthly_fee in user_monthly_fee.iteritems():
        phone_number = utils.alter_phone_format(user)
        billing_details[user] = {
            'phone': phone_number,
            'data': data_fee_per_person,
            'base': monthly_fee
        }
    return billing_details


def is_user_blob(cell_blob):
    user_blob = cell_blob.find("i", {"class": "icon-devices-mobilesmartphone"})
    return user_blob is not None


def is_mobile_share_data(cell_blob):
    '''
    Check if the blob is Mobile Share Value 20GB with Rollover Data blob
    '''
    blob = cell_blob.find("i", {"class": "icon-approval ng-hide", "ng-show": "mntlyChrg.showCheck"})
    if blob is not None:
        s = cell_blob.stripped_strings.next()
        if s == 'AT&T Unlimited Plus Multi Line':
            return True
    return False


def get_user(info_blob):
    '''
    Return user's phone number
    '''
    return utils.extract_phone_number(info_blob.b.next_element)


def get_monthly_charges(cell_blob):
    '''
    Return user's monthly charges
    '''
    blob = cell_blob.b.string
    if utils.is_fee(blob):
        return utils.extract_fee(blob)
    else:
        return 0.0


def get_message_body(user, info):
    import datetime
    month = datetime.date.today().month
    return "Dear {}: Your phone bill from {}.12 to {}.12 is {}, including shared data fee({}) and base fee({}). Please pay to Jun Ma at your convinence, thanks!".format(
        user, month, month + 1, info['data'] + info['base'], info['data'], info['base'])


def send_message(client, billing_details):
    for user, info in billing_details.iteritems():
        client.messages.create(
            to=info['phone'],
            from_=credentials.twilio['from'],
            body=get_message_body(user, info)
        )


def main(client, live_run):
    user_monthly_fee, regular_data_fee = get_all_billing_info()
    billing_details = generate_billing_details(user_monthly_fee, regular_data_fee)
    if not live_run:
        pp.pprint(billing_details)
    else:
        send_message(client, billing_details)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send SMS messages with billing information')
    parser.add_argument('--live-run', action='store_true', default=False)
    args = parser.parse_args()

    twilio_client = Client(credentials.twilio['account_sid'], credentials.twilio['auth_token'])

    main(client=twilio_client, live_run=args.live_run)
