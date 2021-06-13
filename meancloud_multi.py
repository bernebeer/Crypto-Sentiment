import requests, json, tweepy, re, os, time
from config import *
from tinydb import TinyDB, Query
from pycoingecko import CoinGeckoAPI
from pprint import pprint

print('Running...')

# create instance cg api object
cg = CoinGeckoAPI()
 
# auth twitter api
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth,wait_on_rate_limit=True)

# twitter crypto list ids to scrape
cryptolists = [1393929796825067522, 859922654681346049, 904733535612821504, 899718321439944710]
	    
alltweets = []
numpages = 3
numtweets = 150

# animation between segments
def deli():
	for x in range (0,10):
		print('.', sep='', end='', flush=True)
		time.sleep(0.07)
	print('\n')

# get all tweets, add to list, combine lists of tweets into 1 list
for cryptolist in cryptolists:

	tweets = api.list_timeline(list_id = cryptolist, count = numtweets, tweet_mode = "extended", include_rts = True)
	# record tweet lastid for paging (max ~200 per page)
	lastid = tweets[-1].id

	# get tweets per following page (tweet id no higher than)
	for numpage in range(numpages - 1):
		tweets.extend(api.list_timeline(list_id = cryptolist, max_id = lastid - 1, count = numtweets, tweet_mode = "extended", include_rts = False))
		lastid = tweets[-1].id
	
	# add tweet to alltweets list
	alltweets.extend(tweets)
	
	print('List ' + str(cryptolists.index(cryptolist) + 1) + ' fetched!')

deli()

# sort full list by desc id
alltweets = sorted(alltweets, key=lambda x: x.id, reverse=True)
print('Lists sorted by ID!')

# how many?
print('Number of tweets fetched: ', len(alltweets))

# remove duplicate tweets from full list
seentweets = set()
uniquetweets = []

for alltweet in alltweets:
	if alltweet.id not in seentweets:
		uniquetweets.append(alltweet)
		seentweets.add(alltweet.id)

print('Duplicate tweets removed!')
print('Number of unique tweets fetched:', len(uniquetweets))
print('Oldest tweet:', uniquetweets[-1].created_at)
print('Newest tweet:', uniquetweets[0].created_at)

deli()

# list of symbols to check text for
symbols = ['$BTC', '$ETH', '$DOGE', '$XRP', '$LTC', '$BCH', '$EOS', '$ADA', '$ETC', '$DASH', '$USDT', '$ZEC', '$XMR', '$ZIL', '$MTL']

#symbols = {{'symbol':'$BTC'}, {'symbol':'$ETH'}, {'symbol':'$DOGE'}}

cglist = cg.get_coins_list()
# final dict of dicts of data
results = {}

# get all cgids by symbol and create main dicts in results
print('All cgids found by symbol:')
for item in cglist:
	for symbol in symbols:
		if symbol[1:].lower() == item['symbol'] and 'peg' not in item['id']:
			print(symbol, '\tCoingecko id:', '\t', item['id'])
			cgid = item['id']
			results[cgid] = {'symbol':symbol, 'cgid':cgid, 'avgsentiment':0, 'terms':{}, '24hr':0, 'tweets':{}}

deli()

# get prices of all cg ids in results per single api call
print('Updating prices...')

cgnames = []
for key, value in results.items():
	cgnames.append(key)

prices = cg.get_price(ids=cgnames, vs_currencies='usd', include_24hr_change='true')

deli()

# add price to results if coingecko dictname matches cgid in results
print('Adding prices to nested dict')

for key, value in results.items():
	for key2, value2 in prices.items():
		if key == key2:
				results[key].update({'price':value2['usd']})
				results[key].update({'24hr':value2['usd_24h_change']})

deli()

# add terms to results
for key, value in results.items():
	for symbol in symbols:
		if symbol == results[key]['symbol']:
			termslist = []
			termslist.append(symbol)
			termslist.append(symbol[1:])
			termslist.append('#' + symbol[1:])
			termslist.append(results[key]['cgid'])
			
			for term in termslist:
				lengthterms = len(results[key]['terms'])
				results[key]['terms'].update({lengthterms + 1:{'term':term}})

print('Evaluating tweets based on symbol found...')

url = "https://api.meaningcloud.com/sentiment-2.1"
mccalls = 0

# test tweet if symbol in, evaluate, add to results
for uniquetweet in uniquetweets:
	
	# strip crap from tweettext
	text = re.sub(r'@\S+|https?://\S+', '', uniquetweet.full_text)
	text = re.sub('\n', ' ', text)
	
	# loop through all result key value pairs
	# check if symbol value in text, do stuff
	for key, value in results.items():

		termslist = []
		for i in range(len(results[key]['terms'])):
			termslist.append(results[key]['terms'][i + 1]['term'])

		textsplit = text.split()
		#textsplit = text

		#if value['symbol'] in text:
		if any(item in textsplit for item in termslist):
			
			# send tweettext to sentiment api
			payload={
	   	 	'key': MCKEY,
	    		'lang': 'en',
	    		'model': 'crypto',
	    		'txt': text
			}
			# requests data
			sentiments = requests.post(url, data=payload)
			print('.', sep='', end='', flush=True)
			
			mccalls += 1
			
			# calc avg sentiment
			data = sentiments.json()
			score = data['score_tag']
			
			# get old stored avg sentiment for averaging
			avgsent = results[key]['avgsentiment']
			# avg sentiment
			if score == 'P+':
				avgsent += 2
			elif score == 'P':
				avgsent += 1
			elif score == 'N':
				avgsent -= 1
			elif score == 'N+':
				avgsent -= 2
			
			# write avg sentiment to results
			results[key].update(avgsentiment = avgsent)
			
			# write tweet to results
			lengthtweets = len(results[key]['tweets'])
			results[key]['tweets'].update({lengthtweets + 1:{'tweet':text,'created':str(uniquetweet.created_at),'sentiment':score}})

deli()

# prettyprint results
print('Tweets evaluated, prettyprint results...')
pprint(results)

# dump results as json file
f = open('results.json', 'w')
f.write(json.dumps(results))
f.close()

deli()

print('Number of meaningcloud evaluated calls:', mccalls)
			
deli()

#print('Final data')
#for item in results:
	#hist = round(item['24hr'], 2)
	#if hist > 0:
		#hist = '+' + str(hist)
	#price = str(round(item['price'], 2))
	#if len(price) < 4:
		#price = price + '0'

	#print(item['symbol'], '\tmentions:', item['symbolmentions'], '\tprice ($):', price, '\t24hr price (%):', hist, '\tavg sentiment:', item['avgsentiment'])

trendlist = cg.get_search_trending()

print('Trending coins: ')
for trend in trendlist['coins']:
	print('$' + trend['item']['symbol'].upper(), '\tPrice: ', float(trend['item']['price_btc']))
	
deli()

db = TinyDB('db.json')
db.truncate()
db.all()
#db.insert({'id':uniquetweet.id, 'text':text, 'score':score, 'date':str(uniquetweet.created_at), 'symbols':fsymbol})