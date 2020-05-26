#!/usr/bin/python3

import time
import random

import pandas as pd

import requests
from bs4 import BeautifulSoup

import config, twitter

base_url = "https://www.chambredesrepresentants.ma"

def get_new_elements():
    r = requests.get(base_url + "/ar/مراقبة-العمل-الحكومي/الأسـئلة-الشفوية")
    soup = BeautifulSoup(r.text, 'html.parser')

    elements = soup.find_all(class_='q-block3')

    df = {'topic': [], 'date': [], 'author': [], 'url': []}
    for elt in elements:
        # السؤال  :  فتح تحقيق حول إدعاءات بتلقي رشاوي من قبل أعوان...
        df['topic'].append(elt.text.split('\n')[5].split(':')[1].lstrip().rstrip())
        # التاريخ : 22/05/2020  ...
        df['date'].append(elt.text.split('\n')[8].split(':')[1].lstrip().rstrip())
        # صاحب(ة) السؤال                      مصطفى ابراهيمي
        df['author'].append(elt.text.split('\n')[12].split('صاحب(ة) السؤال')[1].lstrip().rstrip())

        df['url'].append(base_url + elt.find_all('a', href=True)[0]['href'])

    new_pd = pd.DataFrame(df, columns=['topic', 'date', 'author', 'url'])
    return new_pd

def display_df(df):
    print(df[['author', 'topic']].to_string(index=False))

def get_diff(prev_pd, new_pd):
    concat = pd.concat([new_pd.head(7), prev_pd.head(7)], sort=True)
    print("Concat")
    display_df(concat)

    diff = concat.drop_duplicates(subset=['author', 'topic'], keep=False)
    print("Diff")
    display_df(diff)

    return diff

def format_tweet(row):
    # todo : update
    h = "#سؤال_شفوي : "
    a = row['author']
    t = row['topic']
    u = row['url']

    if len(h + a + " - " + t) > 280:
        tmp = '... ' + u
        l = len(h + a + " - ")
        snippet = t[:280 -l]
    else:
        snippet = t
    return h + a + " - " + snippet + " " + u

def main(init=False):
    new_pd = get_new_elements()
    print("New pd")
    display_df(new_pd)
    
    if init:
        new_pd.to_csv(config.oral_questions_csv)
        return

    prev_pd = pd.read_csv(config.oral_questions_csv)
    diff = get_diff(prev_pd, new_pd)

    if not diff.empty:
        for index, row in diff.iterrows():
            t = format_tweet(row)
            twitter.tweet(t)
            time.sleep(random.randint(2, 30))

        new_pd.to_csv(config.oral_questions_csv)
    else:
        print("Nothing new")

if __name__ == "__main__":
    main(False)
