#!/usr/bin/python3
import argparse
import datetime
import re

import requests

BASE_URL = 'https://mobilevikings.pl/pl'
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = DATE_FORMAT + '_%H_%M_%S'
SIM_CARD_ID_TO_USE = '51217'


def html_div_to_sim_card(html_div):
    phone_no = re.compile('.+<img.+/>(.+)</div>', re.MULTILINE | re.DOTALL).findall(html_div)[0]\
        .replace('\n','').strip()
    sim_card_id = re.compile('.+routeParams\.subId == (\d+).+', re.MULTILINE | re.DOTALL).findall(html_div)[0]
    return {'phone_no': phone_no, 'sim_card_id': sim_card_id}


def find_all_sim_cards(client):
    # extracts all sim cards
    get_mysims_response = client.get(BASE_URL + '/mysims')
    print('get_mysims_response.status_code', get_mysims_response.status_code)
    found_sim_cards = list()
    if get_mysims_response.status_code == 200:
        sim_cards_html = re.compile('href="sim/\d+/(.*?)</a>', re.MULTILINE | re.DOTALL).findall(
            get_mysims_response.text)
        for one_sim_card_html in sim_cards_html:
            found_sim_cards.append(html_div_to_sim_card(one_sim_card_html))
    else:
        raise RuntimeError('When reading sim cards list response wasn not 200, but ',
                           get_mysims_response.status_code) from error
    return found_sim_cards


def begining_of_the_month():
    now = datetime.date.today()
    return datetime.date(now.year, now.month, 1)


def extract_csv(client, start_date, end_date, sim_card_to_extract):
    csv_response = client.get(
        BASE_URL + '/mysims/partials/' + sim_card_to_extract['sim_card_id'] + '/ng_history.html?export_format=csv&' +
        'ordering=asc&start=' + start_date.strftime(DATE_FORMAT) +
        '&end=' + end_date.strftime(DATE_FORMAT) + '&type=usage&period=custom')
    csv_response.encoding = 'utf-8'
    if csv_response.headers['Content-Type'] != 'text/csv':
        print("Resulting output is not CSV")
        print(csv_response.text)
    else:
        out_csv_file_name = str(datetime.datetime.today().strftime(DATETIME_FORMAT)) + \
                            '_FROM-' + start_date.strftime(DATE_FORMAT) + '_TO-' + end_date.strftime(
            DATE_FORMAT) + '.csv'
        with open(out_csv_file_name, 'w') as out_csv_file:
            out_csv_file.write(csv_response.text)
            print("saved to file " + out_csv_file_name)


def login_user(username, password):
    login_page_url = BASE_URL + '/account/login/'
    client = requests.session()
    # Retrieve the CSRF token first
    client.get(login_page_url)  # sets cookie
    csrftoken = client.cookies['csrftoken']
    login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken, next='/')
    r = client.post(login_page_url, data=login_data, headers=dict(Referer=login_page_url))
    print("Login response is ", r)
    errors_found = re.compile('<div class="messages">(.+?)</div>', re.MULTILINE | re.DOTALL)\
        .findall(r.text)
    if len(errors_found) > 0 and len(errors_found[0].strip()) > 0:
        raise RuntimeError("Error while logging in "+errors_found[0].strip())
    return client


begining_of_the_month = begining_of_the_month()
parser = argparse.ArgumentParser(description='Downloads history from mobilevikings.pl')
parser.add_argument('--user', help='username to use', required=True)
parser.add_argument('--password', help='password to use', required=True)
parser.add_argument('--start_date', help='start date to read history or 1st day of month will be used',
                    default=begining_of_the_month, type=lambda d: datetime.datetime.strptime(d, DATE_FORMAT))

args = parser.parse_args()
http_client = login_user(args.user, args.password)
all_sim_cards = find_all_sim_cards(http_client)
for one_sim_card in all_sim_cards:
    print("Extracting data for simcard ", one_sim_card)
    extract_csv(http_client, args.start_date, datetime.date.today(), one_sim_card)
