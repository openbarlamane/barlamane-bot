"""
As of today (Nov. 7th 2021), some questions still find their way into the
production database with a date of String type. This script can be used
to transform them to ISODates.
"""
from barlapy.utils import *
import datetime
import pymongo

mongo = pymongo.MongoClient(config.mongo_db_url)
db = mongo["barlamane"]
questions_db = db["questions"]

for q in db.questions.find({"date": {"$type": 2}}):
    new_date = datetime.datetime(1900, 1, 1)
    if q["date"] != "":
       new_date = format_raw_date_to_isoformat(q["date"])

    res = questions_db.update_one({'_id': q["_id"]}, {'$set': {"date": new_date}})
    print("updated: ", res.matched_count, res.modified_count)


