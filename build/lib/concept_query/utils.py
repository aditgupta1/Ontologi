import urllib.request
import time
from lxml.html import fromstring
import os
import sqlite3
from itertools import cycle
import requests

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
        print('Refreshing proxies...')

        url = 'https://free-proxy-list.net/'
        text = urlopen(url)
        parser = fromstring(text)
        proxies = set()

        counter = 0
        i = 0
        rows = parser.xpath('//tbody/tr')
        while counter < self.n_proxies and i < len(rows):
            if rows[i].xpath('.//td[7][contains(text(),"yes")]'):
                proxy = ":".join([rows[i].xpath('.//td[1]/text()')[0], rows[i].xpath('.//td[2]/text()')[0]])
                proxies.add(proxy)
                counter += 1
            i += 1

        self.proxies = proxies
        self.timestamp = time.time()

    def save_proxies(self, filepath):
        with open(filepath, 'w') as f:
            for proxy in self.proxies:
                f.write(proxy + '\n')
        print(f'Proxies saved successfully at {filepath}!')

    def verify(self):
        proxy_pool = cycle(self.proxies)

        url = 'https://httpbin.org/ip'
        for i in range(1,11):
            #Get a proxy from the pool
            proxy = next(proxy_pool)
            print("Request #%d"%i)
            try:
                response = requests.get(url,proxies={"http": proxy, "https": proxy})
                print(response.json())
            except:
                #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
                #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 
                print("Skipping. Connnection error")

def urlopen(url, proxies=None):
    headers = [
        # ('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) " \
        #     "AppleWebKit/537.36 (KHTML, like Gecko) " \
        #     "Chrome/ 58.0.3029.81 Safari/537.36"),
        ('User-Agent', "Mozilla/5.0 (X11; Linux x86_64) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) " \
            "Chrome/51.0.2704.103 Safari/537.36"),
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

class TaskQueue(object):
    """
    Task queue for urls to scrape (FIFO queue)
    """
    
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.create()
    
    def create(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS TASKS
            (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
            URL        TEXT     NOT NULL,
            STATUS     TEXT,
            START_TS REAL,
            FINISH_TS REAL);''')

    def is_empty(self):
        response = self.conn.execute('SELECT * FROM TASKS WHERE STATUS IS NULL')
        return len(list(response)) == 0

    def peek(self):
        """
        Get task (return None if empty)
        returns:
            (id, url)
        """
        if self.is_empty():
            return None

        query = "SELECT ID, URL FROM TASKS WHERE STATUS IS NULL LIMIT 1"
        data = list(self.conn.execute(query))[0]
        return data

    def push(self, url):
        # print('119>', url)
        query = "INSERT INTO TASKS (URL) VALUES (?)"
        self.conn.execute(query, (url,))
        self.conn.commit()

    def update_working(self, pid, timestamp=None):
        """Update status to working"""
        if timestamp is None:
            timestamp = time.time()
        query = "UPDATE TASKS SET STATUS = 'WORKING', START_TS = ? WHERE ID = ?"
        self.conn.execute(query, (timestamp, pid))
        self.conn.commit()

    def update_completed(self, pid, timestamp=None):
        """Update status to done"""
        if timestamp is None:
            timestamp = time.time()
        query = "UPDATE TASKS SET STATUS = 'DONE', FINISH_TS = ? WHERE ID = ?"
        self.conn.execute(query, (timestamp, pid))
        self.conn.commit()

    def select(self):
        return list(self.conn.execute('SELECT * FROM TASKS'))

    def pop(self):
        """Get task and update status
        Does not delete item as in typical queue implementation"""

        data = self.peek()
        if data is None:
            return None

        pid, url = data
        self.update_working(pid)
        return pid, url

    def clear(self):
        self.conn.execute("DROP TABLE IF EXISTS TASKS")
        # self.conn.commit()
        print('Task queue cleared successfully!')

        self.create()