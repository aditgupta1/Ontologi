from py2neo import Graph, Node, Relationship, NodeMatcher
import argparse
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--delete', action='store_true', 
                    help='Delete all tables in database')
args = parser.parse_args()

graph = Graph('bolt://localhost:7687', password='pswd')

# Get node weights
# data = graph.run('MATCH (p:Concept) RETURN p.weight AS weight').data()
# weights = [x['weight'] for x in data]
# print('Nodes:', len(data))
# plt.hist(weights, bins=40)
# plt.show()

# Save query graph to csv
# query = "MATCH (a:Concept {name:'tensorflow'})--(b:Concept) WHERE b.weight > 6 RETURN b.name AS name"
# neighbors = [x['name'] for x in graph.run(query).data()]

# query = "MATCH (a:Concept)-[r:HAS]->(b:Concept) " \
#     "WHERE a.name IN $names AND b.name IN $names " \
#     "RETURN a.name AS from, b.name AS to, " \
#     "a.weight AS from_weight, b.weight AS to_weight, r.weight AS edge_weight"
# data = graph.run(query, names=neighbors+['tensorflow',]).data()
# # print(data)

# df = pd.DataFrame(data=data)
# print(df)
# df.to_csv('../samples/graphs/sample-graph_2.csv')

if args.delete:
    graph.run('MATCH (p) DETACH DELETE p')
    print("All nodes deleted successfully!")