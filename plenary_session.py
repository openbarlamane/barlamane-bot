#!/usr/bin/python3

import time
import random
import pandas as pd

from datetime import datetime

from pdf2image import convert_from_path
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import config, twitter
from utils import download_first_page_as_jpeg

base_url = "https://www.chambredesrepresentants.ma"

def display_df(df):
    print(df[['agenda', 'date']].to_string(index=False))

def get_dl_link(path):
    r = requests.get(path)
    s = BeautifulSoup(r.text, 'html.parser')

    try:
        link = s.find_all(class_='views-table cols-10 rtl')[0].find_all('a', href=True)[1]['href']
    except Exception as e:
        print("Exception finding download link : %s" % e)
        return ""

    print("dl link: %s" % link)
    return link

def get_new_elements():
    r = requests.get(base_url + "/ar/مراقبة-العمل-الحكومي/الأسـئلة-الشفوية-الشهرية")
    soup = BeautifulSoup(r.text, 'html.parser')

    elements = soup.find_all(class_="q-block3")

    sessions = {'agenda': [], 'date': [], 'path': [], 'dl_link': []}
    for elt in elements:
        sessions['agenda'].append(elt.text.split('\n')[5].split(':')[1].lstrip().rstrip())
        sessions['date'].append(elt.text.split('\n')[8].split(':')[1].lstrip().rstrip())
        
        path = base_url + elt.find_all('a', href=True)[0]['href']
        sessions['path'] = path

        sessions['dl_link'].append(get_dl_link(path))

    new_pd = pd.DataFrame(sessions, columns=['agenda', 'date', 'path', 'dl_link'])

    return new_pd

def get_diff(prev_pd, new_pd):
    concat = pd.concat([new_pd.head(5), prev_pd.head(5)], sort=True)
    print("Concat")
    display_df(concat)

    diff = concat.drop_duplicates(subset=['agenda', 'date'], keep=False)
    print("Diff")
    display_df(diff)

    return diff

def format_tweet(row):
    h = "#الأسئلة_الشفهية_الشهرية :"
    s = "%s %s يوم %s %s" % (h, row['agenda'], row['date'], row['dl_link'])

    if len(s) > 240:
        l = len(s)
        s = "%s %s... يوم %s %s" % (h, row['agenda'][:l - 3], row['date'], row['dl_link'])
    print("s = %s" % s)
    return s

def main(init=False):
    new_pd = get_new_elements()
    print("New pd")
    display_df(new_pd)

    if init:
        new_pd.to_csv(config.plenary_sessions_csv_file)
        return

    prev_pd = pd.read_csv(config.plenary_sessions_csv_file)
    print("Prev pd")
    display_df(prev_pd)
    diff = get_diff(prev_pd, new_pd)

    if not diff.empty:
        for index, row in diff.iterrows():
            # minutes [en] = procès verbal [fr] = محضر
            if row['dl_link'] != "":
                front_page = 'plenary_sessions/minutes_' + row['dl_link'].rpartition('/')[-1].replace('pdf', 'jpg')
                download_first_page_as_jpeg(row['dl_link'], front_page)
            
                t = format_tweet(row)
                twitter.tweet(t, False, front_page) 
            else:
                t = format_tweet(row)
                t += " (بدون محضر)"
                twitter.tweet(t, False) 
            time.sleep(random.randint(2, 30))

        new_pd.to_csv(config.adopted_law_csv_file)
    else:
        print("Nothing new")


if __name__ == "__main__":
    print(datetime.now().strftime("%d/%m/%Y %H:%M"))
    main()
