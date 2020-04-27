from bokeh.resources import CDN
from bokeh.embed import file_html, components
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
from flask import Flask, request, render_template, abort, Response, Markup
from concept_query import GraphSearch
import time

client = GraphSearch()
start = time.time()
app = Flask(__name__)

@app.route('/')
def index():
	if request.method == 'GET':
		return render_template('application.html')

# @app.route('/reset', methods = ['GET','POST'])
# def reset():
# 	if request.method == 'POST':
# 		return render_template('application.html')

@app.route('/query', methods = ['GET','POST'])
def application(query):
	if request.method == 'GET':	
		gr = client.get_result(query)
		new_nodes = list(gr.nodes())
		new_weights = list(gr.nodes[name]['weight'] for name in gr.nodes) 
		new_edges = list(gr.edges())

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
		graph.node_renderer.data_source.data['color'] = ['red' if x == query else 'green' for x in list(G.nodes())]

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
		url = "http://127.0.0.1:5000/@concept"
		taptool = plot.select(type=TapTool)
		taptool.callback = OpenURL(url=url) #callback on url
		plot.renderers.append(graph)

		#return Markup(file_html(plot, CDN, "my plot"))
		plot_script, plot_div = components(plot)
		kwargs = {'plot_script': plot_script, 'plot_div': plot_div}
		kwargs['title'] = 'plot'

		return render_template('application.html', **kwargs)
		abort(404)
		abort(Response('Hello'))
		
	elif request.method == 'POST':
		if 'search_path' in request.form:
			query = request.form['search_path']
			application(query)
		
if __name__ == '__main__':
    app.run(debug=True)