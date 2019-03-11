from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
import requests
import difflib
import filecmp
import os
import time
import datetime
import shutil
from wireless import Wireless #https://github.com/joshvillbrandt/wireless


d_id  = '[redacted]'

login_url = '[redacted]'
product_url = '[redacted]?d=' + d_id + '&c=1'
test_url = 'http://localhost:8888/page.html'

msg_temp_out_stock = 'Temporarily out of stock'
msg_sold_out = 'SOLD OUT!'

headers = {

'Host': '[redacted]',
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:53.0) Gecko/20100101 Firefox/53.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'en-US,en;q=0.5',
'Accept-Encoding': 'gzip, deflate, br',
'Cookie': '[redacted]',
'Connection': 'keep-alive',
'Upgrade-Insecure-Requests': '1'

}

def send_simple_message(to, subj, txt, timestamp):
	return requests.post(
		"https://api.mailgun.net/v3/[redacted].com/messages",
		auth=("api", "[redacted]"),
		data={"from": "<mailgun@[redacted].com>",
			  "to": to,
			  "subject": subj + " at " + timestamp,
			  "text": txt})


def extract_id(tag):
	soup = BeautifulSoup(tag, 'html.parser')
	try:
		return soup.select('span')[0].get('id')
	except Exception:
		return -1

def get_product_name(tag, soup):
	# this is ugly, but as long as they don't change their formatting this should work
	tag_id = extract_id(tag)
	if tag_id == -1:
		return 'Unable to determine ID'
	found_id = soup.select('#' + tag_id)
	try:
		return found_id[0].parent.parent.find_all('a')[1].getText()
	except Exception:
		return 'Unable to identify product'

while(True):

	timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

	try:
		resp = requests.get(product_url,headers=headers)
		#resp = requests.get(test_url)
	except ConnectionError as e:
		print("ConnectionError: " + str(e))

		# seems to usually happen when wifi is dropped, try toggling power
		wireless = Wireless()
		if (wireless.power()):
			print("Wireless currently enabled, powering off")
			wireless.power(False)
		else:
			print("Wireless currently disabled, powering on")
			wireless.power(True)

		time.sleep(30)
		continue #return to top of while loop

	if (resp.status_code != 200):
		#text the geek
		print(timestamp + ' Oops, text the geek')
		send_simple_message('[redacted]@txt.att.net', 'Something Broke', resp.text, timestamp)
	else:
		soup = BeautifulSoup(resp.text, 'html.parser')

		output_file = open('output.txt', 'w')

		for row in soup.find_all('tr'):
			# print len(row)
			if len(row) == 11:
				output_file.write(str(row))
				# print(row)
		output_file.close()

		# Something changed since last check, send alert
		if filecmp.cmp('output.txt', 'prev.txt') == False:
			print(timestamp + ' Holy moly something changed')

			send_to = ['[redacted]@txt.att.net','[redacted]@txt.att.net']

			file1 = open('output.txt', 'r')
			file2 = open('prev.txt', 'r')

			diff = difflib.ndiff(file1.readlines(), file2.readlines())

			#print('Whole diff : ' + ''.join(diff))

			#delta = 'Here is what the code looks like now:\n'
			delta = ''.join(x[2:] for x in diff if x.startswith('- '))

			# split the results into a list
			changes = delta.split('\n')
			# get rid of blanks
			changes = filter(None, changes)

			in_stock = ['Now In Stock:']
			out_stock = ['No Longer Available:']

			for change in changes:
				# an item went out of stock
				if msg_temp_out_stock in change or msg_sold_out in change:
					out_stock.append(get_product_name(change, soup))
				# an item is available
				else:
					in_stock.append(get_product_name(change, soup))

			if len(in_stock) > 1 and len(out_stock) > 1:
				summary = '\n'.join(in_stock) + '\n\n' + '\n'.join(out_stock)
			elif len(in_stock) > 1:
				summary = '\n'.join(in_stock)
			elif len(out_stock) > 1:
				summary = '\n'.join(out_stock)				
			else:
				summary = '\nSomething changed, not sure what'
				print('No apparent changes, saving logs for troubleshooting')
				shutil.copy2('prev.txt', 'logs/' + timestamp.replace(' ', '_') + 'prev.txt')
				shutil.copy2('output.txt', 'logs/' + timestamp.replace(' ', '_') + 'output.txt')
				#botched, just email the geek
				send_to = '[redacted]@gmail.com'

			# There was a problem identifying the product, keep copies for troubleshooting
			if 'Unable' in summary:
				print('Saving logs for ID troubleshooting...')
				shutil.copy2('prev.txt', 'logs/' + timestamp.replace(' ', '_') + 'prev.txt')
				shutil.copy2('output.txt', 'logs/' + timestamp.replace(' ', '_') + 'output.txt')
				#botched, just email the geek
				send_to = '[redacted]@gmail.com'

			send_simple_message(send_to, 'Something Changed', summary, timestamp)

			try:
				summary += '\n\nFor the geek:\n' + delta
			except UnicodeDecodeError:
				print('Saving logs for UnicodeDecodeError')
				shutil.copy2('prev.txt', 'logs/' + timestamp.replace(' ', '_') + 'prev.txt')
				shutil.copy2('output.txt', 'logs/' + timestamp.replace(' ', '_') + 'output.txt')

			print summary

		else:
			print(timestamp + ' Nothing to report')

		# Replace prev.txt with most recent scan
		os.remove('prev.txt')
		os.rename('output.txt', 'prev.txt')

	time.sleep(60)


