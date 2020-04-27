from concept_query import GraphCrawl, GraphDB

import argparse
import os
import requests
import json

def create_tables():
    os.system('python db/dynamo_db.py')
    # os.system('python db/neo4j.py')

def delete_tables():
    os.system('python db/dynamo_db.py --delete')
    # os.system('python db/neo4j.py --delete')
    graph = GraphDB()
    graph.delete_table()

def stop_crawlers():
    """
    Cancel all pending and running scrapyd jobs"""

    response = requests.get('http://localhost:6800/listjobs.json', params={
        'project' : 'web_crawler'
    })
    data = json.loads(response.text)
    current_jobs = data['pending'] + data['running']
    
    for job in current_jobs:
        print(f'Canceling job: {job["id"]}')
        response = requests.post('http://localhost:6800/cancel.json', data={
            'project' : 'web_crawler',
            'job' : job['id']
        })
        print(response.text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--delete', action='store_true', 
                        help='Delete all tables in database')
    parser.add_argument('--stop', action='store_true', 
                        help='Delete all tables in database')
    args = parser.parse_args()

    if args.stop:
        stop_crawlers()
        exit()

    if args.delete:
        delete_tables()

    create_tables()

    crawler = GraphCrawl(n_crawlers=8, iterations=2, pages_per_concept=5)

    # Run crawlers
    crawler.crawl(args.query)