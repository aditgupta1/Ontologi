import networkx as nx
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
from bokeh.models import Circle, HoverTool, TapTool, BoxSelectTool
from bokeh.models.graphs import from_networkx
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral8


import csv
from csv import reader

#output_notebook()

all_nodes = []
with open('sample-graph.csv', 'r', encoding='utf-8-sig') as f:
    rows = csv.reader(f, delimiter=',')
    for row in rows:
        unique_row_items = set(field.strip() for field in row)
        for item in unique_row_items:
            if item not in all_nodes:
                all_nodes.append(item)

with open('sample-graph.csv', 'r', encoding='utf-8-sig') as read_obj:
    csv_reader = reader(read_obj)
    all_edges = list(map(tuple, csv_reader))

G = nx.Graph()
G.add_nodes_from(all_nodes,color= 'blue')  
G.add_edges_from(all_edges)

node_size = {k:5*v for k,v in G.degree()} 
nx.set_node_attributes(G, node_size, 'node_size')
# create the plot
plot = figure(x_range=(-1, 1), y_range=(-1, 1))

plot.add_tools(HoverTool(tooltips=[("Concept", "@concept"), 
                                   ("Degree", "@degree")]), 
               TapTool(), 
               BoxSelectTool())

graph = from_networkx(G, nx.spring_layout, iterations=10, scale=1, center=(0,0))

graph.node_renderer.data_source.data['concept'] = list(G.nodes())

graph.node_renderer.data_source.data['degree'] = list(v for k,v in G.degree())
test = list(v for k,v in G.degree())

#graph.node_renderer.data_source.data['colors'] = Spectral8

#print(graph.node_renderer.data_source.data['degree'])
# set node size
from bokeh.transform import linear_cmap
graph.node_renderer.glyph = Circle(
    size=15, 
    fill_color=linear_cmap('degree', 'Spectral8', 0, 10)
)
plot.renderers.append(graph)
show(plot)

#important link: https://stackoverflow.com/questions/50420584/color-nodes-by-networkx-node-attribute-with-bokeh