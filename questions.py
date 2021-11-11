#!/usr/bin/python3

"""
Fetch, insert to db and tweet new questions (oral/written).
Usage:
    $ # add -std at the end of the command to print logs to stdout as well
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

def parse_page(page_nb):
    """
    Parse a page of questions (oral or written) and insert new
    questions to the db.
    This method was written with spirit of being multi-threadable 
    in order to parse multiple pages at once.
    To determine which type of questions are being parsed, and to avoid
    having to pass an argument to Pool.map method, we check the value in sys.argv[2]
    """

    if sys.argv[1] == '-w' or sys.argv[1] == "--written":
        questions_type = "written"
        url = "%s?page=%s" % (WRITTEN_Q_PAGE, str(page_nb))
    else:
        questions_type = "oral"
        url = "%s?page=%s" % (ORAL_Q_PAGE, str(page_nb))
    
    logging.info("[PID:%d] Parsing page: %s" % (current_process().pid, url))

    ret = parse_questions_in_page(url)
    logging.debug("[PID:%d] questions parsed in page %d: %d" % (current_process().pid, page_nb, len(ret)))
        
    inserted = []
    for q in ret:
        count = questions_db.count_documents({"id": int(q.get_id()), "type": questions_type, "date": q.get_date()})
        logging.debug("%d, count: %d" % (int(q.get_id()), count))
        if count == 0:
            d = q.to_dict()
            res = questions_db.insert_one(d)
            inserted.append(q)
            logging.debug("inserted one: %s, res: %s" % (q.get_id(), res.inserted_id))
            t = format_tweet(qtype, {'author': q.authors, 'topic': q.topic, 'url': q.get_url()})
            twitter.tweet(t, True, question_text)
            time.sleep(random.randint(2, 30))
        elif count != 1:
            logging.error("There are already %d similar questions (%s)" % (count, q.get_url()))

    logging.info("[PID:%d] Inserted: %s" % (current_process().pid, inserted))
    return inserted

def main(qtype):
    pool = Pool()

    i = 0
    step = 3
    keepgoing = True
    while keepgoing:
        logging.debug("Parsing (%d -> %d).." % (i, i+step))

        # parse "step" pages at each iteration
        ret = pool.map(parse_page, range(i, i+step))

        # We start backwards, if the highest (page number) page
        # didn't yield any result, we stop fetching.
        for elt in ret[::-1]:
            if len(elt) == 0:
                keepgoing = False

        i += step
    logging.debug("Done")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Argument needed (--oral/-o, --written/-w)")
        sys.exit()

    formatter = logging.Formatter('%(asctime)s %(levelname)6s %(message)s')
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler('questions.log')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # tee to stdout
    if len(sys.argv) >= 3 and sys.argv[2] == "-std":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # silence urllib3 verbose logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    if sys.argv[1] == '-w' or sys.argv[1] == "--written":
        logging.info("Parsing written questions")
        main("written")
    elif sys.argv[1] == '-o' or sys.argv[1] == "--oral":
        logging.info("Parsing oral questions")
        main("oral")
