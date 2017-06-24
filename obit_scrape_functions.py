# Python 2.7

import csv
import datetime
import json
import re

import requests

def findDeathDate(global_member_id, first_name, last_name, dob, discharge_date_cushion, discharge_date='NULL', state=''):
	url = ('http://www.tributes.com/search/obituaries/?solr=&first=' + first_name + '&last=' + last_name
	       + '&city=&state=' + state + '&search_type=Range+2010-Now&dod=&keywords=')
	usr_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'}
	r = requests.get(url, headers=usr_agent).text
	u = re.search('item_ids = (.+?);', r)
	jdata = json.loads(u.group(1))
	death_date = ''
	tributes_id = ''
	tributes_url = ''
	match_count = 0
	results = {'global_member_id': global_member_id, 'first_name': first_name, 'last_name': last_name, 'death_date': death_date,
	           'time_generated': datetime.datetime.now(), 'match_count': match_count, 'tributes_id': tributes_id, 'tributes_url': tributes_url}
	year, month, day = discharge_date.split('-')
	discharge_date = datetime.date(int(year), int(month), int(day))
	loose_discharge_date = discharge_date + datetime.timedelta(days=discharge_date_cushion)
	for row in jdata:
		year, month, day = row['dod'].split('/')
		obit_death_date = datetime.date(int(year), int(month), int(day))
		match_first_name = row['first_name'] == first_name.lower()
		match_last_name = row['last_name'] == last_name.lower()
		match_dob = row['dob'] == dob.replace('-', '/')
		match_dod = obit_death_date >= loose_discharge_date
		if match_first_name and match_last_name and match_dob and match_dod:
			match_count += 1
			results['death_date'] = obit_death_date
			results['match_count'] = match_count
			search_id = row['id']
			real_id = re.search('search_item_' + str(search_id) + '(.*?) class="serif', r, re.DOTALL).group(1)
			real_id = re.search('/obituary/show/[^0-9]*?-([0-9]*?)"', real_id).group(1)
			try:
				results['tributes_id'] = real_id
			except:
				print 'Parser broke when looking for ID for ' + first_name + ' ' + last_name + '. DOB = ' + str(dob) + '. Global = ' + str(global_member_id)
				results['tributes_id'] = 'ERROR: PARSER FAIL'
				results['tributes_url'] = 'ERORR: PARSER FAIL. NEEDS MANUAL LOOKUP'
				continue
			results['tributes_url'] = 'http://www.tributes.com/obituary/show/' + real_id
	return results

def csvOutput(output_file, file_mode, write_mode, results=''):
	with open(output_file, file_mode) as f:
		writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['global_member_id', 'first_name', 'last_name', 'death_date', 'time_generated',
			                                                        'match_count', 'tributes_id', 'tributes_url'])
		if write_mode == 'header':
			writer.writeheader()
		if write_mode == 'results':
			writer.writerow(results)

def printResults(write_mode, console_results_headers, spaces_between_output_headers, start_time=None, rslt=None):
	hdrs = console_results_headers[:]	
	if write_mode == 'header':
		print ''
		for idx, val in enumerate(hdrs):
			hdrs[idx] = [val, len(val)]
		for h in hdrs:
			if h == hdrs[len(hdrs) - 1]:
				print h[0]
			else:
				print h[0] + ' ' * spaces_between_output_headers,
	if write_mode == 'results':
		for idx, val in enumerate(hdrs):
			hdrs[idx] = [val, len(val), rslt[idx]]
		for h in hdrs:
			if h == hdrs[len(hdrs) - 1]:
				print str(datetime.datetime.now() - start_time)
			else:
				print str(h[2]) + ' ' * (spaces_between_output_headers + h[1] - len(str(h[2]))),