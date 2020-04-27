import urllib.request
import time
from lxml.html import fromstring
from itertools import cycle
import os

class ProxyRetriever(object):
    def __init__(self, n_proxies=10):
        self.n_proxies = n_proxies
        self.proxies = None
        self.refresh()
        self.timestamp = time.time()

    def get(self):
        if time.time() - self.timestamp > 3600:
            self.refresh()
        return self.proxies

    def refresh(self):
        url = 'https://free-proxy-list.net/'
        text = urlopen(url)
        parser = fromstring(text)
        proxies = set()
        for i in parser.xpath('//tbody/tr')[:self.n_proxies]:
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxies.add(proxy)

        self.proxies = proxies
        self.timestamp = time.time()

        # print(proxies)
        # proxy_pool = cycle(proxies)

        # url = 'https://httpbin.org/ip'
        # for i in range(1,11):
        #     #Get a proxy from the pool
        #     proxy = next(proxy_pool)
        #     print("Request #%d"%i)
        #     try:
        #         response = _urlopen(url, proxies={"http": proxy, "https" : proxy})
        #         print(response)
        #     except:
        #         print("Skipping. Connnection error")

    def save_proxies(self, filepath):
        with open(filepath, 'w') as f:
            for proxy in self.proxies:
                f.write(proxy + '\n')
        print(f'Proxies saved successfully at {filepath}!')

def urlopen(url, proxies=None):
    headers = [
        ('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) " \
            "Chrome/ 58.0.3029.81 Safari/537.36"),
        ("Accept-Language", "en-US,en;q=0.5"),
    ]

    if proxies is not None:
        # print(proxies)
        handler = urllib.request.ProxyHandler(proxies)
        opener = urllib.request.build_opener(handler)
    else:
        opener = urllib.request.build_opener()

    opener.addheaders = headers

    with opener.open(url) as response:
        text = response.read()

    return text

def distribute(arr, n):
    lists = [[] for _ in range(n)]
    i = 0
    total = len(arr)
    counter = 0
    while i < total:
        lists[counter].append(arr[i])
        i += 1
        counter = (counter + 1) % n
    return lists