from concept_query import GraphCrawl, GraphDB, DynamoDB, SqlDB

import argparse
import os
import requests
import json
import toml

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

    # DB configs
    config = toml.load('config.toml')
    neo4j_config = config['NEO4J_LOCAL']
    sql_config = config['SQL_CLOUD']

    if args.stop:
        stop_crawlers()
        exit()

    if args.delete:
        graph = GraphDB(uri=neo4j_config['URI'],
            user=neo4j_config['USER'],
            password=neo4j_config['PASSWORD'])
        graph.delete_table()

        dynamodb = DynamoDB(region_name=config['DYNAMODB_LOCAL']['REGION_NAME'],
            endpoint_url=config['DYNAMODB_LOCAL']['URI'])
        dynamodb.get_pages_table().delete()
        dynamodb.get_patterns_table().delete()

        print('Tables deleted successfully!')

        sql = SqlDB.fromconfig(sql_config)
        sql.delete()

    crawler = GraphCrawl(n_crawlers=16, iterations=2, pages_per_concept=5,
                        dynamodb_config=config['DYNAMODB_LOCAL'],
                        neo4j_config=neo4j_config,
                        sql_config=sql_config,
                        task_queue_config=config['TASK_QUEUE'])

    # Run crawlers
    crawler.crawl(args.query)