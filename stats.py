#!/usr/bin/python3

import logging
import six
import sys
import pymongo
from datetime import datetime, timedelta

from barlapy.barlapy.question import Question
from utils import connect_to_db, twitter_map
import twitter
import config

db = connect_to_db()

def month_to_arabic_name(month):
    if month == 1:
        return "يناير"
    elif month == 2:
        return "فبراير"
    elif month == 3:
        return "مارس"
    elif month == 4:
        return "أبريل"
    elif month == 5:
        return "ماي"
    elif month == 6:
        return "يونيو"
    elif month == 7:
        return "يوليوز"
    elif month == 8:
        return "غشت"
    elif month == 9:
        return "شتنبر"
    elif month == 10:
        return "أكتوبر"
    elif month == 11:
        return "نونبر"
    elif month == 12:
        return "دجنبر"

def send_summary_tweet(rankings, month = None):
    if month:
        m = month_to_arabic_name(month)
        t = "🏆 الأعضاء الأكثر طرحا للأسئلة خلال شهر %s:\n" % m
    else:
        t = "🏆 الأعضاء الأكثر طرحا للأسئلة خلال %s:\n" % "14 يوما الأخير"

    mps = db["mps"]
    for k, v in six.iteritems(rankings):
        # get party name 
        mp = mps.find_one({"name": k, "legislature": "2021-2026"})
        if mp != None and mp["party"] != "":
            party = " (%s)" % mp["party"]

        # get twitter @ if available
        if k in twitter_map.keys():
            k = twitter_map[k]

        tmp = "%-4d - %s%s\n" % (v, k, party)
        if len(t + tmp) <= 240:
            t += tmp
        else:
            break

    twitter.tweet(t) 

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Argument needed")
        sys.exit()

    formatter = logging.Formatter('%(asctime)s %(levelname)6s %(message)s')
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(config.stats_log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

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

    questions = db['questions']

    today = datetime.today()
    if sys.argv[1] == '--bi':
        daterange = today - timedelta(days=14)
        query = {"date": {
                    "$gte": datetime.strptime('%s-%s-%s' % (daterange.strftime('%Y'), daterange.strftime('%m'), daterange.strftime('%d')), '%Y-%m-%d'),
                    "$lte": datetime.strptime('%s-%s-%s' % (today.strftime('%Y'), today.strftime('%m'), today.strftime('%d')), '%Y-%m-%d')}}

    elif sys.argv[1] == '--mo':
        daterange = today - timedelta(days=30)
        query = {"date": {
                    "$gte": datetime.strptime('%s-%s-%s' % (daterange.strftime('%Y'), daterange.strftime('%m'), 1), '%Y-%m-%d'),
                    "$lt": datetime.strptime('%s-%s-%s' % (today.strftime('%Y'), today.strftime('%m'), 1), '%Y-%m-%d'),
            }}

    logging.info("query: %s" % query)

    rankings = {}
    for q in questions.find(query):
        for a in q['authors']:
            if a in rankings.keys():
                rankings[a] += 1
            else:
                rankings[a] = 1

    rankings = {k: v for k, v in sorted(rankings.items(), key = lambda item: item[1], reverse=True)}
    logging.debug("rankings: %s" % rankings)

    if sys.argv[1] == '--bi':
        send_summary_tweet(rankings)
    else:
        send_summary_tweet(rankings, today.month - 1)
