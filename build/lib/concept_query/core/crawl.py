from ..google_search import GoogleSearch
from ..db import GraphDB, DynamoDB
from ..utils import distribute

import os
import requests
import json
import time

# from py2neo import Graph
import boto3
from boto3.dynamodb.conditions import Key, Attr

class GraphCrawl(object):
    def __init__(self, n_crawlers=8, iterations=2, pages_per_concept=5,
            dynamodb_config={}, neo4j_config={}):
        """
        Initialize graph crawler
        args:
            n_crawlers: number of concurrent crawlers
                https://scrapyd.readthedocs.io/en/stable/config.html
                (set max_proc_per_cpu in scrapyd conf)
            iterations: number of degrees of freedom to crawl
            pages_per_concept: number of urls to scrape per concept
            dynamodb_config: dict-like object (e.g., ConfigParser section)
            neo4j_config: see dynamodb_config
        """
        
        os.makedirs('./urls', exist_ok=True)
        self.n_crawlers = n_crawlers
        self.iterations = iterations
        self.pages_per_concept = pages_per_concept
        self.googlesearch = GoogleSearch(max_proc=16)

        # Databases
        self.neo4j_config = neo4j_config
        self.graph = GraphDB(uri=neo4j_config['URI'],
            user=neo4j_config['USERNAME'], 
            password=neo4j_config['PASSWORD'],
            encrypted=neo4j_config['ENCRYPTED'])

        self.dynamodb_config = dynamodb_config
        self.dynamodb = DynamoDB(region_name=dynamodb_config['REGION_NAME'],
            endpoint_url=dynamodb_config['URI'])
        self.patterns_table = self.dynamodb.get_patterns_table()

    def crawl(self, query):
        """
        Run crawlers on query
        args:
            query: string
        """

        print('Getting starting URLs...')
        start_urls = self.googlesearch.search(query, n_results=20) #self.pages_per_concept)
        print(start_urls)
        scraped_concepts = set([query])

        for it in range(self.iterations):
            crawler_urls = distribute(start_urls, self.n_crawlers)
            crawler_paths = []

            for i in range(self.n_crawlers):
                # Use absolute path because spider is deployed from web_crawler dir
                path = os.path.abspath(f'urls/spider_{i+1}.txt')
                with open(path, 'w', encoding='utf-8') as f:
                    for url in crawler_urls[i]:
                        f.write(url + '\n')
                crawler_paths.append(path)

            for i in range(self.n_crawlers):
                if len(crawler_urls[i]) > 0:
                    response = requests.post('http://localhost:6800/schedule.json', data={
                        'project' : 'web_crawler',
                        'spider' : 'page_graph',
                        'url_path' : crawler_paths[i],
                        # 'save_name' : f'spider-{i+1}_{it}'
                        'dynamodb_region_name' : self.dynamodb_config['REGION_NAME'],
                        'dynamodb_uri' : self.dynamodb_config['URI']
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

            # Perform pruning
            self._prune_db()

            # Get next start urls
            if it < self.iterations - 1:
                start = time.time()
                print('Getting next URLs...')
                query = 'MATCH (p:Concept) RETURN p.name AS name'
                data = self.graph.run(query).data()
                print('crawl:73> concepts=', len(data))

                query_list = []
                for node in data:
                    if node['name'] not in scraped_concepts:
                        query_list.append(node['name'].replace('-',' '))
                        scraped_concepts.add(node['name'])

                start_urls = self.googlesearch.search(query_list, n_results=self.pages_per_concept)
                print('crawl:82> urls=', len(start_urls))
                print('crawl:83> unique urls=', len(set(start_urls)))
                print(time.time() - start)

                start_urls = list(set(start_urls))

                # Delete current graph 
                self.graph.run('MATCH (p) DETACH DELETE p')
                print('Graph deleted successfully!')

    def _prune_db(self):
        """Consolidate patterns (identical patterns with different ids)"""
        # Get patterns and convert to python dict
        db_response = self.patterns_table.scan()
        patterns = {}
        for item in db_response['Items']:
            if item['pattern'] in patterns.keys():
                # print(item['pattern'], patterns[item['pattern']], item['id'])
                patterns[item['pattern']].add(item['id'])
            else:
                patterns[item['pattern']] = set([item['id'],])

        # Disjoint sets of ent ids with overlapping patterns
        duplicate_groups = []
        for p in patterns.keys():
            if len(patterns[p]) > 1:
                # print(p, patterns[p])
                for ent_id in patterns[p]:
                    i = 0
                    while i < len(duplicate_groups):
                        if ent_id in duplicate_groups[i]:
                            duplicate_groups[i].update(patterns[p])
                            break
                        i += 1
                    if i == len(duplicate_groups):
                        duplicate_groups.append(patterns[p])
        # print(duplicate_groups)

        for group in duplicate_groups:
            all_cases = []
            for ent_id in group:
                db_response = self.patterns_table.query(
                    KeyConditionExpression=Key('id').eq(ent_id)
                )
                all_cases += db_response['Items']
            
            merge = None

            # Case 1: Acroynm
            for case in all_cases:
                if is_acroynm(case):
                    upper_letters = [c.lower() for c in case['pattern'] if c.isupper()]
                    for ent_id in group:
                        tokens = ent_id.split('-')
                        if len(upper_letters) == len(tokens) and \
                                all([upper_letters[i] == tokens[i][0] for i in range(len(tokens))]):
                            merge = ent_id

            print('crawl:156>', merge)

            if merge is not None:
                print('crawl:159>', group)

                with self.patterns_table.batch_writer() as batch:
                    for case in all_cases:
                        if case['id'] != merge:
                            batch.delete_item(
                                Key={
                                    'id': case['id'],
                                    'pattern' : case['pattern']
                                }
                            )
                            batch.put_item(
                                Item={
                                    'id': case['id'],
                                    'pattern' : merge
                                }
                            )

        """Consolidate nodes using applicable patterns"""
        time.sleep(1)
        db_response = self.patterns_table.scan()
        patterns = {}
        for item in db_response['Items']:
            patterns[item['pattern']] = item['id']

        nodes_to_update = []

        db_response = self.graph.run('MATCH (n:Concept) RETURN n.name AS name, n.weight AS weight')
        for item in db_response.data():
            concept = item['name']
            if concept in patterns.keys() and concept != patterns[concept]:
                nodes_to_update.append((item, patterns[concept]))

        # print(nodes_to_update)

        for old, new in nodes_to_update:
            print('crawl:195>', old['name'], new)
            query = 'MATCH (a:Concept {name: $name})-[r:HAS]->(b:Concept) ' \
                'RETURN b.name AS name, r.weight AS weight'
            out_edges = self.graph.run(query, name=old['name']).data()
            # print('out', out_edges)

            query = 'MATCH (a:Concept {name: $name})<-[r:HAS]-(b:Concept) ' \
                'RETURN b.name AS name, r.weight AS weight'
            in_edges = self.graph.run(query, name=old['name']).data()
            # print('in', in_edges)

            # Delete these edges
            self.graph.run('MATCH (a:Concept {name: $name}) DETACH DELETE a', name=old['name'])

            # Add node weight to new node
            self.graph.run('MATCH (a:Concept {name: $name}) SET a.weight = a.weight + $old_weight',
                            name=new, old_weight=old['weight'])

            # Relink edges from old to new
            query = 'UNWIND $out_edges AS x ' \
                'MATCH (a:Concept {name: $new}) ' \
                'MATCH (b:Concept {name: x.name}) ' \
                "MERGE (a)-[r:HAS]->(b) " \
                "ON CREATE SET r.weight = x.weight, r.timestamp = -1 " \
                "ON MATCH SET r.weight = r.weight + x.weight"
            self.graph.run(query, new=new, out_edges=out_edges)

            query = 'UNWIND $in_edges AS x ' \
                'MATCH (a:Concept {name: $new}) ' \
                'MATCH (b:Concept {name: x.name}) ' \
                "MERGE (a)<-[r:HAS]-(b) " \
                "ON CREATE SET r.weight = x.weight, r.timestamp = -1 " \
                "ON MATCH SET r.weight = r.weight + x.weight"
            self.graph.run(query, new=new, in_edges=in_edges)

            # print(self.graph.run('MATCH (n:Concept {name: $name}) RETURN n', name=old['name']).data())

def is_acroynm(pattern):
    if pattern['pattern'].isupper() and pattern['pattern'].lower() == pattern['id']:
        return True
    if pattern['pattern'][:-1].isupper() and pattern['pattern'][-1] == 's' and \
            pattern['pattern'].lower() == pattern['id']:
        return True
    return False