#!/usr/bin/python3

"""
Fetch, insert to db and tweet new questions (oral/written).
Usage:
    $ python3.6 questions.py --oral # for oral questions
    $ python3.6 questions.py --written # for written questions
"""

import logging
from multiprocessing import Pool, current_process
import sys
import time
import random
from datetime import datetime

# import barlapy.barlapy as bp
from barlapy.barlapy.parser import parse_questions_in_page

import twitter
from utils import *

db = connect_to_db()
questions_db = db["questions"]

def match_twitter(author):
    if author in twitter_map.keys():
        return twitter_map[author]
    return author

def format_tweet(qtype, row):
    if qtype == 'written':
        h = "#سؤال_كتابي : "
    elif qtype == 'oral':
        h = "#سؤال_شفوي : "

    a = '، '.join(list(map(match_twitter, row['author'])))
    t = row['topic']
    u = row['url']

    if len(h + a + " - " + t + u) > 280:
        tmp = '... ' + u
        l = len(h + a + " - ")
        snippet = t[:280 -l]
    else:
        snippet = t
    return h + a + " - " + snippet + " " + u

def parse_page(i):
    url = "%s?page=%s" % (ORAL_Q_PAGE, str(i))
    logging.info("[PID:%d] Parsing page: %s" % (current_process().pid, url))

    ret = parse_questions_in_page(url)

    inserted = []

    for q in ret:
        count = questions_db.count_documents({"id": int(q.get_id()), "type": "oral"})
        if count == 0:
            res = questions.insert_one(d)
            logger.debug("Inserted new question, _id: %s" % res.inserted_id)
            inserted.append(q)

            t = format_tweet(qtype, {'author': q.authors, 'topic': q.topic, 'url': q.get_url()})
            # TODO : FIXME selenium geckodriver does not work, is this still true?
            question_text = clip_question_verbatim_screenshot(q.get_url(), './written_questions_text')
            twitter.tweet(t, True, question_text)
            time.sleep(random.randint(2, 30))

    return inserted
    

def main(qtype):
    pool = Pool()

    i = 0
    step = 2
    keepgoing = True
    while keepgoing:
        logging.debug("Parsing from %d.." % i)
        ret = pool.map(parse_page, range(i, i + step)) # parse 2 pages at each iteration

        keepgoing = False
        for elt in ret:
            if len(elt) > 0:
                keepgoing = True

        i += step
    logging.debug("Done")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Argument needed (--oral/-o, --written/-w)")
        sys.exit()

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.basicConfig(filename='questions.log', level=logging.DEBUG, format='%(asctime)s %(levelname)7s %(message)s')

    if sys.argv[1] == '-w' or sys.argv[1] == "--written":
        logging.info("Parsing written questions")
        main("written")
    elif sys.argv[1] == '-o' or sys.argv[1] == "--oral":
        logging.info("Parsing oral questions")
        main("oral")
