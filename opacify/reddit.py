import requests
import json
import time
import re

def reddit_get_links(count=50, sleep=5, giveup=600, filter_over18=True):
    cache = []
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    start = time.time()
    errors = 0
    count = int(count)
    giveup = int(giveup)
    while len(cache) < count and time.time() - start < giveup:
        r = requests.get('https://www.reddit.com/r/all/new.json', headers=headers)
        if r.status_code > 204:
            errors += 1
            if errors > 10:
                break
            time.sleep(sleep*2)
            continue
        
        for i in r.json()['data']['children']:
            d = i['data']
            over_18 = d['over_18']
            if over_18 is True: continue
            if 'url' in d:
                url = d['url']
                if re.search('\.(jpg|png|jpeg|gif|txt|pdf)$', url):
                    if not url in cache:
                        cache.append(url)
        time.sleep(sleep)
    return cache

if __name__ == '__main__':
    for i in reddit_get_links():
        print(i)

