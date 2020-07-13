#!/usr/bin/python3

import six
import sys
import pymongo
from datetime import datetime, timedelta

from barlapy.question import Question
from utils import connect_to_db, twitter_map
import twitter

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
        t = "الأعضاء الأكثر طرحا للأسئلة خلال شهر %s:\n" % m
    else:
        t = "الأعضاء الأكثر طرحا للأسئلة خلال %s:\n" % "14 يوما الأخير"

    i = 0
    for k, v in six.iteritems(rankings):
        if k in twitter_map.keys():
            k = twitter_map[k]
        t += "%-3d - %s\n" % (v, k)
        i += 1
        if i == 5:
            break

    print("tweeting : ", t)
    print("len: ", len(t))
    twitter.tweet(t) 

if __name__ == "__main__":
    db = connect_to_db()
    questions = db['questions']

    if len(sys.argv) < 2:
        print("Argument needed")
        sys.exit()

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

    print(query)

    rankings = {}
    for q in questions.find(query):
        for a in q['authors']:
            if a in rankings.keys():
                rankings[a] += 1
            else:
                rankings[a] = 1

    rankings = {k: v for k, v in sorted(rankings.items(), key = lambda item: item[1], reverse=True)}

    if sys.argv[1] == '--bi':
        send_summary_tweet(rankings)
    else:
        send_summary_tweet(rankings, today.month - 1)
