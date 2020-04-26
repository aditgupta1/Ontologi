'''
https://github.com/anthonyhseb/googlesearch/blob/master/googlesearch/googlesearch.py
'''
import urllib.request
import time

from lxml.html import fromstring
from itertools import cycle
import os
import multiprocessing

class GoogleSearch:
    def __init__(self, max_proc=8):
        self.max_proc = max_proc
        self.proxies = ProxyRetriever(10)

    def search(self, query, n_results=10):
        if isinstance(query, str):
            return _search(query, n_results)

        # List of queries
        n_proc = min(len(query), self.max_proc)
        return self._batch_search(query, n_results, n_proc)

    def _batch_search(self, query_list, n_results, n_proc):
        proc_lists = distribute(query_list, n_proc)

        with multiprocessing.Manager() as manager: 
            # creating a list in server process memory 
            records = manager.list()

            processes = []
            for i in range(n_proc):
                print(proc_lists[i])
                p = multiprocessing.Process(target=_search_list, 
                                            args=(proc_lists[i], records, n_results))
                processes.append(p)

            for i in range(n_proc):
                processes[i].start()

            for i in range(n_proc):
                processes[i].join()
            
            result = list(records)

        return result

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
        text = _urlopen(url)
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

def _urlopen(url, proxies=None):
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

def _search(query, n_results=10):
    SEARCH_URL = "https://google.com/search"
    RESULTS_PER_PAGE = 10

    searchResults = []

    i = 0
    while len(searchResults) < n_results:
        start = i * RESULTS_PER_PAGE
        text = _urlopen(SEARCH_URL + \
            "?q="+ urllib.parse.quote(query) + ("" if start==0 else f"&start={start}"))
        parser = fromstring(text)

        for link in parser.xpath('//div[@class="r"]/a'):
            searchResults.append(link.get('href'))
        i += 1

    return searchResults[:n_results]

def _search_list(arr, records=[], n_results=10):
    for query in arr:
        for result in _search(query, n_results):
            records.append(result)

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

if __name__ == "__main__":
    search = GoogleSearch()
    
    for i in range(100):
        start = time.time()
        query = "tensorflow"
        count = 10
        # print ("Fetching first " + str(count) + " results for \"" + query + "\"...")
        response = search.search(query, count)
        # print(response)
        # print(len(response))
        print(i, time.time() - start)
        time.sleep(2)