#!/usr/bin/python3

import logging
import time
import random
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

import config, twitter
from utils import download_first_page_as_jpeg

base_url = "https://www.chambredesrepresentants.ma"

# TODO: refactor: move to config.py
def get_dl_link(path):
    r = requests.get(base_url + path)
    s = BeautifulSoup(r.text, 'html.parser')

    try:
        link = s.find_all(class_='dp-section mb-4')[0].find_all('a', href=True)[0]['href']
        logging.debug("dl link: %s" % link)
    except Exception as e:
        logging.error("There was an exception retrieving download link: %s" % e)
        link = ""
    return link

def get_new_elements():
    r = requests.get(base_url + "/ar/التشريع/مشاريع-القوانين")
    soup = BeautifulSoup(r.text, 'html.parser')
    elements = soup.find_all(class_='col-md-6 col-lg-4 mb-4')

    law_projects = {'name': [], 'link': [], 'commission': [], 'dl_link': []}
    for elt in elements:
        law_name = elt.text.split('\n')[6].lstrip().rstrip()
        link = elt.find_all('a', href=True)[0]['href']
        commission_name = elt.find_all('a', href=True)[1].text.lstrip().rstrip()

        law_projects['name'].append(law_name)
        law_projects['link'].append(link)
        law_projects['commission'].append(commission_name)
        law_projects['dl_link'].append(get_dl_link(link))

    new_pd = pd.DataFrame(law_projects, columns=['name', 'link', 'commission', 'dl_link'])
    return new_pd

def get_diff(prev_pd, new_pd):
    concat = pd.concat([new_pd.head(7), prev_pd.head(7)], sort=True)
    diff = concat.drop_duplicates(subset=['link'], keep=False)
    logging.debug("diff: %s" % diff)
    return diff

def format_tweet(row):
    logging.debug("tweeting %s" % row)

    h = "#مشروع_قانون :"
    n = row['name']
    u = base_url + row['link']

    r = 280 - len(h)

    return "%s %s %s" % (h, n[0:r], u)

def main(init = False):
    new_pd = get_new_elements()

    if init:
        new_pd.to_csv(config.law_projects_csv_file)
        return

    prev_pd = pd.read_csv(config.law_projects_csv_file)
    diff = get_diff(prev_pd, new_pd)

    if diff.empty:
        logging.debug("No new elements")
    else:
        for index, row in diff.iterrows():
            t = format_tweet(row)

            if row['dl_link'] != '':
                first_page = "%s/%s" % (config.law_projects_downaloads, row['dl_link'].rpartition('/')[-1].replace('pdf', 'jpg'))
                download_first_page_as_jpeg(row['dl_link'], first_page)
                twitter.tweet(t, False, first_page)
            else:
                twitter.tweet(t)
            time.sleep(random.randint(2, 30))

        new_pd.to_csv(config.law_projects_csv_file)

if __name__ == "__main__":
    logging.basicConfig(filename='law_projects.log', level=logging.DEBUG, format='%(asctime)s %(levelname)7s %(message)s')
    main()
