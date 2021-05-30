#!/usr/bin/python3

import csv
import pymongo
from datetime import datetime, timedelta
from utils import connect_to_db, twitter_map

start_date = datetime.fromisoformat('2019-10-01')
end_date = datetime.fromisoformat('2020-07-20')
query = {"date": {
        "$gte": datetime.strptime('%s-%s-%s' % (start_date.strftime('%Y'), start_date.strftime('%m'), start_date.strftime('%d')), '%Y-%m-%d'),
        "$lte": datetime.strptime('%s-%s-%s' % (end_date.strftime('%Y'), end_date.strftime('%m'), end_date.strftime('%d')), '%Y-%m-%d')}}

db = connect_to_db()
questions = db['questions']
mps = db['mps']


# csv_columns = ['id', 'type', 'topic', 'date', 'text', 'author', 'party', 'status', 'answer_date', 'ministry']
# csv_file = "legislature_year_summary_201920.csv"
# try:
#     with open(csv_file, 'w') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
#         writer.writeheader()
#         for q in questions.find(query):
#             for author in q['authors']: # we'll print one line per author
#                 mp = mps.find_one({"name": author})
#                 flat_dict = {
#                     "id": q['id'],
#                     "type": q['type'],
#                     "topic": q['topic'],
#                     "date": q['date'].strftime("%d/%m/%y"),
#                     "text": q['text'],
#                     "author": author,
#                     "party": mp['party'] if mp != None else '',
#                     "status": q['status'],
#                     "answer_date": q['answer']['date'].strftime("%d/%m/%y") if q['answer'] != {} else '',
#                     "ministry": q['ministry']
#                 }
#                 writer.writerow(flat_dict)
# except IOError:
#     print("I/O error")
# 
def rankings():
    rank = {}
    for q in questions.find(query):
        for a in q['authors']:
            if a in rank.keys():
                rank[a] += 1
            else:
                rank[a] = 1

    rank = {k: v for k, v in sorted(rank.items(), key = lambda item: item[1], reverse=True)}
    return rank

