from py2neo import Graph
import pandas as pd
import networkx as nx

class GraphSearch(object):
    def __init__(self, neo4j_url='bolt://localhost:7687', **kwargs):
        self.graph = Graph(neo4j_url, password=kwargs['password'])

    def exists(self, query):
        node_name = query.replace(' ', '-')
        data = self.graph.run('MATCH (n:Concept {name: $name}) RETURN n', name=node_name).data()
        return len(data) > 0

    def get_result(self, query):
        """
        Get networkx representation of query results
        args:
            query: entity id, multi-word phrase must be joined by hyphens
        returns:
            networkx digraph
        """
        node_name = query.replace(' ', '-')

        if not self.exists(node_name):
            print(f'{node_name} not in graph')
            return

        # Get query region
        edges, neighbors = self.get_region(node_name)

        # Get scores from global graph
        scores = self.get_scores()

        # Get region scores
        score_sum = sum([scores[node] for node in neighbors])
        neighbor_scores = {}
        for node in neighbors:
            neighbor_scores[node] = scores[node] / score_sum

        gr = nx.DiGraph()
        for node in neighbors:
            # Normalize score based on query
            gr.add_node(node, weight=neighbor_scores[node] / neighbor_scores[node_name])
            
        for edge in edges:
            gr.add_edge(edge['from'], edge['to'])

        return gr

    def get_neighbors(self, concept_name, weight_threshold=0):
        """
        Get neighbors of concept
        args:
            concept_name: name of node
            weight_threshold: only nodes with weight >= this value 
                will be returned
        returns:
            list of node names
        """

        query = "MATCH (a:Concept {name:$concept_name})--(b:Concept) " \
            "WHERE b.weight >= $threshold RETURN DISTINCT b.name AS name"
        response = self.graph.run(query, concept_name=concept_name, threshold=weight_threshold)
        neighbors = [x['name'] for x in response.data()]
        return neighbors

    def get_region(self, concept_name, weight_threshold=0):
        """
        Get all nodes/edges within one degree of freedom from concept
        args:
            concept_name: name of node
            weight_threshold: only nodes with weight >= this value 
                will be returned
        returns:
            list of (from, to, from_weight, to_weight, edge_weight) dicts
        """

        names = self.get_neighbors(concept_name, weight_threshold) + [concept_name,]
        query = "MATCH (a:Concept)-[r:HAS]->(b:Concept) " \
            "WHERE a.name IN $names AND b.name IN $names " \
            "RETURN a.name AS from, b.name AS to, " \
            "a.weight AS from_weight, b.weight AS to_weight, r.weight AS edge_weight"
        data = self.graph.run(query, names=names).data()
        return data, names

    def get_globe(self, weight_threshold=0):
        """Get all edges in the graph database
        """
        query = "MATCH (a:Concept)-[r:HAS]->(b:Concept) " \
            "RETURN a.name AS from, b.name AS to, " \
            "a.weight AS from_weight, b.weight AS to_weight, r.weight AS edge_weight"
        data = self.graph.run(query).data()
        return data

    def get_scores(self, concept_name=None, weight_threshold=0):
        """Get sorted region concepts
        """
        if concept_name is None:
            data = self.get_globe(weight_threshold)
        else:
            data = self.get_region(concept_name, weight_threshold)

        gr = _get_networkx(data)
        scores = nx.pagerank(gr, weight='weight')
        # sorted_concepts = sorted(scores, key=scores.get, reverse=True)

        # data = []
        # for c in sorted_concepts:
        #     data.append({'name':c, 'prob':scores[c]})

        return scores

def _get_networkx(data):
    """
    Construct networkx directed graph from data list
    """
    gr = nx.DiGraph()
    for e in data:
        if e['from'] not in gr.nodes:
            gr.add_node(e['from'])
        if e['to'] not in gr.nodes:
            gr.add_node(e['to'])

        # score = e['from_weight'] / e['edge_weight']
        # Switch to and from nodes
        # Graph contains 'has' relationships
        # PageRank contains redirect connections
        gr.add_edge(e['to'], e['from'], weight=e['edge_weight'])
    
    return gr