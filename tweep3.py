#imports
from config import *
import tweepy
from tinydb import TinyDB, Query
from pycoingecko import CoinGeckoAPI
import requests
import json
import re

# func rm emojis
def deEmojify(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)

# auth twitter api
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth,wait_on_rate_limit=True)

#db = TinyDB('db.json')

# Post a tweet from Python
# api.update_status("Look, I'm tweeting from #Python in my #earthanalytics class! @EarthLabCU")
# Your tweet has been posted!

print('Running...')

# The IDs of the lists to be tweepyd
lists = [1393929796825067522, 859922654681346049, 904733535612821504, 899718321439944710]
	    
fullist = []
numpages = 2
numtweets = 50

# get all tweets by list, combine lists of tweets into 1 list
# get tweets per page in list
for list in lists:

	items = api.list_timeline(list_id = list, count = numtweets, tweet_mode = "extended", include_rts = False)
	lastid = items[-1].id

	for x in range(numpages - 1):
		items.extend(api.list_timeline(list_id = list, max_id = lastid - 1, count = numtweets, tweet_mode = "extended", include_rts = False))
		lastid = items[-1].id
			
	fullist.extend(items)
	
	print('List ' + str(lists.index(list) + 1) + ' fetched!')

# sort full list by desc id
sortedlist = sorted(fullist, key=lambda x: x.id, reverse=True)
print('Lists sorted by ID!')

# remove duplicate tweets from full list
dupcnt = 0
seenids = set()
uniquelist = []

for item in sortedlist:
	if item.id not in seenids:
		uniquelist.append(item)
		seenids.add(item.id)
	else:
		dupcnt += 1

print('Duplicate tweets removed!')

print('Oldest tweet: ', end = '')
print(uniquelist[-1].created_at)

print('Newest tweet: ', end = '')
print(uniquelist[0].created_at)
 
# set variables for match and sentiment payload loop      
cons_text = ''
symbols = ['$BTC', 'BTC', '$ETH', 'ETH', '$DOGE', 'DOGE', '$XRP', 'XRP', '$LTC', 'LTC', '$BCH', 'BCH', '$EOS', 'EOS', '$ADA', 'ADA']
punctuations = '''!()-[]{};:'"\,<>./?@#%^&*_~'''
paylist = [''] * len(symbols)

# for each unique and sorted tweet object in list:
# 1. clean text: match all tweets to symbol by upper and punct, then
# 2. if symbol found, clean text, add to payload list item
for x in uniquelist:
	cons_text += x.full_text
	cons_text += "\n"
	
	# get full tweettext and transform to uppercase
	up = x.full_text.upper()
	
	# remove crap characters from tweet string	
	for item in up:
		if item not in punctuations:
			up = up + item
			
	# split tweet into list
	upsplit = up.split()
	
	# remove all tweet list items containing @
	upsplitat = []
	for item in upsplit:
		if '@' not in item:
			upsplitat.append(item)
	
	# get full text if symbol found in split list of cleaned tweet
	# clean full text 
	for item in symbols:
		if item in upsplitat:

			sentfull = x.full_text
			
			sentsplit = sentfull.split()

			# strip @
			sentat = []
			for y in sentsplit:
				if '@' not in y:
					sentat.append(y)
					
			# strip http
			senthtp = []
			for y in sentat:
				if 'http' not in y:
					senthtp.append(y)

			# join list
			sentjoin = ' '.join(senthtp)
			
			# deemoijify
			sentjoin = deEmojify(sentjoin)
			
			paylist[symbols.index(item)] += sentjoin

# get sentiment for each payload text by paylist
# payload is accumulated text per symbol
# paylist conforms to symbol list
for item in paylist:
	r = requests.post(
    	"https://api.deepai.org/api/sentiment-analysis",
		data={
			'text': item,
    	},
    	headers={'api-key': DEEPAIAPI}
	)
	print(item)
	print(r.json())
	
					
# count instances of symbol + print price
cons_text = cons_text.upper()
strip = ""

for x in cons_text:
   if x not in punctuations:
       strip = strip + x
       
split = strip.split()
print("The number of tweets fetched is: " + str(len(fullist)) + ', of which ' + str(dupcnt) + ' were duplicates') 

cg = CoinGeckoAPI()
cglist = cg.get_coins_list()
value = 0
price = 0

print('------------')

for x in symbols:
	
	print('Number of mentions   ' + x + ':\t' + str(split.count(x)))
	
	for y in cglist:
		if x.lower() == y['symbol'] and 'binance' not in y['id']:
			#print('found')
			price = cg.get_price(ids=y['id'], vs_currencies='usd')#
			for z in price.values():
				value = z.get('usd')
				#print (z)
			print('Value of ' + x + ' is: \t\t$', end = '')
			print(value)
			
	if (symbols.index(x) + 1) % 2 == 0:
		print('------------')
		
data = api.rate_limit_status()
print(data['resources']['lists']['/lists/statuses'])

