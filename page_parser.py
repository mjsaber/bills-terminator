from bs4 import BeautifulSoup
soup = BeautifulSoup(open("BillingUsage-ATT.html"), "html.parser")


def get_account_summary():
	mpc = get_mpc()
	# find all personal fee
	summary = soup.find_all("div", {"class": "float-right PadTop10 price-orange padRight20 "})
	for s in summary:
		t = s.find_previous_sibling("div")
		phone = get_phone(t)
		if phone == '310-600-0358':
			continue
		base = get_price(s)
		print "{}: total = {}(base) + {}(data per user) = {}".format(phone, base, mpc/10, base + mpc/10)


def get_mpc():
	# TODO:
	holder_insurance = 9.99
	# find first div with 'Monthly Plan Charges' title
	holder = soup.find(title = 'Monthly Plan Charges').parent
	# find span tag
	spans = holder.find_all('span')
	for span in spans:
		if 'class' in span.attrs and 'colorBlack' in span.attrs['class']:
			holder_mpc = get_price(span) - holder_insurance;
			print 'Shared Monthly Plan Charges(data): {}'.format(holder_mpc)
			return holder_mpc


def get_price(tag):
	return float(tag.text.strip()[1:])


def get_phone(tag):
	return tag.text.split(' ')[2]


if __name__ == '__main__':
	get_account_summary()
