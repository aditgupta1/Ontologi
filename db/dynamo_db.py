import boto3
from boto3.dynamodb.conditions import Key, Attr
import argparse

def get_pages_table(db):
    """
    This table stores visited sites
    """
    try:
        sites_table = db.create_table(
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
    except db.meta.client.exceptions.ResourceInUseException:
        sites_table = db.Table('Pages')
    return sites_table

def get_entities_table(db):
    """
    This table stores parsed entities and their page frequencies
    """
    try:
        entities_table = db.create_table(
            TableName='Entities',
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'  #Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'freq',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'FreqIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'freq',
                            'KeyType': 'HASH'
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
    except db.meta.client.exceptions.ResourceInUseException:
        entities_table = db.Table('Entities')
    return entities_table

def get_patterns_table(db):
    """
    This table stores entity patterns for named entity recognition (NER) 
    when parsing text.
    """
    try:
        patterns_table = db.create_table(
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
                    'AttributeName': 'freq',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'FreqIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'freq',
                            'KeyType': 'HASH'
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
    except db.meta.client.exceptions.ResourceInUseException:
        patterns_table = db.Table('Patterns')
    return patterns_table

if __name__ == '__main__':
    # Argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--delete', action='store_true', 
                        help='Delete all tables in database')
    args = parser.parse_args()
    
    db = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:5000")

    pages_table = get_pages_table(db)
    entities_table = get_entities_table(db)
    patterns_table = get_patterns_table(db)

    print("Pages status:", pages_table.table_status)
    print("Entities status:", entities_table.table_status)
    print("Patterns status:", patterns_table.table_status)

    # Get tables
    # print(list(db.tables.all()))

    # Get all items
    response = patterns_table.scan()
    print('Patterns:', len(response['Items']))

    # Get query
    # response = sites_table.query(
    #     KeyConditionExpression=Key('url').eq(response['Items'][0]['url'])
    # )
    # print(response['Items'])

    # response = patterns_table.scan(
    #     FilterExpression=Attr('id').eq('machine')
    # )
    # items = response['Items']
    # print(items)

    # print(pages_table.get_item(
    #     Key={
    #         'url' : 'https://en.wikipedia.org/wiki/TensorFlow'
    #     }
    # ))

    # Delete tables
    if args.delete:
        pages_table.delete()
        entities_table.delete()
        patterns_table.delete()
        print('Tables deleted successfully!')