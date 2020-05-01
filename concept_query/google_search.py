'''
https://github.com/anthonyhseb/googlesearch/blob/master/googlesearch/googlesearch.py
'''
from .utils import distribute, ProxyRetriever, urlopen

import urllib
import time
from lxml.html import fromstring
import multiprocessing
from itertools import cycle
from lxml import etree
from pprint import pprint

class GoogleSearch:
    def __init__(self, max_proc=8, use_proxy=False, engine='bing'):
        self.max_proc = max_proc
        self.proxies = ProxyRetriever(10)
        self.use_proxy = use_proxy
        self.engine = engine

    def search(self, query, n_results=10, full=False):
        """
        Get search results
        args:
            query: string
            n_results: number of results (may scrape more than this)
            full: if true, return url, title, and caption
                if false, only return url
                applies only to single search query
        """
        proxies = self.proxies.get() if self.use_proxy else []

        if isinstance(query, str):    
            return _search(query, n_results, proxies=proxies, 
                full=full, engine=self.engine)

        # List of queries
        n_proc = min(len(query), self.max_proc)
        return self._batch_search(query, n_results, n_proc, proxies)

    def _batch_search(self, query_list, n_results, n_proc, proxies):
        proc_lists = distribute(query_list, n_proc)

        with multiprocessing.Manager() as manager: 
            # creating a list in server process memory 
            records = manager.list()

            processes = []
            for i in range(n_proc):
                print(proc_lists[i])
                args = (proc_lists[i], records, n_results, proxies, self.engine)
                p = multiprocessing.Process(target=_search_list, args=args)
                processes.append(p)

            for i in range(n_proc):
                processes[i].start()

            for i in range(n_proc):
                processes[i].join()
            
            result = list(records)

        return result

def _search(query, n_results=10, proxies=[], full=False, engine='bing'):
    """
    Use bing for only getting links because less likely to be blocked
        But not all search results have nicely formatted text captions
    Use google for retrieving full search results
    
    args:
        n_results: number of search results
        proxies: list of proxies
        full: if true return (url, title, caption)
            if false, return url only
        engine: bing or google
    returns:
        list
    """
    # Uncomment to use Google
    # SEARCH_URL = "https://google.com/search"

    # Uncomment to use Bing
    # SEARCH_URL = "https://www.bing.com/search"

    RESULTS_PER_PAGE = 10

    searchResults = []
    url_set = set()

    # Proxies
    if len(proxies) == 0:
        proxy = None
    else:
        proxy_pool = cycle(proxies)
        print(proxies)
        proxy_ip = next(proxy_pool)
        proxy = {'http' : proxy_ip, 'https' : proxy_ip}

    i = 0
    while len(searchResults) < n_results:
        start = i * RESULTS_PER_PAGE
        url = _get_search_url(query, start, engine)

        if proxy is None:
            text = urlopen(url)
        else:
            while True:
                try:
                    print(proxy)
                    text = urlopen(url, proxies=proxy)
                    break
                except:
                    print("Skipping. Connnection error")
                    proxy_ip = next(proxy_pool)
                    proxy = {'http' : proxy_ip, 'https' : proxy_ip}

        # print('Finished', url)
        parser = fromstring(text)
        # s = etree.tostring(parser, pretty_print=True).decode('utf-8')
        
        # with open('bing.html', 'w', encoding='utf-8') as f:
        #     f.write(s)

        if engine == 'bing':
            data = _parse_bing(parser, full)
        elif engine == 'google':
            data = _parse_google(parser, full)
        else:
            raise ValueError('invalid search engine', engine)

        for item in data:
            if item['url'] not in url_set:
                if full:
                    searchResults.append(item)
                else:
                    searchResults.append(item['url'])
                url_set.add(item['url'])
        i += 1

        time.sleep(1)
  
    return searchResults[:n_results]

def _get_search_url(query, start, engine='bing'):
    """
    Get search result
    args:
        query: search text
        start: starting result index
        engine: bing or google
    """
    if engine == 'bing':
        SEARCH_URL = "https://www.bing.com/search"
        url = SEARCH_URL + "?q="+ urllib.parse.quote(query) + \
                ("" if start==0 else f"&first={start}")
    elif engine == 'google':
        SEARCH_URL = "https://google.com/search"
        url = SEARCH_URL + "?q="+ urllib.parse.quote(query) + \
                ("" if start==0 else f"&start={start}")
    else:
        raise ValueError('invalid search engine', engine)
    
    return url

def _parse_bing(parser, full=False):
    print('bing')
    data = []
    for result in parser.xpath('//li[@class="b_algo"]'):
        try:
            href = result.xpath('h2//a')[0].get('href')
            if full:
                item = {
                    'url' : href,
                    'title' : ' '.join(result.xpath('h2/a//text()')),
                    'caption' : ' '.join(result.xpath('div[@class="b_caption"]//p//text()'))
                }
            else:
                item = {'url' : href}
            data.append(item)
        except IndexError:
            pass
    return data

def _parse_google(parser, full=False):
    print('google')
    data = []
    for result in parser.xpath('//div[@class="rc"]'):
        href =  result.xpath('div[@class="r"]/a')[0].get('href')
        if full:
            item = {
                'url' : href,
                'title' : ' '.join(result.xpath('div[@class="r"]/a/h3//text()')),
                'caption' : ' '.join(result.xpath('div[@class="s"]//span[@class="st"]//text()'))
            }
        else:
            item = {
                'url' : href
            }
        data.append(item)
    return data

def _search_list(arr, records=[], n_results=10, proxies=[], engine='bing'):
    for query in arr:
        for result in _search(query, n_results, proxies, engine):
            records.append(result)

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