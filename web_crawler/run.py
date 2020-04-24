from web_crawler.utils import GoogleSearch
import requests
import os
from math import ceil
import json
import time
from py2neo import Graph

if not os.path.isdir('./urls'):
    os.mkdir('./urls')

num_crawlers = 8
googlesearch = GoogleSearch()
print('Getting starting URLs...')
start_urls = googlesearch.search('tensorflow', num_results=20)
graph = Graph('bolt://localhost:7687', password='pswd')
scraped_concepts = ['tensorflow']

for i in range(2):
    urls_per_crawler = ceil(len(start_urls) / num_crawlers)

    for i in range(num_crawlers):
        start = i * urls_per_crawler
        if i < num_crawlers - 1:
            end = (i+1) * urls_per_crawler
        else:
            end = len(start_urls)

        with open(f'urls/spider_{i+1}.txt', 'w', encoding='utf-8') as f:
            for url in start_urls[start:end]:
                f.write(url + '\n')

    for i in range(num_crawlers):
        response = requests.post('http://localhost:6800/schedule.json', data={
            'project' : 'web_crawler',
            'spider' : 'page_graph',
            'url_path' : f'urls/spider_{i+1}.txt',
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
    print('Getting next URLs...')
    query = 'MATCH (p:Concept) WHERE p.weight > 2 RETURN p.name AS name'
    start_urls = []
    for node in graph.run(query).data():
        if node['name'] not in scraped_concepts:
            start_urls += googlesearch.search(node['name'].replace('-',' '), num_results=5)
            scraped_concepts.append(node['name'])