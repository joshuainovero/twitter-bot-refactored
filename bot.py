from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import tweepy
import json
import time

settings = json.load(open('settings.json'))

op = webdriver.ChromeOptions()
op.add_argument('headless')
scraper = webdriver.Chrome(settings['bot-settings']['chrome-driver-path'], options=op)

time_interval = settings['bot-settings']['time_interval']
targetJSON_file = settings['bot-settings']['targetJSON_file']
targetTwitterProfile = json.load(open(str(targetJSON_file)))['profile-link']
twitter_id = json.load(open(str(targetJSON_file)))['twitter_id']

bearer_token = settings['token']['bearer_token']
consumer_key = settings['token']['consumer_key']
consumer_secret = settings['token']['consumer_secret']
access_token = settings['token']['access_token']
access_token_secret = settings['token']['access_token_secret']

assert len(bearer_token) != 0
assert len(consumer_key) != 0
assert len(consumer_secret) != 0
assert len(access_token) != 0
assert len(access_token_secret) != 0

client = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret, wait_on_rate_limit=True)

tempTarget = json.load(open(targetJSON_file))
if not tempTarget['cache']['finished_id']:
    print('Initializing...')
    tempTarget['cache']['finished_id'].append(client.get_users_tweets(int(twitter_id), max_results=5).data[0].id)
    scraper.get(str(targetTwitterProfile))
    element = WebDriverWait(scraper, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div')))
    tweets_number = (element.text).split()[0]
    tempTarget['tweets'] = tweets_number
    with open(str(targetJSON_file), 'w') as file:
        json.dump(tempTarget, file, indent = 4)

while True:
    try:
        scraper.get(str(targetTwitterProfile))
        time.sleep(time_interval)
        print('scrapping...')
        element = WebDriverWait(scraper, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div')))
        tweets_number = (element.text).split()[0]
        print(f'Current tweets : {tweets_number}')
        JSONtweets = json.load(open(str(targetJSON_file)))

        if int(tweets_number) != int(JSONtweets['tweets']):
            if int(tweets_number) < int(JSONtweets['tweets']):
                JSONtweets['tweets'] = tweets_number
                JSONtweets['cache']['finished_id'].clear()
                JSONtweets['cache']['finished_id'].append(client.get_users_tweets(int(twitter_id), max_results=5).data[0].id)
                with open(str(targetJSON_file), 'w') as file:
                    json.dump(JSONtweets, file, indent=4)
                print('Recent tweet detected. Dumped new data')
                continue
            JSONtweets['tweets'] = tweets_number
            while client.get_users_tweets(int(twitter_id), max_results=5).data[0].id in JSONtweets['cache']['finished_id']:
                pass
            
            tweets = client.get_users_tweets(int(twitter_id), max_results=5)
            JSONtweets['cache']['finished_id'].append(tweets.data[0].id)
            tweet_id = tweets.data[0].id
            client.like(tweet_id)
            client.retweet(tweet_id)
            client.create_tweet(text=str(settings['bot-settings']['in_reply_tweet']), in_reply_to_tweet_id=tweet_id)
            with open(str(targetJSON_file), 'w') as file:
                json.dump(JSONtweets, file, indent=4)
            print('Recent tweet detected. Dumped new data')
    except:
        print('Reloading scraper')
        scraper.close()
        scraper = webdriver.Chrome('chromedriver.exe', options=op)
    