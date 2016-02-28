from bs4 import BeautifulSoup
soup = BeautifulSoup(open("BillingUsage-ATT.html"), "html.parser")


def get_holder_mpc():
	# find first div with 'Monthly Plan Charges' title
	holder = soup.find(title = 'Monthly Plan Charges').parent
	# find span tag
	spans = holder.find_all('span')
	for span in spans:
		if 'class' in span.attrs and 'colorBlack' in span.attrs['class']:
			print float(span.text.strip()[1:])


if __name__ == '__main__':
	get_holder_mpc()
