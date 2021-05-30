#!/usr/bin/python3

import time
import random

from datetime import datetime

import pandas as pd

import requests
from bs4 import BeautifulSoup

import config, twitter
from utils import download_first_page_as_jpeg

base_url = "https://www.chambredesrepresentants.ma"

def get_dl_link(path):
    print("Dl link from : %s" % path)
    r = requests.get(base_url + path)
    s = BeautifulSoup(r.text, 'html.parser')

    # Sometimes pdf links are missing
    try:
        link = s.find_all(class_='dp-section mb-4')[0].find_all('a', href=True)[0]['href']
        print("dl link: ", link)
    except Exception as e:
        print("There was an exception retrieving download link: %s" % e)
        link = ""
    return link

def get_new_elements():
    r = requests.get(base_url + "/ar/التشريع/لائحة-مقترحات-القوانين")
    soup = BeautifulSoup(r.text, 'html.parser')
    elements = soup.find_all(class_='col-md-6 col-lg-4 mb-4')

    law_propositions = {'name': [], 'link': [], 'commission': [], 'dl_link': []}
    for elt in elements:
        law_name = elt.text.split('\n')[6].lstrip().rstrip()
        link = elt.find_all('a', href=True)[0]['href']
        commission_name = elt.find_all('a', href=True)[1].text.lstrip().rstrip()

        law_propositions['name'].append(law_name)
        law_propositions['link'].append(link)
        law_propositions['commission'].append(commission_name)
        law_propositions['dl_link'].append(get_dl_link(link))

    new_pd = pd.DataFrame(law_propositions, columns=['name', 'link', 'commission', 'dl_link'])
    return new_pd

def get_diff(prev_pd, new_pd):
    concat = pd.concat([new_pd.head(7), prev_pd.head(7)], sort=True)
    diff = concat.drop_duplicates(subset=['link'], keep=False)
    print("diff: ", diff)
    return diff

def format_tweet(row):
    h = "#مقترح_قانون : "
    n = row['name']
    u = base_url + row['link'] # dl_link instead no ?

    r = 280 - len(h)

    return "%s %s %s" % (h, n[0:r], u)

def main(init = False):
    new_pd = get_new_elements()

    if init:
        new_pd.to_csv(config.law_propositions_csv_file)
        return

    prev_pd = pd.read_csv(config.law_propositions_csv_file)
    diff = get_diff(prev_pd, new_pd)

    if diff.empty:
        print("No new elements")
    else:
        print("New elements: ", diff)

        for index, row in diff.iterrows():
            t = format_tweet(row)

            """
            if row['dl_link'] != '':
                first_page = 'law_propositions/' + row['dl_link'].rpartition('/')[-1].replace('pdf', 'jpg')
                download_first_page_as_jpeg(row['dl_link'], first_page)
                twitter.tweet(t, False, first_page)
            else:
                twitter.tweet(t)
            """
            twitter.tweet(t, True)
            time.sleep(random.randint(2, 30))

        new_pd.to_csv(config.law_propositions_csv_file)

if __name__ == "__main__":
    print(datetime.now().strftime("%d/%m/%Y %H:%M"))
    main()
