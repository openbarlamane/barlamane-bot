import logging
import sys
import tweepy
import config

auth = tweepy.OAuthHandler(config.twitter_oauth_consumer_key, 
                           config.twitter_oauth_consumer_secret)
auth.set_access_token(config.twitter_oauth_access_token_key,
                      config.twitter_oauth_access_token_secret)
twitter = tweepy.API(auth)

def tweet(msg, dry_run=False, img=""):
    try:
        logging.debug("Tweeting %s: (%s)" % (len(msg), msg))
        if dry_run:
            return
        if not img:
            return twitter.update_status(msg)
        else:
            return twitter.update_with_media(img, msg)

    except Exception as e:
        logging.error("There was an exception tweeting: %s" % e)

# TODO: use tweet above
def thread(statuses, start_tweet_id=None):
    try:
        prev_status_id = start_tweet_id
        i = 0
        for status in statuses:
            if prev_status_id == None:
                logging.debug("Tweeting '%s' as first tweet in thread" % status)
                new_status = twitter.update_status(status)
            else:
                logging.debug("(%d) Tweeting '%s' in reply to %d" % (i+1, status, prev_status_id))

                new_status = twitter.update_status(status,
                                 in_reply_to_status_id=prev_status_id,
                                 auto_populate_reply_metadata=True)

            i += 1

            prev_status_id = new_status.id
    except Exception as e:
        logging.error("There was an exception tweeting: %s" % e)


if __name__ == '__main__':
    l = logging.getLogger()
    l.addHandler(logging.StreamHandler(sys.stdout))
    l.setLevel(logging.DEBUG)

    if len(sys.argv) > 1:
        tweet(sys.argv[1])
    else:
        logging.error("No argument, usage: python twitter.py <tweet>")
