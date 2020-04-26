from py2neo import Graph

public_ip = '99.111.153.200'
graph = Graph(f'bolt://{public_ip}:7687', password='pswd')

try:
    print(graph.run("MATCH (n) RETURN n LIMIT 1").data())
    print('ok')
except Exception:
    print('not ok')