import logging
import sys
import tweepy
import config

# v1, still necessary for image upload, see https://github.com/tweepy/tweepy/discussions/1954
auth = tweepy.OAuthHandler(config.twitter_oauth_consumer_key,
                           config.twitter_oauth_consumer_secret)
auth.set_access_token(config.twitter_oauth_access_token_key,
                      config.twitter_oauth_access_token_secret)
api = tweepy.API(auth)

# v2
twitter = tweepy.Client(
        consumer_key=config.twitter_oauth_consumer_key,
        consumer_secret=config.twitter_oauth_consumer_secret,
        access_token=config.twitter_oauth_access_token_key,
        access_token_secret=config.twitter_oauth_access_token_secret)

def tweet(msg, dry_run=False, img=""):
    try:
        logging.debug("Tweeting %s: (%s)" % (len(msg), msg))
        if dry_run:
            return

        if not img:
            return twitter.create_tweet(text=msg)
        else:
            media = api.media_upload(img)
            return twitter.create_tweet(text=msg, media_ids=[media.media_id])

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
