# Python 2.7

import csv
import datetime
import json
import random
import re
import sys
import time

import pandas as pd
import requests

start_time = datetime.datetime.now()
avoid_block_seconds = 2
discharge_date_cushion = -14
input_file = sys.argv[1]
output_file = sys.argv[2]
overwrite_output = sys.argv[3].lower() in ['true', '1', 't', 'y', 'yes']
previous_global_ids = []
skipped_lookups = 0
successful_lookups = 0
complete_lookups = 0

df = pd.read_csv(input_file)
pats = df.to_dict('records')

spaces_between_output_headers = 3
console_results_headers = ['Success', 'Complete', 'Skipped', 'Remaining', 'Total',
                           'Success Rate', 'Completion Rate', 'Time Elapsed']

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

# Ready to be moved to another file
# import csv
def csvOutput(output_file, file_mode, write_mode, results=''):
	with open(output_file, file_mode) as f:
		writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['global_member_id', 'first_name', 'last_name', 'death_date', 'time_generated',
			                                                        'match_count', 'tributes_id', 'tributes_url'])
		if write_mode == 'header':
			writer.writeheader()
		if write_mode == 'results':
			writer.writerow(results)

# Figure out how to pass rslt as an argument, then make sure it changes
# no import needed
def printResults(write_mode, console_results_headers, rslt=None):
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

if overwrite_output:
	csvOutput(output_file, 'wb', 'header')

with open(output_file, 'rb') as csvfile:
	reader = csv.reader(csvfile)
	reader.next()
	for row in reader:
		previous_global_ids.append(row[0])

printResults('header', console_results_headers)

for row in pats:
	prior_id = str(row['global_member_id']) in previous_global_ids
	if not overwrite_output and prior_id:
		complete_lookups += 1
		skipped_lookups += 1
		continue
	results = findDeathDate(row['global_member_id'], row['first_name'], row['last_name'], row['person_birth_date'], discharge_date_cushion, row['discharge_date'])
	avoid_block_seconds += random.uniform(-0.5, 0.5)
	delay_until= datetime.datetime.now() + datetime.timedelta(seconds=avoid_block_seconds)
	csvOutput(output_file, 'a', 'results', results)
	complete_lookups += 1
	if results['death_date'] != '':
		successful_lookups += 1

	try:
		succ_pct = str(int(float(successful_lookups) / float(complete_lookups - skipped_lookups) * 100)) + '%'
	except ZeroDivisionError:
		succ_pct = '0%'                        
	   
	rslt = [str(successful_lookups),
	        str(complete_lookups),
	        str(skipped_lookups),
	        str(len(df) - complete_lookups),
	        str(len(df)),
	        succ_pct,
	        str(int(float(complete_lookups) / float(len(df)) * 100)) + '%',
	        str(datetime.datetime.now() - start_time)]

	printResults('results', console_results_headers, rslt)

	while datetime.datetime.now() < delay_until:
		time.sleep(0.25)
	else:
		continue
