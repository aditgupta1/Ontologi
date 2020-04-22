# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from .settings import DYNAMODB_URL, NEO4J_URL, NEO4J_PSWD

import boto3
from boto3.dynamodb.conditions import Key, Attr
from py2neo import Graph, Node, Relationship

import time

class DBStorePipeline(object):
    """
    Store extracted information in DynamoDB and Neo4J
        entities
        patterns
        graph
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', 
                                        endpoint_url=DYNAMODB_URL)
        self.pages_table = self.dynamodb.Table('Pages')
        self.entities_table = self.dynamodb.Table('Entities')
        self.patterns_table = self.dynamodb.Table('Patterns')
        self.graph = Graph(NEO4J_URL, password=NEO4J_PSWD)

    def process_item(self, item, spider):
        graph = item['graph']
        # print('pipelines:34>', graph['nodes'])

        '''Add entities'''
        for ent in graph['nodes']:
            db_response = self.entities_table.get_item(
                Key={
                    'name': ent,
                }
            )
            
            if 'Item' in db_response.keys():
                self.entities_table.update_item(
                    Key={
                        'name': ent,
                    },
                    UpdateExpression='SET freq = :val',
                    ExpressionAttributeValues={
                        ':val': int(db_response['Item']['freq']) + 1
                    }
                )
            else:
                self.entities_table.put_item(
                    Item={
                        'name': ent,
                        'freq': 1,
                        'timestamp' : int(time.time()) # Timestamp created
                    }
                )

        '''Add nodes to graph'''
        for node in graph['nodes']:
            # Find node if exists
            n_match = _match_node(self.graph, 'Concept', node)
            print('67>', n_match)
            if n_match is None:
                n = Node('Concept', name=node, weight=1)
            else:
                n = Node('Concept', name=node, weight=n_match['weight']+1)
            self.graph.merge(n, 'Concept', 'name')

        for edge in graph['edges']:
            a_match = _match_node(self.graph, 'Concept', edge[0])
            a = Node('Concept', name=edge[0], weight=a_match['weight'])
            b_match = _match_node(self.graph, 'Concept', edge[1])
            b = Node('Concept', name=edge[1], weight=b_match['weight'])
            
            # Find relationship if exists
            rel_match = _match_relationship(self.graph, 'Concept', edge[0], edge[1])
            print('79>', rel_match, a, b)
            
            if rel_match is None:
                rel = Relationship(a, b, weight=1)
            else:
                rel = Relationship(a, b, weight=rel_match['weight']+1)

            self.graph.merge(rel, 'Concept', 'name')

        '''Add new patterns'''
        patterns = item['patterns']
        # print('pipelines:75>', len(patterns))

        for pat in patterns:
            db_response = self.patterns_table.get_item(
                Key={
                    'id': pat['id'],
                    'pattern' : pat['pattern']
                }
            )
            # print(db_response, 'Item' in db_response.keys())
            if 'Item' in db_response.keys():
                if 'hits' in pat.keys():
                    self.patterns_table.update_item(
                        Key={
                            'id': pat['id'],
                            'pattern' : pat['pattern']
                        },
                        UpdateExpression='SET freq = :val',
                        ExpressionAttributeValues={
                            ':val': int(db_response['Item']['freq']) + 1
                        }
                    )
            else:
                print('pipelines:98>', pat['id'], pat['pattern'])
                freq = 1 if 'hits' in pat.keys() else 0
                self.patterns_table.put_item(
                    Item={
                        'id': pat['id'],
                        'pattern' : pat['pattern'],
                        'freq' : freq
                    }
                )

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
            for node in db_response['Item']['nodes']:
                n_match = _match_node(self.graph, 'Concept', node)
                n = Node('Concept', name=node, weight=n_match['weight']-1)
                self.graph.merge(n, 'Concept', 'name')
            # Subtract old edges
            for edge in db_response['Item']['edges']:
                name1, name2 = edge.split(' ')
                a_match = _match_node(self.graph, 'Concept', name1)
                a = Node('Concept', name=name1, weight=a_match['weight'])
                b_match = _match_node(self.graph, 'Concept', name2)
                b = Node('Concept', name=name2, weight=b_match['weight'])

                rel_match = _match_relationship(self.graph, 'Concept', name1, name2)
                rel = Relationship(a, b, weight=rel_match['weight']-1)                    
                self.graph.merge(rel, 'Concept', 'name')

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

        return item

class DBPrunePipeline(object):
    """
    Prune
    Entities with only one occurrence after a minute are deleted,
    along with the associated patterns and node in the graph 
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', 
                                        endpoint_url=DYNAMODB_URL)
        self.entities_table = self.dynamodb.Table('Entities')
        self.patterns_table = self.dynamodb.Table('Patterns')
        self.graph = Graph(NEO4J_URL, password=NEO4J_PSWD)

    def process_item(self, item, spider):
        # time.sleep(5)

        # Remove rare patterns (one pattern per ent_id)
        # Get occurrence freq for each entity-id
        response = self.entities_table.query(
            IndexName='FreqIndex',
            KeyConditionExpression=Key('freq').eq(1)
        )
        pruned_ents = response['Items']
        # print('pipelines:134>', pruned_ents)
        # print('pipelines:135>', len(self.entities_table.scan()['Items']))

        current = time.time()
        for ent in pruned_ents:
            # print('pipelines:138>', current - int(ent['timestamp']))
            if ent['freq'] <= 1 and current - int(ent['timestamp']) > 60:
                print('pipelines:139>', ent)

                # Delete all associated patterns
                response = self.patterns_table.query(
                    KeyConditionExpression=Key('id').eq(ent['name'])
                )
                for it in response['Items']:
                    print('pipelines:146>', it)
                    self.patterns_table.delete_item(
                        Key={
                            'id' : it['id'],
                            'pattern' : it['pattern']
                        }
                    )

                # Delete item in entries table
                self.entities_table.delete_item(
                    Key={
                        'name' : ent['name']
                    }
                )
                
                # Delete node in graph
                node = Node('Concept', name=ent['name'])
                self.graph.delete(node)
            
        return item

def _match_node(graph, label, name):
    query = f'MATCH (a:{label}) WHERE a.name = "{name}" ' \
        'RETURN a.name AS name, a.weight AS weight'
    data = graph.run(query).data()
    if len(data) == 0:
        return None
    return data[0]

def _match_relationship(graph, label, name1, name2):
    query = f'MATCH (a:{label})-[r]->(b:{label})' \
        f'WHERE a.name = "{name1}" AND b.name = "{name2}"' \
        'RETURN r.weight AS weight'
    data = graph.run(query).data()
    if len(data) == 0:
        return None
    return data[0]