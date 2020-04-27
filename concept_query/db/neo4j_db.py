from neo4j import GraphDatabase

class GraphDB(object):
    def __init__(self, uri='bolt://34.74.158.108:7687', 
                user='neo4j', password='password'):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query, **kwargs):
        def _run(tx, **kwargs):
            response = tx.run(query, **kwargs)
            return response

        with self.driver.session() as session:
            response = session.write_transaction(_run, **kwargs)
        
        # print(response)
        # data = [dict(x) for x in response]
        return response

    def delete_table(self):
        self.run('MATCH (p) DETACH DELETE p')
        print('Graph deleted successfully!')

if __name__ == '__main__':
    graph = GraphDB()

    # query = 'MATCH (a:Concept {name: "tensorflow"}) ' \
    #     'MATCH (b:Concept {name: "python"}) ' \
    #     "MERGE (a)-[r:HAS]->(b) " \
    #     "ON CREATE SET r.weight = 1 " \
    #     "ON MATCH SET r.weight = r.weight + 1"

    # edges = [['tensorflow','python'], ['tensorflow', 'machine-learning']]

    # query = 'UNWIND $edges AS edge ' \
    #     'MATCH (a:Concept {name: edge[0]}) ' \
    #     'MATCH (b:Concept {name: edge[1]}) ' \
    #     "MERGE (a)-[r:HAS]->(b) " \
    #     "ON CREATE SET r.weight = 1, r.timestamp = $timestamp " \
    #     "ON MATCH SET r.weight = r.weight + 1"
    # print(graph.run(query, edges=edges, timestamp=1))

    print(graph.run('MATCH (n) RETURN n.name AS name LIMIT 10').data())
    graph.close()