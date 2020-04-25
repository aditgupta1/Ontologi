from web_crawler.utils import GoogleSearch
import requests
import os
from math import ceil
import json
import time
from py2neo import Graph

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

if not os.path.isdir('./urls'):
    os.mkdir('./urls')

num_crawlers = 8
iterations = 2

googlesearch = GoogleSearch()
print('Getting starting URLs...')
start_urls = googlesearch.search('tensorflow', num_results=20)
print(start_urls)
graph = Graph('bolt://localhost:7687', password='pswd')
scraped_concepts = ['tensorflow']

for it in range(iterations):
    urls_per_crawler = distribute(start_urls, num_crawlers)

    for i in range(num_crawlers):
        with open(f'urls/spider_{i+1}.txt', 'w', encoding='utf-8') as f:
            for url in urls_per_crawler[i]:
                f.write(url + '\n')

    for i in range(num_crawlers):
        response = requests.post('http://localhost:6800/schedule.json', data={
            'project' : 'web_crawler',
            'spider' : 'page_graph',
            'url_path' : f'urls/spider_{i+1}.txt',
            # 'save_name' : f'spider-{i+1}_{it}'
        })
        print(response.text)

    is_finished = False
    while not is_finished:
        time.sleep(10)
        response = requests.get('http://localhost:6800/listjobs.json', params={
            'project' : 'web_crawler'
        })
        data = json.loads(response.text)
        is_finished = len(data['pending']) + len(data['running']) == 0
        print(int(time.time()))

    # Get next start urls
    if it < iterations - 1:
        print('Getting next URLs...')
        query = 'MATCH (p:Concept) WHERE p.weight > 2 RETURN p.name AS name'
        start_urls = []
        for node in graph.run(query).data():
            if node['name'] not in scraped_concepts:
                search_query = node['name'].replace('-',' ')
                start_urls += googlesearch.search(search_query, num_results=5)
                scraped_concepts.append(node['name'])