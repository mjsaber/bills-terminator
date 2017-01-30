import credentials
from bs4 import BeautifulSoup
from twilio.rest import TwilioRestClient

soup = BeautifulSoup(open("Billing & Usage - AT&T.htm"), "html.parser")


def get_account_summary():
    mpc = get_mpc()
    # find all personal fee
    # personal fee class
    summary = soup.find_all("div", {"class": "float-right accRow bold padRight20 colorBlack"})
    result = {}
    for s in summary:
        t = s.find_previous_sibling("div")
        phone = get_phone(t)
        if phone == 'Charges':
            continue
        base = get_price(s)
        # print "{}: total = {}(base) + {}(data per user) = {}".format(phone, base, mpc/10, base + mpc/10)
        result[phone] = {'phone': trans_phone_format(phone), 'data': mpc / 10, 'base': base}

    # rearrange distribution of extra data charge to make it more fair
    if soup.find_all(text='Data overage charge'):
        result = trans_extra_data_fee(result)

    return result


def get_mpc():
    # find first div with 'Monthly Plan Charges' title
    holder = soup.find(title='Monthly Plan Charges').parent
    # find span tag
    spans = holder.find_all('span')
    for span in spans:
        if 'class' in span.attrs and 'colorBlack' in span.attrs['class']:
            holder_mpc = get_price(span)
            print 'Shared Monthly Plan Charges(data): {}'.format(holder_mpc)
            return holder_mpc


def get_price(tag):
    return float(tag.text.strip()[1:])


def get_phone(tag):
    return tag.text.split(' ')[2]


# from xxx-xxx-xxxx to +1xxxxxxxxxx
def trans_phone_format(phone):
    return '+1' + phone.replace('-', '')


# from xxx.xxx.xxxx to xxx-xxx-xxxx
def trans_phone_format2(phone):
    return '{}-{}-{}'.format(phone.split('.')[0], phone.split('.')[1], phone.split('.')[2])


def get_msg_body(user, info):
    msg = "Dear {}: Your monthly phone bill in total is {}, including shared data fee: {}, "\
        .format(user, info['data'] + info['base'] + info.get('extra_data_fee', 0), info['data'])
    if info.get('extra_data_fee') > 0:
        msg += "extra data fee (your monthly data usage exceed 2G, " \
               "this is calculated by the percentage of extra data usage): {}, ".format(info['extra_data_fee'])
    msg += "base fee: {}. Please pay to Jun Ma at your convenience, thanks!".format(info['base'])
    return msg


def send_message(client, members):
    for user, info in members.iteritems():
        client.messages.create(
            to=info['phone'],
            from_=credentials.twilio['from'],
            body=get_msg_body(user, info)
        )


def print_message(menbers):
    for user, info in members.iteritems():
        print get_msg_body(user, info)


# If extra fee is charged, go download https://www.att.com/olam/billUsageTiles.myworld and save as "billusage.htm" 
def trans_extra_data_fee(members):  # need to judge there is extra usage
    owner_phone = "310-600-0358"
    data_plan = 20.0
    usage_quota = data_plan * .1
    soup_data = BeautifulSoup(open("billusage.htm"), "html.parser")
    extra_datausage = float(
        soup_data.find_all("div", {"class": "additionalColCenter"})[1].text.split('M')[0].replace(',', '')
    ) / 1024  # in GB
    total_datausage = data_plan + extra_datausage

    ths = soup_data.find_all("th", {"class": "PadTop0 BotSolidBorder borderRightSolid borderLeftSolid left",
                                    "headers": "header1"})
    extra_data_usage_dict = {}

    # print(ths[0].text[4:-1])
    real_extra_usage = total_datausage * float(ths[0].text[4:-1]) / 100 - usage_quota
    extra_data_usage_dict[owner_phone] = real_extra_usage if real_extra_usage >= 0 else 0

    total_extra_percent = extra_data_usage_dict[owner_phone]
    for i in range(1, 10):
        phone = ths[i].text[0:12]
        phone = trans_phone_format2(phone)
        real_extra_usage = total_datausage * float(ths[i].text[13:-1]) / 100 - usage_quota
        extra_data_usage_dict[phone] = real_extra_usage if real_extra_usage >= 0 else 0
        total_extra_percent += extra_data_usage_dict[phone]

    extra_fee_holder = soup_data.find_all("div", {"class": "additionalColRight"})
    extra_fee = float(extra_fee_holder[1].text[1:])

    for user, info in members.iteritems():
        # members[user]['data'] = members[user]['data'] - extra_fee / 10 + extra_fee * extra_data_usage_dict[
        #     user] / total_extra_percent
        extra_data_fee = round(extra_fee * extra_data_usage_dict[user] / total_extra_percent, 2)
        members[user]['extra_data_fee'] = extra_data_fee
    return members


if __name__ == '__main__':
    twilio_client = TwilioRestClient(credentials.twilio['account_sid'], credentials.twilio['auth_token'])
    # members = {'310-890-1520': {'phone': '+13108901520', 'data': 10.7, 'base': 20.18}}
    members = get_account_summary()
    # print_message(members)
    send_message(twilio_client, members)
