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
avoid_block_seconds = 5
discharge_date_cushion = -14
input_file = sys.argv[1]
output_file = sys.argv[2]
overwrite_output = sys.argv[3]
complete_lookups = 0
successful_lookups = 0
skipped_lookups = 0
previous_global_ids = []

def findDeathDate(global_member_id, first_name, last_name, dob, discharge_date = 'NULL', state = ''):
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
		if (row['first_name'] == first_name.lower() and row['last_name'] == last_name.lower() and row['dob'] == dob.replace('-', '/')
		and obit_death_date >= loose_discharge_date):
			match_count += 1
			results['death_date'] = obit_death_date
			results['match_count'] = match_count
			search_id = row['id']
			real_id = re.search('search_item_' + str(search_id) + '(.*?) class="serif', r, re.DOTALL).group(1)
			real_id = re.search('/obituary/show/[^0-9]*?-([0-9]*?)"', real_id)
			results['tributes_id'] = real_id.group(1)
			results['tributes_url'] = 'http://www.tributes.com/obituary/show/' + real_id.group(1)
	return results

def csv_output(file_mode, write_mode, results=''):
	with open(output_file, file_mode) as f:
		writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['global_member_id', 'first_name', 'last_name', 'death_date', 'time_generated',
			                                                        'match_count', 'tributes_id', 'tributes_url'])
		if write_mode == 'header':
			writer.writeheader()
		if write_mode == 'results':
			writer.writerow(results)

def print_results(write_mode):
	if write_mode == 'header':
		print ('Success' + '\t' + 'Complete' + '\t' + 'Skipped' + '\t' + 'Remaining' + '\t' + 'Total' + '\t' + 'Success Rate' + '\t' + 'Completion Rate'
			    + '\t' * 2 + 'Time Elapsed')
	if write_mode == 'results':
		print (str(successful_lookups) + '\t' + str(complete_lookups) + '\t' * 2 + str(skipped_lookups) + '\t' + str(len(df) - complete_lookups - skipped_lookups) + '\t' * 2 + str(len(df)) + '\t'
		      + str(int(float(successful_lookups) / float(complete_lookups) * 100)) + '%' + '\t' * 2 + str(int(float(complete_lookups + skipped_lookups) / float(len(df)) * 100))
		      + '%' + '\t' * 3 + str(datetime.datetime.now() - start_time))

if overwrite_output == 1:
	csv_output('wb', 'header')

df = pd.read_csv(input_file)
pats = df.to_dict('records')

with open(output_file, 'rb') as csvfile:
	reader = csv.reader(csvfile)
	reader.next()
	for row in reader:
		previous_global_ids.append(row[0])

print_results('header')

for row in pats:
	if overwrite_output == '0' and str(row['global_member_id']) in previous_global_ids:
		complete_lookups += 1
		skipped_lookups += 1
		continue
	results = findDeathDate(row['global_member_id'], row['first_name'], row['last_name'], row['person_birth_date'], row['discharge_date'])
	delay_until= datetime.datetime.now() + datetime.timedelta(seconds=avoid_block_seconds + random.randint(0, 1) - 0.5)
	csv_output('a', 'results', results)
	complete_lookups += 1
	if results['death_date'] != '':
		successful_lookups += 1
	print_results('results')

	while datetime.datetime.now() < delay_until:
		time.sleep(0.25)
	else:
		continue
