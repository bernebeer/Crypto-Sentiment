import requests
import json
from config import *
import tweepy
from tinydb import TinyDB, Query
import re
import os

# auth twitter api
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth,wait_on_rate_limit=True)

cryptolists = [1393929796825067522, 859922654681346049, 904733535612821504, 899718321439944710]
	    
alltweets = []
numpages = 1
numtweets = 200

# get all tweets by list, combine lists of tweets into 1 list
# get tweets per page in list
for cryptolist in cryptolists:

	tweets = api.list_timeline(list_id = cryptolist, count = numtweets, tweet_mode = "extended", include_rts = False)
	lastid = tweets[-1].id
	firstid = tweets[0].id

	for numpage in range(numpages - 1):
		tweets.extend(api.list_timeline(list_id = cryptolist, max_id = lastid - 1, count = numtweets, tweet_mode = "extended", include_rts = False))
		lastid = tweets[-1].id
			
	alltweets.extend(tweets)
	
	print('List ' + str(cryptolists.index(cryptolist) + 1) + ' fetched!')

# sort full list by desc id
alltweets = sorted(alltweets, key=lambda x: x.id, reverse=True)
print('Lists sorted by ID!')

# how many
print('Number of tweets fetched: ', len(alltweets))

# remove duplicate tweets from full list
seentweets = set()
uniquetweets = []

for alltweet in alltweets:
	if alltweet.id not in seentweets:
		uniquetweets.append(alltweet)
		seentweets.add(alltweet.id)

print('Number of unique tweets fetched: ', end = '')		
print(len(uniquetweets))

print('Duplicate tweets removed!')

print('Oldest tweet: ', uniquetweets[-1].created_at)

print('Newest tweet: ', uniquetweets[0].created_at)

print('------------')

punctuations = '''!()-[]{};:'"\,<>./?@#%^&*_~'''
symbols = ['$BTC', '$ETH', '$DOGE', '$XRP', '$LTC', '$BCH', '$EOS', '$ADA']

db = TinyDB('db.json')
db.truncate()
db.all()

url = "https://api.meaningcloud.com/sentiment-2.1"
ftweets = []

for uniquetweet in uniquetweets:
	text = re.sub(r'@\S+|https?://\S+', '', uniquetweet.full_text)
	text = re.sub('\n', ' ', text)
	if any(x in text.upper() for x in symbols):
		fsymbol = []
		for symbol in symbols:
			if symbol in text.upper():
				fsymbol.append(symbol)
				#print('symbols: ', end = '')
				#print(fsymbol)
		jsymbols = ''
		sep = (',')
		#jsymbols = sep.join(fsymbol)
	
		print('Symbols found in tweet: ', fsymbol)
		print('Text: ', text)
		
		payload={
	    	'key': MCKEY,
	    	'lang': 'en',
	    	'txt': text
		}
		sentiments = requests.post(url, data=payload)
		
		data = sentiments.json()
		score = data['score_tag']
		print('Sentiment: ', score)
		
		db.insert({'id':uniquetweet.id, 'text':text, 'score':score, 'date':str(uniquetweet.created_at), 'symbols':fsymbol})
		
		ftweets.append(uniquetweet)
		
		print('Remaining credits: ', data['status']['remaining_credits'])
		
		print('------------')

print('Number of filtered tweets: ', len(ftweets))

print('------------')

with open('db.json', 'r') as handle:
	parsed = json.load(handle)

#print(json.dumps(parsed, indent=4, sort_keys=True))
