from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.plotting import figure
from bokeh.models import Circle, HoverTool, TapTool, BoxSelectTool, OpenURL
from bokeh.models.graphs import from_networkx
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral8

import networkx as nx
from flask import Flask, request, render_template, Response, Markup, jsonify
from concept_query import GraphSearch, GoogleSearch
import json

client = GraphSearch()
g = GoogleSearch()
app = Flask(__name__)

URL = 'http://127.0.0.1:5000'



@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        if 'search_path' in request.form:
            query = request.form['search_path']
            link_data = g.search(query, full=True)
            print('27>', query)
            return render_template('testd3-adit.html', query_name=query, links = link_data)

    return render_template('testd3-adit.html', query_name='tensorflow', links = g.search('tensorflow', full=True))

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
        data['nodes'].append({
            'id' : node, 
            'group': 1 if node == query else 0, 
            'score' : round(attr['weight'], 2)
        })

    # print(data['nodes'])
    for source, target, attr in gr.edges(data=True):
        data['links'].append({'source' : source, 'target' : target, 'value' : attr['weight']})

    return jsonify(data)
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)