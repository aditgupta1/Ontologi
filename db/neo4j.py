from py2neo import Graph, Node, Relationship
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--delete', action='store_true', 
                    help='Delete all tables in database')
args = parser.parse_args()

graph = Graph('bolt://localhost:7687', password='pswd')

# Insert node
# graph.run("MERGE (n:Concept {name: 'tensorflow'})")
# a = Node('Concept', name='tensorflow')
# graph.merge(a, 'Concept', 'name')

# Get all nodes
cursor = graph.run('MATCH (p) RETURN p')
for record in cursor:
    print(record)

if args.delete:
    graph.run('MATCH (p) DETACH DELETE p')
    print("All nodes deleted successfully!")