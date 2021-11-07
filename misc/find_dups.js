// Find duplicate questions (id + type same)

use barlamane;
let s = db.questions.aggregate([
{
    "$group" : {
        "_id": {"id": "$id", "type": "$type"},
        "count": { "$sum": 1 } }},
{
    "$match": {
        "_id" :{ "$ne" : null } , "count" : {"$gt": 1}
    }
},
{
     "$sort": {"count": -1 }
 }
]);

s.forEach(item => {
    let question = item._id;

    // Do something

});
