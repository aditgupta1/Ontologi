import boto3
from boto3.dynamodb.conditions import Key, Attr
import argparse
import time

class DynamoDB(object):
    def __init__(self, region_name, endpoint_url):
        self.db = boto3.resource('dynamodb', 
            region_name=region_name, 
            endpoint_url=endpoint_url)

    def get_pages_table(self):
        """
        This table stores visited sites
        """
        try:
            pages_table = self.db.create_table(
                TableName='Pages',
                KeySchema=[
                    {
                        'AttributeName': 'url',
                        'KeyType': 'HASH'  #Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'url',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
        except self.db.meta.client.exceptions.ResourceInUseException:
            pages_table = self.db.Table('Pages')
        return pages_table

    def get_patterns_table(self):
        """
        This table stores entity patterns for named entity recognition (NER) 
        when parsing text.
        Only store patterns that have occurred to save space, then construct
        variants on the fly
        """
        try:
            patterns_table = self.db.create_table(
                TableName='Patterns',
                KeySchema=[
                    {
                        'AttributeName': 'id', # ent_id (see text_parser module)
                        'KeyType': 'HASH'  #Partition key
                    },
                    {
                        'AttributeName': 'pattern',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'pattern',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'N'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'TimestampIndex',
                        'KeySchema': [
                            {
                                'AttributeName': 'id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
        except self.db.meta.client.exceptions.ResourceInUseException:
            patterns_table = self.db.Table('Patterns')
        return patterns_table

    def delete_tables(self):
        self.get_pages_table().delete()
        self.get_patterns_table().delete()
        print('Tables deleted successfully!')

# if __name__ == '__main__':
#     # Argument parser
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--delete', action='store_true', 
#                         help='Delete all tables in database')
#     args = parser.parse_args()
    
#     dynamodb = DynamoDB()

#     pages_table = dynamodb.get_pages_table()
#     patterns_table = dynamodb.get_patterns_table()

#     print("Pages status:", pages_table.table_status)
#     print("Patterns status:", patterns_table.table_status)
    
#     # Delete tables
#     if args.delete:
#         dynamodb.delete_tables()
        