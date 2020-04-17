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

class GraphPipeline(object):
    """
    Integrate page graphs into global entity graph.
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2', 
                                        endpoint_url=DYNAMODB_URL)
        self.entities_table = self.dynamodb.Table('Entities')
        self.graph = Graph(NEO4J_URL, password=NEO4J_PSWD)

    def process_item(self, item, spider):
        graph = item['graph']
        # print('pipelines:25>', graph['nodes'])

        # DynamoDB
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
                        'freq': 1
                    }
                )

        # Neo4j
        for edge in graph['edges']:
            a = Node('Concept', name=edge[0])
            b = Node('Concept', name=edge[1])
            rel = Relationship(a, b)
            self.graph.merge(rel, 'Concept', 'name')
            
        return item

class PatternsPipeline(object):
    """
    Add patterns from pages to database
    Handle near duplicates and remove false/rare patterns
    """

    def __init__(self):
        self.db = boto3.resource('dynamodb', region_name='us-west-2', 
                                endpoint_url=DYNAMODB_URL)
        self.table = self.db.Table('Patterns')

    def process_item(self, item, spider):
        patterns = item['patterns']
        # print('pipelines:66>', patterns)

        for pat in patterns:
            db_response = self.table.get_item(
                Key={
                    'id': pat['id'],
                    'pattern' : pat['pattern']
                }
            )
            # print(db_response, 'Item' in db_response.keys())
            if 'Item' in db_response.keys():
                if 'hits' in pat.keys():
                    self.table.update_item(
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
                print(pat['id'], pat['pattern'])
                freq = 1 if 'hits' in pat.keys() else 0
                self.table.put_item(
                    Item={
                        'id': pat['id'],
                        'pattern' : pat['pattern'],
                        'freq' : freq,
                        # 'creation_timestamp' : {'N' : str(int(time.time()))}
                    }
                )

        # Clean patterns

        # Remove rare patterns (one pattern per ent_id)
        # response = table.query(
        #     KeyConditionExpression=Key('username').eq('johndoe')
        # )
        # items = response['Items']

        return item