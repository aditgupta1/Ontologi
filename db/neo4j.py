from py2neo import Graph, Node, Relationship, NodeMatcher
import argparse
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('--delete', action='store_true', 
                    help='Delete all tables in database')
args = parser.parse_args()

graph = Graph('bolt://localhost:7687', password='pswd')

# Insert node
# graph.run("MERGE (n:Concept {name: 'tensorflow'})")
# a = Node('Concept', name='tensorflow')
# graph.merge(a, 'Concept', 'name')

# Match node
# query = 'MATCH (a:Concept) WHERE a.name = "tensorflow" RETURN a.name AS name, a.weight AS weight'
# query = 'MATCH (a:Concept)-[r]->(b:Concept)' \
#         'WHERE a.name = "announcement" AND b.name = "tensorflow"' \
#         'RETURN r.weight AS weight'

# cursor = graph.run(query)
# print(cursor.data())
# for record in cursor:
#     print(record)

# Get all nodes
data = graph.run('MATCH (p:Concept) RETURN p.weight AS weight').data()
weights = [x['weight'] for x in data]
print('Nodes:', len(data))
plt.hist(weights, bins=20)
plt.show()

# print('35>', graph.run('MATCH (p:Concept) WHERE p.name="requirement" RETURN p').data())

# # a = Node('Concept', name='requirement')
# # graph.delete(a)
# graph.run('MATCH (p) WHERE p.name="requirement" DETACH DELETE p')

# print('40>', graph.run('MATCH (p:Concept) WHERE p.name="requirement" RETURN p').data())

if args.delete:
    graph.run('MATCH (p) DETACH DELETE p')
    print("All nodes deleted successfully!")