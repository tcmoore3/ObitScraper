# Python 2.7

import csv
import datetime
import random
import sys
import time

import pandas as pd
import requests

import obitscrape

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

if overwrite_output:
    obitscrape.csvOutput(output_file, 'wb', 'header')

try:
    with open(output_file, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()
        for row in reader:
            previous_global_ids.append(row[0])
except:
    previous_global_ids = []
    obitscrape.csvOutput(output_file, 'wb', 'header')

obitscrape.printResults('header', console_results_headers, spaces_between_output_headers)

for row in pats:
    prior_id = str(row['global_member_id']) in previous_global_ids
    if not overwrite_output and prior_id:
        complete_lookups += 1
        skipped_lookups += 1
        continue
    results = obitscrape.findDeathDate(row['global_member_id'], row['first_name'], row['last_name'], row['person_birth_date'], discharge_date_cushion, row['discharge_date'])
    avoid_block_seconds += random.uniform(-0.5, 0.5)
    delay_until= datetime.datetime.now() + datetime.timedelta(seconds=avoid_block_seconds)
    obitscrape.csvOutput(output_file, 'a', 'results', results)
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

    obitscrape.printResults('results', console_results_headers, spaces_between_output_headers, start_time, rslt)

    while datetime.datetime.now() < delay_until:
        time.sleep(0.25)
    else:
        continue
