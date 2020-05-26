#!/usr/bin/python3

# Note : as we only fetch the first page, we assume an update can at most 
# add 5 new laws. So we restrict the pd diff compare to a truncate of the 
# previous df. This also assumes the dataframes are FIFO.

import time
import random
import pandas as pd

from pdf2image import convert_from_path
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import config, twitter
from utils import download_first_page_as_jpeg

base_url = "https://www.chambredesrepresentants.ma"

def get_dl_link(path):
    r = requests.get(base_url + path)
    s = BeautifulSoup(r.text, 'html.parser')
    link = s.find_all(class_='dp-block-r')[0].find_all('a', href=True)[0]['href']
    print("dl link: %s" % link)
    return link

def get_new_elements():
    r = requests.get(base_url + "/ar/%D8%A7%D9%84%D8%AA%D8%B4%D8%B1%D9%8A%D8%B9/%D8%A7%D9%84%D9%86%D8%B5%D9%88%D8%B5-%D8%A7%D9%84%D8%AA%D9%8A-%D8%B5%D8%A7%D8%AF%D9%82-%D8%B9%D9%84%D9%8A%D9%87%D8%A7-%D9%85%D8%AC%D9%84%D8%B3-%D8%A7%D9%84%D9%86%D9%88%D8%A7%D8%A8")
    r.encoding = "utf-8" # not needed ?

    soup = BeautifulSoup(r.text, 'html.parser')

    results = soup.find_all(class_="questionss_group")

    texts = {'text': [], 'path': [], 'dl_link': []}
    for text in results:
        texts['text'].append(text.find_all('p')[0].text)
        
        path = text.find_all('a', href=True)[0]['href']
        texts['path'].append(path)

        texts['dl_link'].append(get_dl_link(path))

    new_pd = pd.DataFrame(texts, columns=['text', 'path', 'dl_link'])

    return new_pd

def get_diff(prev_pd, new_pd):
    concat = pd.concat([new_pd.head(5), prev_pd.head(5)], sort=True)
    # use 'path' as a key to compare
    diff = concat.drop_duplicates(subset='path', keep=False)

    return diff

def format_tweet(row):
    h = "#نص_مصادق_عليه_بمجلس_النواب : "
    if len(h + row['text'] + " " + row['dl_link']) > 240:
        tmp = "... " + row['dl_link']
        l = len(h + "... ")
        return h + row['text'][:240 - l] + tmp
    return h + row['text'] + " " + row['dl_link']

def main():
    new_pd = get_new_elements()
    prev_pd = pd.read_csv(config.adopted_law_csv_file)

    diff = get_diff(prev_pd, new_pd)

    if not diff.empty:
        print("New elements: ", diff)

        for index, row in diff.iterrows():
            first_page = 'adopted/law_front_page_' + row['dl_link'].rpartition('/')[-1].replace('pdf,' 'jpg')
            download_law_front_page(row['dl_link'], first_page)
            
            t = format_tweet(row)
            twitter.tweet(t, False, front_page) 
            time.sleep(random.randint(2, 30))

        new_pd.to_csv(config.adopted_law_csv_file)
    else:
        print("Nothing new")


if __name__ == "__main__":
    main()
