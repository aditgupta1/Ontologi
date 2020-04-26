import networkx as nx
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
from bokeh.models import Circle, HoverTool, TapTool, BoxSelectTool, OpenURL
from bokeh.models.graphs import from_networkx
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral8
from math import log
import csv
from csv import reader
import pickle

with open('tensorflow-networkx', 'rb') as f:
    gr = pickle.load(f)

new_nodes = list(gr.nodes())
new_weights = list(gr.nodes[name]['weight'] for name in gr.nodes) 
new_edges = list(gr.edges())
root = 'tensorflow'

G = nx.Graph()
G.add_nodes_from(new_nodes,color= 'blue')  #add all weights
G.add_edges_from(new_edges) #add all edges

plot = figure(x_range=(-1, 1), y_range=(-1, 1))

plot.add_tools(HoverTool(tooltips=[("Concept", "@concept"), 
                                   ("degree", "@degree")]), 
               TapTool(), 
               BoxSelectTool())


graph = from_networkx(G, nx.spring_layout, iterations=15, scale=1, center=(0,0))

graph.node_renderer.data_source.data['concept'] = list(G.nodes())

graph.node_renderer.data_source.data['degree'] = list(v for k,v in G.degree())

graph.node_renderer.data_source.data['size'] = list(6*v for v in new_weights) #size of node (current six times the weight provided)

#if we just want two colors use this 
graph.node_renderer.data_source.data['color'] = ['red' if x == root else 'green' for x in list(G.nodes())]

#if we want to add edge width differences based on weight, use: https://stackoverflow.com/questions/49136867/networkx-plotting-in-bokeh-how-to-set-edge-width-based-on-graph-edge-weight

# set node size
from bokeh.transform import linear_cmap
graph.node_renderer.glyph = Circle(
    size='size', 
    fill_color = 'color'
    #use the below if we want multiple colors
    #fill_color=linear_cmap('degree', 'Spectral8', 0, 100)
)

#url that you want to redirect. Currently take you to google search with @concept
url = "https://www.google.com/search?q=@concept&oq=@concept+&aqs=chrome..69i57j46j0l3j46j0.2127j0j1&sourceid=chrome&ie=UTF-8"
taptool = plot.select(type=TapTool)
taptool.callback = OpenURL(url=url) #callback on url

plot.renderers.append(graph)
show(plot)
