'''
https://github.com/anthonyhseb/googlesearch/blob/master/googlesearch/googlesearch.py
'''
from .utils import distribute, ProxyRetriever, urlopen

import urllib
import time
from lxml.html import fromstring
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

def _search(query, n_results=10):
    SEARCH_URL = "https://google.com/search"
    RESULTS_PER_PAGE = 10

    searchResults = []

    i = 0
    while len(searchResults) < n_results:
        start = i * RESULTS_PER_PAGE
        text = urlopen(SEARCH_URL + \
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