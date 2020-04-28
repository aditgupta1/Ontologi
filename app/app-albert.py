from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.plotting import figure
from bokeh.models import Circle, HoverTool, TapTool, BoxSelectTool, OpenURL
from bokeh.models.graphs import from_networkx
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral8

import networkx as nx
from flask import Flask, request, render_template, Response, Markup, jsonify
from concept_query import GraphSearch
import json

client = GraphSearch()
app = Flask(__name__)

URL = 'http://127.0.0.1:1001'

@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        if 'search_path' in request.form:
            query = request.form['search_path']
            print('27>', query)
            return render_template('testd3.html', query_name=query)

    return render_template('testd3.html', query_name='tensorflow')

@app.route('/data/<query>')
def get_data(query):
    # with open('static/data/miserables.json', 'r') as f:
    #     data = json.load(f11)
    # query = 'tensorflow'
    gr = client.get_result(query, prune=True)
    # print('35>', gr.nodes)

    data = {}
    data['nodes'] = []
    data['links'] = []

    for node, attr in gr.nodes(data=True):
        data['nodes'].append({'id' : node, 'group': 1, 'score' : attr['weight']})

    # print(data['nodes'])
    for source, target, attr in gr.edges(data=True):
        data['links'].append({'source' : source, 'target' : target, 'value' : attr['weight']})

    return jsonify(data)
		
if __name__ == '__main__':
    app.run(debug=True, port=1001)