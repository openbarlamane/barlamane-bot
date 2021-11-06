import logging
import sys
import tweepy
import config

auth = tweepy.OAuthHandler(config.twitter_oauth_consumer_key, 
                           config.twitter_oauth_consumer_secret)
auth.set_access_token(config.twitter_oauth_access_token_key,
                      config.twitter_oauth_access_token_secret)
twitter = tweepy.API(auth)

def tweet(msg, dry_run = False, img = ""):
    try:
        logging.debug("Tweeting %s: (%s)" % (len(msg), msg))
        if dry_run:
            return
        if not img:
            twitter.update_status(msg)
        else:
            twitter.update_with_media(img, msg)

    except Exception as e:
        logging.error("There was an exception tweeting: %s" %e)

if __name__ == '__main__':
    l = logging.getLogger()
    l.addHandler(logging.StreamHandler(sys.stdout))
    l.setLevel(logging.DEBUG)

    if len(sys.argv) > 1:
        tweet(sys.argv[1])
    else:
        logging.error("No argument, usage: python twitter.py <tweet>")

