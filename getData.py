#!/usr/bin/python3
import argparse
import sys
import requests
import datetime

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = DATE_FORMAT + '_%H:%M:%S'

def begining_of_the_month():
    now = datetime.date.today()
    return datetime.date(now.year, now.month, 1)

def extract_csv(username, password):
    BASE_URL = 'https://mobilevikings.pl/pl'
    LOGIN_PAGE_URL = BASE_URL+'/account/login/'
    URL_TO_READ = BASE_URL+'/mysims/sim/51217/balance'

    client = requests.session()

    # Retrieve the CSRF token first
    client.get(LOGIN_PAGE_URL)  # sets cookie
    csrftoken = client.cookies['csrftoken']

    login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken, next='/')
    r = client.post(LOGIN_PAGE_URL, data=login_data, headers=dict(Referer=LOGIN_PAGE_URL))
    print ("Login response is ", r)
    csv_response = client.get(BASE_URL+'/mysims/partials/51217/ng_history.html?export_format=csv&' +
    'ordering=asc&start=2017-10-09&end=2017-10-16&type=usage&period=custom')
    csv_response.encoding = 'utf-8'
    out_csv_file_name = 'out.csv'
    with open(out_csv_file_name, 'w') as out_csv_file:
        out_csv_file.write(csv_response.text)
        print("saved to file "+out_csv_file_name)

begining_of_the_month = begining_of_the_month()
parser = argparse.ArgumentParser(description='Downloads history from mobielvikings.pl')
parser.add_argument('--user', help='username to use', required = True)
parser.add_argument('--password', help='password to use', required = True)
parser.add_argument('--start_date', help='start date to read history or 1st day of month will be used',
default=begining_of_the_month)

args = parser.parse_args()
extract_csv(args.user, args.password)