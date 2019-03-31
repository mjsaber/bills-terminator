from bs4 import BeautifulSoup
from twilio.rest import Client
import credentials
import utils
import pprint
import argparse

soup = BeautifulSoup(open('Print Bill.html'), 'html.parser')
pp = pprint.PrettyPrinter(indent=4)
GROUP_HOLDER = '310.600.0358'


def get_all_billing_info():
    '''
    Get billing summary for all users
    Return user_monthly_fee {xxx-xxx-xxxx: base_fee}, shared_data_fee
    '''
    user_monthly_fee = {}
    shared_data_fee = 0
    all_info_blobs = soup.find_all("div", {"class": "ng-scope", "ng-repeat": "ctn in wirelessBill.ctnSummaryList"})
    for info_blob in all_info_blobs:
        is_mobile_share_data_fee = False
        user = None
        cell_blobs = info_blob.find_all("div", {"class": "faux-table-cell"})
        for cell_blob in cell_blobs:
            # print cell_blob.prettify()
            if is_user_blob(cell_blob):
                user = get_user(cell_blob)
                user_monthly_fee[user] = 0.0
                # print user
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
                shared_data_fee = data_fee
                # print 'Shared data fee is %s' % shared_data_fee
                is_mobile_share_data_fee = False
                continue
    return user_monthly_fee, shared_data_fee


def generate_billing_details(user_monthly_fee, regular_data_fee):
    billing_details = {}
    data_fee_per_person = round(regular_data_fee / len(user_monthly_fee.keys()), 2)
    for user, monthly_fee in user_monthly_fee.iteritems():
        phone_number = utils.alter_phone_format(user)
        billing_details[user] = {
            'phone': phone_number,
            'data': data_fee_per_person,
            'base': monthly_fee
        }
    return billing_details


def is_user_blob(cell_blob):
    user_blob = cell_blob.find("b", {"class": "ng-binding"})
    if user_blob is not None:
        return utils.is_phone_number(user_blob.stripped_strings.next())
    return False


def is_mobile_share_data(cell_blob):
    '''
    Check if the blob is `Shared plan charges` blob
    '''
    blob = cell_blob.find("span")
    if blob is not None:
        s = cell_blob.stripped_strings.next()
        if s == 'Shared plan charges':
            return True
    return False


def get_user(info_blob):
    '''
    Return user's phone number
    '''
    return utils.extract_phone_number(info_blob.stripped_strings.next())


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
    from datetime import datetime
    from dateutil import relativedelta
    today = datetime.today().day
    if today > 15:
        start_month = (datetime.now() + relativedelta.relativedelta(months=-1)).strftime("%b")
        end_month = (datetime.now()).strftime("%b")
    else:
        start_month = (datetime.now() + relativedelta.relativedelta(months=-2)).strftime("%b")
        end_month = (datetime.now() + relativedelta.relativedelta(months=-1)).strftime("%b")
    return "Dear {}: Your phone bill from {}.13 to {}.12 is {}, including shared data fee({}) and base fee({}). Please pay to Jun Ma at your convinence, thanks!".format(
        user, start_month, end_month, info['data'] + info['base'], info['data'], info['base'])


def send_message(client, billing_details, live_run=False):
    for user, info in billing_details.iteritems():
        if live_run:
            client.messages.create(
                to=info['phone'],
                from_=credentials.twilio['from'],
                body=get_message_body(user, info)
            )
        else:
            print info['phone'], get_message_body(user, info)


def main(client, live_run):
    user_monthly_fee, shared_data_fee = get_all_billing_info()
    # print user_monthly_fee, shared_data_fee
    billing_details = generate_billing_details(user_monthly_fee, shared_data_fee)
    send_message(client, billing_details, live_run)


class BillSummary(object):
    shared_data_fee = 0
    user_monthly_fee = {}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send SMS messages with billing information')
    parser.add_argument('--live-run', action='store_true', default=False)
    args = parser.parse_args()

    twilio_client = Client(credentials.twilio['account_sid'], credentials.twilio['auth_token'])

    main(client=twilio_client, live_run=args.live_run)
