'''
https://github.com/anthonyhseb/googlesearch/blob/master/googlesearch/googlesearch.py
'''
import urllib
import math
from bs4 import BeautifulSoup
import time
        
class GoogleSearch:
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/ 58.0.3029.81 Safari/537.36"
    SEARCH_URL = "https://google.com/search"
    RESULT_SELECTOR = "div.r > a"
    RESULTS_PER_PAGE = 10
    DEFAULT_HEADERS = [
        ('User-Agent', USER_AGENT),
        ("Accept-Language", "en-US,en;q=0.5"),
    ]
    
    def search(self, query, num_results=10):
        searchResults = []
        # pages = int(math.ceil(num_results / float(GoogleSearch.RESULTS_PER_PAGE)))

        i = 0
        while len(searchResults) < num_results:
            start = i * GoogleSearch.RESULTS_PER_PAGE
            opener = urllib.request.build_opener()
            opener.addheaders = GoogleSearch.DEFAULT_HEADERS
            response = opener.open(GoogleSearch.SEARCH_URL + \
                "?q="+ urllib.parse.quote(query) + ("" if start==0 else f"&start={start}"))
            # print(response.geturl())
            # with open(f'test{i}.html', 'w', encoding='utf-8') as f:
            #     f.write(response.read().decode('utf-8'))
            soup = BeautifulSoup(response.read(), "lxml")
            response.close()

            # print(soup.select(GoogleSearch.RESULT_SELECTOR))
            for link in soup.select(GoogleSearch.RESULT_SELECTOR):
                searchResults.append(link.get('href'))
            i += 1

        return searchResults[:num_results]
        
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