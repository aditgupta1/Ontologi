from ..db import GraphDB

# from py2neo import Graph
import pandas as pd
import networkx as nx

class GraphSearch(object):
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, neo4j_encrypted):
        # self.graph = Graph(neo4j_url, password=kwargs['password'])
        self.graph = GraphDB(uri=neo4j_uri, user=neo4j_user, 
            password=neo4j_password, encrypted=neo4j_encrypted)

    @classmethod
    def fromconfig(cls, config):
        """
        Instantiate GraphSearch from neo4j config object
        """
        return cls(config['URI'], config['USER'], config['PASSWORD'], config['ENCRYPTED'])

    def exists(self, query):
        node_name = query.replace(' ', '-')
        data = self.graph.run('MATCH (n:Concept {name: $name}) RETURN n', name=node_name).data()
        return len(data) > 0

    def get_result(self, *query, prune=False):
        """
        Get networkx representation of query results
        args:
            query: entity id, multi-word phrase must be joined by hyphens
                or list if entity ids
        returns:
            networkx digraph
        """
        node_names = []
        for q in query:
            name = q.replace(' ', '-')
            if self.exists(name):
                node_names.append(name)
            else:
                print(f'{name} not in graph')

        if len(node_names) == 0:
            print('No concepts found')
            return nx.DiGraph()

        # Get query region
        edges, neighbors = self.get_region(*node_names)

        # Get scores from global graph
        scores = self.get_scores()

        # Get region scores
        score_sum = sum([scores[node] for node in neighbors])
        neighbor_scores = {}
        for node in neighbors:
            neighbor_scores[node] = scores[node] / score_sum

        gr = nx.DiGraph()
        for node in neighbors:
            # Normalize score based on first concept in query
            gr.add_node(node, weight=neighbor_scores[node] / neighbor_scores[node_names[0]])
            
        for edge in edges:
            gr.add_edge(edge['from'], edge['to'], weight=edge['edge_weight'])

        if prune:
            gr = _prune_graph(gr, query)

        return gr

    def get_neighbors(self, *concept_names):
        """
        Get neighbors of concept
        args:
            concept_name: name of node
        returns:
            list of node names
        """

        neighbors_list = []
        for name in concept_names:
            query = "MATCH (a:Concept {name:$name})--(b:Concept) " \
                "RETURN DISTINCT b.name AS name"
            response = self.graph.run(query, name=name)
            neighbors = set([x['name'] for x in response.data()])
            neighbors_list.append(neighbors)

        intersection = neighbors_list[0].intersection(*neighbors_list[1:])
        return list(intersection)

    def get_region(self, *concept_names):
        """
        Get all nodes/edges within one degree of freedom from concept
        args:
            concept_name: name of node, or list of names
        returns:
            list of (from, to, from_weight, to_weight, edge_weight) dicts
        """

        names = self.get_neighbors(*concept_names) + list(concept_names)
        query = "MATCH (a:Concept)-[r:HAS]->(b:Concept) " \
            "WHERE a.name IN $names AND b.name IN $names " \
            "RETURN a.name AS from, b.name AS to, " \
            "a.weight AS from_weight, b.weight AS to_weight, r.weight AS edge_weight"
        data = self.graph.run(query, names=names).data()
        return data, names

    def get_globe(self):
        """Get all edges in the graph database
        """
        query = "MATCH (a:Concept)-[r:HAS]->(b:Concept) " \
            "RETURN a.name AS from, b.name AS to, " \
            "a.weight AS from_weight, b.weight AS to_weight, r.weight AS edge_weight"
        data = self.graph.run(query).data()
        return data

    def get_scores(self, concept_name=None):
        """Get sorted region concepts
        """
        if concept_name is None:
            data = self.get_globe()
        else:
            data = self.get_region(concept_name)

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

def _prune_graph(gr, query):
    """
    Remove all nodes that don't have any outbound nodes
    Unless the node is original query"""

    G = gr
    continue_pruning = True
    step = 1

    while continue_pruning:
        any_inbound_only = False
        
        # Get nodes
        display_nodes = []
        for node in G.nodes:
            if G.out_degree(node) > 0 or node == query:
                display_nodes.append(node)
            else:
                any_inbound_only = True

        # Get edges
        display_edges = []
        for u,v,attr in G.edges(data=True):
            if u in display_nodes and v in display_nodes:
                display_edges.append((u,v,attr))
                
        G_new = nx.DiGraph()
        for node in display_nodes:
            G_new.add_node(node, weight=G.nodes[node]['weight'])
        G_new.add_edges_from(display_edges)
        
        continue_pruning = any_inbound_only
        G = G_new
        
        # print('Step:', step)
        step += 1
        
    return G