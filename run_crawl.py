from concept_query import GraphCrawl

import argparse
import os

def create_tables():
    os.system('python db/dynamo_db.py')
    os.system('python db/neo4j.py')

def delete_tables():
    os.system('python db/dynamo_db.py --delete')
    os.system('python db/neo4j.py --delete')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--delete', action='store_true', 
                        help='Delete all tables in database')
    args = parser.parse_args()

    if args.delete:
        delete_tables()

    create_tables()

    crawler = GraphCrawl(n_crawlers=8, iterations=2, pages_per_concept=5)
    crawler.crawl(args.query)