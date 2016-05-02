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
		base = get_price(s)
		# print "{}: total = {}(base) + {}(data per user) = {}".format(phone, base, mpc/10, base + mpc/10)
		result[phone] = {'phone': trans_phone_format(phone), 'data': mpc/10, 'base': base}
	return result


def get_mpc():
	# find first div with 'Monthly Plan Charges' title
	holder = soup.find(title = 'Monthly Plan Charges').parent
	# find span tag
	spans = holder.find_all('span')
	for span in spans:
		if 'class' in span.attrs and 'colorBlack' in span.attrs['class']:
			holder_mpc = get_price(span);
			print 'Shared Monthly Plan Charges(data): {}'.format(holder_mpc)
			return holder_mpc


def get_price(tag):
	return float(tag.text.strip()[1:])


def get_phone(tag):
	return tag.text.split(' ')[2]


# from xxx-xxx-xxxx to +1xxxxxxxxxx
def trans_phone_format(phone):
	return '+1' + phone.replace('-', '')


def get_msg_body(user, info):
	return "Dear {}: Your monthly phone bill in total is {}, including shared data fee({}) and base fee({}). Please pay to Jun Ma at your convinence. This message is auto-generated, if you have any suggestion or concern, please contact Jun Ma at 310-614-6728. You're welcome to contribute to this project at https://github.com/mjsaber/bills-terminator. Thanks for your time.".format(user, info['data'] + info['base'], info['data'], info['base'])


def send_message(client, members):
	for user, info in members.iteritems():
		client.messages.create(
			to = info['phone'],
			from_ = credentials.twilio['from'],
			body = get_msg_body(user, info)
		)


def print_message(menbers):
	for user, info in members.iteritems():
		print "%s: data: %s base:%s\n" % (user, info['data'], info['base'])

if __name__ == '__main__':
	twilio_client = TwilioRestClient(credentials.twilio['account_sid'], credentials.twilio['auth_token'])
	# members = {'310-890-1520': {'phone': '+13108901520', 'data': 10.7, 'base': 20.18}}
	members = get_account_summary()
	print_message(members)
	send_message(twilio_client, members)
