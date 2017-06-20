import re, requests, json, datetime, time, random, csv
import pandas as pd

# we want to make sure the death date isn't way before the discharge date
discharge_date_cushion = -14
avoid_block_seconds = 5

def findDeathDate(global_member_id, first_name, last_name, dob, discharge_date = 'NULL', state = ''):

	url = 'http://www.tributes.com/search/obituaries/?solr=&first=' + first_name + '&last=' + last_name + '&city=&state=' + state + '&search_type=Range+2010-NowAll&dod=&keywords='

	r = requests.get(url).text

	u = re.search('item_ids = (.+?);', r)

	jdata = json.loads(u.group(1))

	death_date = ''
	
	results = {'global_member_id': global_member_id, 'first_name': first_name, 'last_name': last_name, 'death_date': death_date}

	print discharge_date

	year, month, day = discharge_date.split('-')
	
	discharge_date = datetime.date(int(year), int(month), int(day))
	
	loose_discharge_date = discharge_date + datetime.timedelta(days = discharge_date_cushion)

	for row in jdata:

		death_year, death_month, death_day = row['dod'].split('/')

		obit_death = datetime.date(int(death_year), int(death_month), int(death_day))

		# debugging output
		print first_name.lower() + '\t' + last_name.lower() + '\t' + dob.replace('-', '/') + '\t' + str(loose_discharge_date)
		print row['first_name'] + '\t' +  row['last_name'] + '\t' +  row['dob'] + '\t' + str(obit_death)
		# end debugging output

		if row['first_name'] == first_name.lower() and row['last_name'] == last_name.lower() and row['dob'] == dob.replace('-', '/') and obit_death >= loose_discharge_date:

				death_date = obit_death

				results = {'global_member_id': global_member_id, 'first_name': first_name, 'last_name': last_name, 'death_date': death_date}

	return results;

#df = pd.read_csv('AnthemDeathDatesNeeded.csv')
df = pd.read_csv('DeclineDeathDatesNeeded.csv')

pats = df.to_dict('records')

death_list = []

i = 0

j = 0

print 'Success' + '\t' + 'Complete' + '\t' + 'Remaining' + '\t' + 'Total' + '\t' + 'Success Rate' + '\t' + 'Completion Rate'

with open('DeclineDeathResults.csv', 'wb') as f:
		writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['global_member_id', 'first_name', 'last_name', 'death_date'])
		writer.writeheader()

for row in pats:

	delay_until= datetime.datetime.now() + datetime.timedelta(seconds=avoid_block_seconds + random.randint(0, 1) - 0.5)

	results = findDeathDate(row['global_member_id'], row['first_name'], row['last_name'], row['person_birth_date'], row['discharge_date'])
	
	death_list.append(results)

	with open('DeclineDeathResults.csv', 'a') as f:
		writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['global_member_id', 'first_name', 'last_name', 'death_date'])
		writer.writerow(results)

	i += 1
	
	if results['death_date'] != '':
		j += 1

	print str(j) + '\t' + str(i) + '\t' + '\t' + str(len(df) - i) + '\t' + '\t' + str(len(df)) + '\t' + str(int(float(j) / float(i) * 100)) + '%' + '\t' + '\t' + str(int(float(i) / float(len(df)) * 100)) + '%'

	while datetime.datetime.now() < delay_until:
		time.sleep(0.5)
	else:
		continue
	
df2 = pd.DataFrame(death_list)

#df2.to_csv('AnthemDeathResults.csv')
#df2.to_csv('DeclineDeathResults.csv')