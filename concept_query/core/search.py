from ..db import GraphDB

# from py2neo import Graph
import pandas as pd
import networkx as nx

class GraphSearch(object):
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, neo4j_encrypted):
        # self.graph = Graph(neo4j_url, password=kwargs['password'])
        self.graph = GraphDB(uri=neo4j_uri, user=neo4j_user, 
            password=neo4j_password, encrypted=neo4j_encrypted)
        self.global_scores = self.get_scores()

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

    def get_result(self, *query, prune=False, n_nodes=50, use_cache=False):
        """
        Get networkx representation of query results
        args:
            query: entity id, multi-word phrase must be joined by hyphens
                or list if entity ids
            prune: if true, repeately prune nodes that don't have outbound edges
            n_nodes: number of nodes to return
                if multiple query concepts, the result must contain all of them
                so potentially there may be more than n_nodes
                the graph is also pruned, so there may be less than n_nodes
            use_cache: if true, use cached glocal scores
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
        if not use_cache:
            self.global_scores = self.get_scores()

        # Get region scores
        score_sum = sum([self.global_scores[node] for node in neighbors])
        neighbor_scores = {}
        for node in neighbors:
            neighbor_scores[node] = self.global_scores[node] / score_sum

        # Get only a portion of the results
        display_nodes = _slice_nodes(neighbor_scores, node_names, n_nodes)

        gr = nx.DiGraph()
        for node in display_nodes:
            # Normalize score based on first concept in query
            norm_score = neighbor_scores[node] / neighbor_scores[node_names[0]]
            gr.add_node(node, weight=norm_score)
            
        for edge in edges:
            if edge['from'] in display_nodes and edge['to'] in display_nodes:
                gr.add_edge(edge['from'], edge['to'], weight=edge['edge_weight'])

        if prune:
            gr = _prune_graph(gr, node_names)

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

    def refresh_global(self):
        self.global_scores = self.get_scores()

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

def _prune_graph(gr, keep_nodes):
    """
    Remove all nodes that don't have any outbound nodes
    Unless the node is in keep_nodes"""

    G = gr
    continue_pruning = True
    step = 1

    while continue_pruning:
        any_inbound_only = False
        
        # Get nodes
        display_nodes = []
        for node in G.nodes:
            if G.out_degree(node) > 0 or node in keep_nodes:
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

def _slice_nodes(neighbor_scores, keep_nodes, n_nodes):
    """
    Get higher-scored and lower-scored nodes neighbors
    With at max n_nodes
    """
    if len(neighbor_scores) <= n_nodes:
        return neighbor_scores.keys()

    sorted_neighbors = sorted(neighbor_scores, key=neighbor_scores.get, reverse=True)
    search_node_indeces = [sorted_neighbors.index(node) for node in keep_nodes]
    min_idx = min(search_node_indeces)
    max_idx = max(search_node_indeces)

    display_nodes = sorted_neighbors[min_idx:max_idx+1]
    min_counter = min_idx-1
    max_counter = max_idx + 1
    while len(display_nodes) < n_nodes:
        if min_counter >= 0:
            display_nodes.insert(0, sorted_neighbors[min_counter])
            min_counter -= 1
        if max_counter < len(sorted_neighbors):
            display_nodes.append(sorted_neighbors[max_counter])
            max_counter += 1

    return display_nodes