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
        print("Tweeting: ", msg)
        if not dry_run:
            if not img:
                twitter.update_status(msg)
            else:
                twitter.update_with_media(img, msg)
    except Exception as e:
        print("There was an exception tweeting.")
        print(e)

if __name__ == '__main__':
    tweet(sys.argv[1])


