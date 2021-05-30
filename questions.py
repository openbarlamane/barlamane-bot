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
from datetime import datetime

from barlapy.parser import parse_questions_in_page

import twitter
from utils import twitter_map, WRITTEN_Q_PAGE, ORAL_Q_PAGE, clip_question_verbatim_screenshot, connect_to_db

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

def get_new_questions(questions_db, qtype):
    page = 0

    new_questions = []
    found_in_db = False
    while not found_in_db:
        if qtype == 'written':
            url = WRITTEN_Q_PAGE
        elif qtype == 'oral':
            url = ORAL_Q_PAGE
        else:
            print("Wrong parameter")
            return []

        url += "?page=%s" % str(page)

        print("Fetching questions in page: %s" % url)
        questions = parse_questions_in_page(url)
        for q in questions:
            count = questions_db.count_documents({"id": int(q.get_id()), "type": qtype})
            if count == 1:
                print("Found question %d in db" % q.get_id())
                found_in_db = True
                break
            elif count > 1:
                print("Question %d has %d duplicates!" % (q.get_id(), count))
                return []
            else:
                print("Question %d not in db" % q.get_id())

            new_questions.append(q)

        page += 1

    return new_questions

def main(qtype):
    db = connect_to_db()
    questions = db["questions"]

    new_questions = get_new_questions(questions, qtype)

    if len(new_questions) == 0:
        print('No new questions')
        return

    print('There are %d new questions' % len(new_questions))
    for q in new_questions:

        d = q.to_dict()
        d['updated_at'] = datetime.now()
        res = questions.insert_one(d)

        print("Inserted new question, _id: %s" % res.inserted_id)

        t = format_tweet(qtype, {'author': q.authors, 'topic': q.topic, 'url': q.get_url()})
        # TODO : FIXME selenium geckodriver does not work
        # question_text = clip_question_verbatim_screenshot(q.get_url(), './written_questions_text')
        # twitter.tweet(t, True, question_text)
        twitter.tweet(t, False)
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
