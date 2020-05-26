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
        f = open('tweets.txt', 'r+')
        for l in f.readlines():
            if msg == l:
                print("Already tweeted...")
                return
        print("Tweeting %s: " % len(msg), msg)
        if dry_run:
            print("Dry running.. %s" % msg)
            return
        else:
            if not img:
                twitter.update_status(msg)
            else:
                twitter.update_with_media(img, msg)
            f.write(msg + "\n")

    except Exception as e:
        print("There was an exception tweeting.")
        print(e)

if __name__ == '__main__':
    tweet(sys.argv[1])


