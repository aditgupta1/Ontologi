# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from concept_query.db import GraphDB, DynamoDB

import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import time
import matplotlib.pyplot as plt

class DBStorePipeline(object):
    """
    Store extracted information in DynamoDB and Neo4J
        entities
        patterns
        graph
    """
    
    def __init__(self):
        self.dynamodb = DynamoDB(region_name='us-west-2', endpoint_url='http://localhost:5000')
        self.pages_table = self.dynamodb.get_pages_table()
        self.patterns_table = self.dynamodb.get_patterns_table()
        self.graph = GraphDB(uri='bolt://localhost:7687', user='neo4j', password='pswd')

    def process_item(self, item, spider):
        graph = item['graph']
        # print('pipelines:34>', graph['nodes'])

        '''Add nodes to graph'''
        # start = time.time()
        query = "UNWIND $nodes AS node " \
            'MERGE (n:Concept {name: node}) ' \
            "ON CREATE SET n.weight = 1, n.timestamp = $timestamp " \
            "ON MATCH SET n.weight = n.weight + 1"
        self.graph.run(query, nodes=graph['nodes'], timestamp=timestamp())

        '''Add edges to graph'''
        query = 'UNWIND $edges AS edge ' \
            'MATCH (a:Concept {name: edge[0]}) ' \
            'MATCH (b:Concept {name: edge[1]}) ' \
            "MERGE (a)-[r:HAS]->(b) " \
            "ON CREATE SET r.weight = 1, r.timestamp = $timestamp " \
            "ON MATCH SET r.weight = r.weight + 1"
        self.graph.run(query, edges=graph['edges'], timestamp=timestamp())

        # print('pipelines:69>', time.time() - start, 'nodes:', len(graph['nodes']), 'edges:', len(graph['edges']))

        '''Add new patterns'''
        patterns = item['patterns']
        # print('pipelines:75>', len(patterns))

        with self.patterns_table.batch_writer() as batch:
            for pat in patterns:
                # print('pipelines:98>', pat['id'], pat['pattern'])
                batch.put_item(
                    Item={
                        'id': pat['id'],
                        'pattern' : pat['pattern'],
                        'timestamp' : timestamp()
                    }
                )
        # print('pipelines:105>', time.time() - start)

        '''Add graph to Pages table
        If exists already, subtract old nodes/edges from global graph and
        add new nodes/edges from page graph'''
        db_response = self.pages_table.get_item(
            Key={
                'url' : item['url']
            }
        )
        if 'Item' in db_response.keys():
            # Subtract old nodes
            query = "UNWIND $nodes AS node " \
                'MERGE (n:Concept {name: node}) ' \
                "ON MATCH SET n.weight = n.weight - 1"
            self.graph.run(query, nodes=db_response['Item']['nodes'])

            # Subtract old edges
            query = 'UNWIND $edges AS edge ' \
                'MATCH (a:Concept {name: edge[0]}) ' \
                'MATCH (b:Concept {name: edge[1]}) ' \
                "MERGE (a)-[r:HAS]->(b) " \
                "ON MATCH SET r.weight = r.weight - 1"
            self.graph.run(query, edges=[edge.split(' ') for edge in db_response['Item']['edges']])

            # Updated pages table
            self.pages_table.update_item(
                Key={
                    'url': item['url']
                },
                UpdateExpression='SET nodes = :val1, edges = :val2',
                ExpressionAttributeValues={
                    ':val1' : graph['nodes'],
                    ':val2' : [' '.join(edge) for edge in graph['edges']]
                }
            )
        else:
            self.pages_table.put_item(
                Item={
                    'url' : item['url'],
                    'nodes' : graph['nodes'],
                    'edges' : [' '.join(edge) for edge in graph['edges']]
                }
            )
        # print('pipelines:155>', time.time() - start)

        return item

    # def execute(self, query, **kwargs):
    #     """
    #     Handle database deadlocks
    #     Try up to 4 times before finally quiting
    #     Sleep for 1 second before retrying
    #     """
        
    #     num_tries = 0
    #     while num_tries < 4:
    #         try:
    #             self.graph.run(query, **kwargs)
    #             return
    #         except TransientError:
    #             print('WARNING: TransientError database deadlock (retrying)')
    #             num_tries += 1
    #             time.sleep(0.5)
        
    #     print('ERROR: TransientError database deadlock (quit after 4 tries)')

# class DBPrunePipeline(object):
#     """
#     Prune
#     Entities with only one occurrence after a minute are deleted,
#     along with the associated patterns and node in the graph 
#     """
    
#     def __init__(self):
#         self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', 
#                                         endpoint_url=DYNAMODB_URL)
#         self.entities_table = self.dynamodb.Table('Entities')
#         self.patterns_table = self.dynamodb.Table('Patterns')
#         self.graph = Graph(NEO4J_URL, password=NEO4J_PSWD)

#         if not os.path.isdir('../test_results'):
#             os.mkdir('../test_results')
#         if not os.path.isdir('../test_results/freq_dist'):
#             os.mkdir('../test_results/freq_dist')

#     def process_item(self, item, spider):
#         # Save freq distribution
#         plt.figure(figsize=(8,6))
#         for delay in [0, 90]:
#             query = f'MATCH (p:Concept) WHERE p.timestamp < {timestamp(delay)} RETURN p.weight AS weight'
#             weights = [x['weight'] for x in self.graph.run(query).data()]
#             plt.hist(weights, bins=20, alpha=0.25, label=str(delay))
#         plt.legend()
#         plt.savefig(f'../test_results/freq_dist/{timestamp()}.png')

#         # Remove rare patterns (one pattern per ent_id)
#         # Get occurrence freq for each entity-id
#         # response = self.entities_table.query(
#         #     IndexName='FreqIndex',
#         #     KeyConditionExpression=Key('freq').eq(1)
#         # )
#         query = 'MATCH (p:Concept) WHERE p.weight = 1 AND ' \
#             f'p.timestamp < {timestamp(90)} RETURN p.name AS name'

#         for ent in self.graph.run(query).data():
#             # print('pipelines:138>', current - int(ent['timestamp']))
#             # print('pipelines:139>', ent)

#             # Delete all associated patterns
#             response = self.patterns_table.query(
#                 KeyConditionExpression=Key('id').eq(ent['name'])
#             )
#             for it in response['Items']:
#                 # print('pipelines:146>', it)
#                 self.patterns_table.delete_item(
#                     Key={
#                         'id' : it['id'],
#                         'pattern' : it['pattern']
#                     }
#                 )

#             # # Delete item in entries table
#             # self.entities_table.delete_item(
#             #     Key={
#             #         'name' : ent['name']
#             #     }
#             # )
            
#             # Delete node in graph
#             # node = Node('Concept', name=ent['name'])
#             # self.graph.delete(node)
#             ent_name = ent['name']
#             self.graph.run(f'MATCH (p:Concept) WHERE p.name="{ent_name}" DETACH DELETE p')
            
#         return item         

def timestamp(delay=0):
    return int(time.time()) - delay