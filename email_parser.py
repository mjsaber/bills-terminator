import sys
import imaplib
import getpass
import email
import datetime
import credentials
from bs4 import BeautifulSoup

conn = imaplib.IMAP4_SSL('imap.gmail.com')
try:
	conn.login(credentials.gmail['account'], credentials.gmail['password'])
except imaplib.IMAP4.error:
    print "LOGIN FAILED!!! "
        
conn.select('Money', readonly=1) # Select inbox or default namespace
retcode, messages = conn.search(None, '(UNSEEN)')
print messages
if retcode == 'OK':
    for num in messages:
        typ, data = conn.fetch(num,'(RFC822)')
        # print 'Processing :', typ, data
        # print data[0][1]
        soup = BeautifulSoup(data[0][1], "html.parser")
        print(soup.prettify())
        # msg = email.message_from_string(data[0][1])
        # typ, data = conn.store(num,'-FLAGS','\\Seen')
        # if ret == 'OK':
        #     print data,'\n',30*'-'
        #     print msg
