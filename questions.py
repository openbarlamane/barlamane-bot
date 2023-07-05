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

from barlapy.barlapy.parser import parse_questions_in_page

import twitter
from utils import *

MAX_QUESTIONS_IN_THREAD=4
MAX_TWEETS_OR_THREADS=4

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

def format_thread_header(qtype, authors):
    if qtype == 'written':
        h = "#سؤال_كتابي : "
    elif qtype == 'oral':
        h = "#سؤال_شفوي : "

    a = ", ".join(list(map(match_twitter, authors)))

    return h + a


def parse_page(page_nb):
    """
    Parse a page of questions (oral or written) and insert new
    questions to the db.
    This method was written with spirit of being multi-threadable 
    in order to parse multiple pages at once.
    To determine which type of questions are being parsed, and to avoid
    having to pass an argument to Pool.map method, we check the value in sys.argv[2].
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
        logging.debug("question ID: %d, found in db: %d" % (int(q.get_id()), count))
        if count == 0:
            d = q.to_dict()
            res = questions_db.insert_one(d)
            inserted.append(q)
            logging.debug("inserted one: %s, res: %s" % (q.get_id(), res.inserted_id))
        elif count != 1:
            logging.error("There are already %d similar questions (%s)" % (count, q.get_url()))

    logging.info("[PID:%d] Inserted: %s" % (current_process().pid, inserted))
    return inserted

def main(qtype):
    if sys.argv[1] == '-w' or sys.argv[1] == "--written":
        qtype = "written"
    else:
        qtype = "oral"

    pool = Pool()

    i = 0
    step = 3
    keepgoing = True
    result = []
    while keepgoing:
        logging.debug("Parsing (%d -> %d).." % (i, i+step))

        # parse "step" pages at each iteration
        ret = pool.map(parse_page, range(i, i+step))
        for l in ret:
            for q in l:
                result.append(q)

        # We start backwards, if the highest (page number) page
        # didn't yield any result, we stop fetching.
        for elt in ret[::-1]:
            if len(elt) == 0:
                keepgoing = False

        i += step

    logging.debug("Done, found %d new questions" % len(result))
    if len(result) == 0:
        return

    # from now on there is no more use of Question as a structure, we only
    # keep the necessary data to tweet
    d = {}
    for q in result:
        # if the frozenset of authors is already in the structure,
        # we add a new element to its list, otherwise we create it.
        if frozenset(q.authors) in d.keys():
            d[frozenset(q.authors)].append((q.topic, q.get_url()))
        else:
            d[frozenset(q.authors)] = [(q.topic, q.get_url())]

    logging.debug("d = %s" % d.keys())

    # If we have "too much" questions, we sample the data to limit the number
    # of tweets, this prevents the bot from flooding the timeline, and also being
    # potentially flagged for spam.
    if len(d.keys()) > MAX_TWEETS_OR_THREADS:
        logging.debug("Too much tweets (%d), reducing the number of elements (to %d) before tweeting" % (len(d.keys()), MAX_TWEETS_OR_THREADS))
        # sample the dictionary
        sampled_keys = random.sample(d.keys(), MAX_TWEETS_OR_THREADS)
        d = { k: d[k] for k in sampled_keys }

    """
    d = {frozenset(mp1, mp2, mp3): [(topic1, url1), (topic2, url2)],
         frozenset(mp4): [(topic3, url3), (topic4, url4), (topic5, url5)],
         frozenset(mp5, mp6, mp7): [(topic6, url6)]}
    """
    for k in d.keys():
        logging.info("There are %d questions in this set" % len(d[k]))
        # only one question
        if len(d[k]) == 1:
            # 0: topic, 1: url
            t = format_tweet(qtype, {'author': k, 'topic': d[k][0][0], 'url': d[k][0][1]})
            img = clip_question_verbatim_screenshot(d[k][0][1])
            logging.debug("img = %s" % img)
            res = twitter.tweet(t, img=img)
            logging.debug("twitter.tweet returned: %s" % res)
        # multiple questions
        else:
            thread = [format_thread_header(qtype, k)]
            for q in d[k]:
                next_tweet = "%s %s" % (q[0], q[1])
                logging.debug("Adding to thread: %s" % next_tweet)
                thread.append(next_tweet)
            if len(thread) >= MAX_QUESTIONS_IN_THREAD + 1:
                logging.debug("Too much tweets in the thread (%d), reducing the number of elements (to %d) before tweeting" % (len(thread),  MAX_QUESTIONS_IN_THREAD))
                thread = [thread[0]] + random.sample(thread[0:], MAX_QUESTIONS_IN_THREAD)
            twitter.thread(thread)

        sleep_itv = random.randint(2, 30)
        logging.info("Sleeping %d seconds..." % sleep_itv)
        time.sleep(sleep_itv)

    logging.info("DONE")

if __name__ == "__main__":
   try:
        if len(sys.argv) < 2:
            logging.error("Argument needed (--oral/-o, --written/-w)")
            sys.exit()

        formatter = logging.Formatter('%(asctime)s %(levelname)6s %(message)s')
        root_logger = logging.getLogger()

        file_handler = logging.FileHandler(config.questions_log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # tee to stdout
        if len(sys.argv) >= 3 and sys.argv[2] == "-std":
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

        # silence verbose logs from external libraries, some are still missing...
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests-oauthlib").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("oauthlib").setLevel(logging.WARNING)

        if sys.argv[1] == '-w' or sys.argv[1] == "--written":
            logging.info("Parsing written questions")
            main("written")
        elif sys.argv[1] == '-o' or sys.argv[1] == "--oral":
            logging.info("Parsing oral questions")
            main("oral")

   except Exception as e:
      logging.exception("oh, no! we crashed. Error: %s", e)

