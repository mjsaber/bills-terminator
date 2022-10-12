from bs4 import BeautifulSoup
from twilio.rest import Client
import credentials
import utils
import pprint
import argparse

pp = pprint.PrettyPrinter(indent=4)
GROUP_HOLDER = '310.600.0358'

UNLIMITED_PLUS_MULTI_LINE = 118.61	
BASE_FEE = {
    '310.600.0358': 25.01,
    '310.600.7354': 25.01,
    '310.614.6728': 25.01,
    '310.614.8638': 40.01,
    '310.745.8790': 25.01,
    '310.745.9890': 25.01,
    '310.751.4233': 25.01,
    '310.773.1401': 25.01,
    '310.871.5381': 25.02,
    '814.441.8926': 26.21,
}


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


def get_message_body(user, info):
    from datetime import datetime
    from dateutil import relativedelta
    today = datetime.today().day
    if today > 15:
        start_month = (datetime.now() + relativedelta.relativedelta(months=-1)).strftime("%b")
        end_month = (datetime.now() + relativedelta.relativedelta(months=0)).strftime("%b")
    else:
        start_month = (datetime.now() + relativedelta.relativedelta(months=-2)).strftime("%b")
        end_month = (datetime.now() + relativedelta.relativedelta(months=-1)).strftime("%b")
    return "Dear {}: Your phone bill from {}.13 to {}.12 is {}, including shared data fee({}) and base fee({}). Please pay to Jun Ma at your convinence, thanks!".format(
        user, start_month, end_month, info['data'] + info['base'], info['data'], info['base'])


def send_message(client, billing_details):
    for user, info in billing_details.iteritems():
        if client is not None:
            client.messages.create(
                to=info['phone'],
                from_=credentials.twilio['from'],
                body=get_message_body(user, info)
            )
        else:
            print info['phone'], get_message_body(user, info)


def get_all_billing_info():
    sum = 0
    for phone, base_fee in BASE_FEE.iteritems():
        sum += base_fee
    print sum + UNLIMITED_PLUS_MULTI_LINE
    return 0, 0

def main(client):
    # user_monthly_fee, shared_data_fee = get_all_billing_info()
    # print user_monthly_fee, shared_data_fee
    billing_details = generate_billing_details(BASE_FEE, UNLIMITED_PLUS_MULTI_LINE)
    send_message(client, billing_details)


class BillSummary(object):
    shared_data_fee = 0
    user_monthly_fee = {}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send SMS messages with billing information')
    parser.add_argument('--live-run', action='store_true', default=False)
    args = parser.parse_args()

    if args.live_run:
        twilio_client = Client(credentials.twilio['account_sid'], credentials.twilio['auth_token'])
    else:
        twilio_client = None

    main(client=twilio_client)
