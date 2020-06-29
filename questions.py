#!/usr/bin/python3

"""
Fetch, insert to db and tweet new questions (oral/written).
Usage:
    $ python3.6 questions.py --oral # for oral questions
    $ python3.6 questions.py --written # for written questions
"""

import sys
import time
import random
import pymongo
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from barlapy.barlapy.parser import parse_questions_in_page

import config, twitter
from utils import clip_question_verbatim_screenshot

def format_tweet(qtype, row):
    if qtype == 'written':
        h = "#سؤال_كتابي : "
    elif qtype == 'oral':
        h = "#سؤال_شفوي : "

    a = '، '.join(row['author'])
    t = row['topic']
    u = row['url']

    if len(h + a + " - " + t + u) > 280:
        tmp = '... ' + u
        l = len(h + a + " - ")
        snippet = t[:280 -l]
    else:
        snippet = t
    return h + a + " - " + snippet + " " + u

def get_new_questions(questions_db, qtype):
    page = 0

    new_questions = []
    found_in_db = False
    while not found_in_db:
        if qtype == 'written':
            url = "https://www.chambredesrepresentants.ma/ar/%D8%A7%D9%84%D8%A3%D8%B3%D9%80%D8%A6%D9%84%D8%A9-%D8%A7%D9%84%D9%83%D8%AA%D8%A7%D8%A8%D9%8A%D8%A9"
        elif qtype == 'oral':
            url = "https://www.chambredesrepresentants.ma/ar/%D9%85%D8%B1%D8%A7%D9%82%D8%A8%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D9%84-%D8%A7%D9%84%D8%AD%D9%83%D9%88%D9%85%D9%8A/%D8%A7%D9%84%D8%A3%D8%B3%D9%80%D8%A6%D9%84%D8%A9-%D8%A7%D9%84%D8%B4%D9%81%D9%88%D9%8A%D8%A9"
        else:
            print("Wrong parameter")
            return []

        url += "?page=%s" % str(page)

        print("Fetching questions in page: %s" % url)
        questions = parse_questions_in_page(url)
        for q in questions:
            s = questions_db.find({"id": int(q.get_id()), "type": qtype})
            if s is not None and s.count() > 0:
                found_in_db = True
                break
            else:
                print("Question %s not in db: " % q.get_id())

            new_questions.append(q)

        page += 1

    return new_questions

def main(qtype):
    mongo = pymongo.MongoClient(config.mongo_db_url)
    db = mongo["barlamane"]
    questions = db["questions"]

    new_questions = get_new_questions(questions, qtype)

    if len(new_questions) == 0:
        print('No new questions')
        return

    print('There are %d new questions' % len(new_questions))
    for q in new_questions:

        d = q.to_dict()
        d['updated_at'] = datetime.now().isoformat()
        res = questions.insert_one(d)

        print("Inserted new question, _id: %s" % res.inserted_id)

        t = format_tweet(qtype, {'author': q.authors, 'topic': q.topic, 'url': q.get_url()})
        question_text = clip_question_verbatim_screenshot(q.get_url(), './written_questions_text')
        twitter.tweet(t, False, question_text)
        time.sleep(random.randint(2, 30))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Argument needed (--oral/-o, --written/-w)")
        sys.exit()

    print(datetime.now().strftime("%d/%m/%Y %H:%M"))
    if sys.argv[1] == '-w' or sys.argv[1] == "--written":
        main("written")
    elif sys.argv[1] == '-o' or sys.argv[1] == "--oral":
        main("oral")
