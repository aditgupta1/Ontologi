from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.plotting import figure
from bokeh.models import Circle, HoverTool, TapTool, BoxSelectTool, OpenURL
from bokeh.models.graphs import from_networkx
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral8

from flask import Flask, request, render_template, Response, Markup, jsonify
import networkx as nx
import json
import spacy
import toml

from concept_query import GraphSearch, GoogleSearch
from concept_query.db import SqlDB

app = Flask(__name__)
URL = 'http://127.0.0.1:1001'

config = toml.load('../config.toml')
client = GraphSearch.fromconfig(config['NEO4J_CLOUD'])
g = GoogleSearch()
sql = SqlDB.fromconfig(config['SQL_CLOUD'])

"""
Search bar parser
For more info about spacy entity recognition:
    concept_query/text_parser/textrank.py:extract_top_terms
    https://spacy.io/usage/rule-based-matching#entityruler
"""
nlp = spacy.load("en_core_web_sm")
ruler = spacy.pipeline.EntityRuler(nlp)

sql_response = sql.execute('select PATTERN, ENT, FREQ from PATTERNS')
entity_patterns = []
entities = {} # Common patterns for each entity id
for pattern, ent_id, freq in sql_response:
    entity_patterns.append({'label':'CUSTOM', 'pattern':pattern, 'id':ent_id})
    
    # Get frequencies for each pattern
    if ent_id in entities.keys():
        entities[ent_id][pattern] = freq
    else:
        entities[ent_id] = {pattern : freq}

other_pipes = [p for p in nlp.pipe_names if p != "tagger"]
with nlp.disable_pipes(*other_pipes):
    ruler.add_patterns(entity_patterns)
nlp.add_pipe(ruler, before='ner')

@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        if 'search_path' in request.form:
            text = request.form['search_path'].replace('-', ' ')
            concepts = parse(nlp, text)
            print('58>', concepts)
            
            if len(concepts) > 0:
                query = concepts[0]
                link_data = g.search(query, full=True)
                print('27>', query)
                return render_template('testd3-adit.html', 
                    query_name=query, links = link_data, concepts=concepts)

    return render_template('testd3-adit.html', query_name='tensorflow', 
        links = g.search('tensorflow', full=True), concepts=[])

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
        data['links'].append({
            'source' : source, 
            'target' : target, 
            'value' : attr['weight']
        })

    return jsonify(data)

def parse(nlp, text):
    """Get concepts from text"""
    doc = nlp(text)

    # Retokenize
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    
    # Get nouns and entities
    concepts = []
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN', 'X'] and len(token.text) > 1:
            if token.ent_id_ != '':
                noun = token.ent_id_
            else:
                noun = token.lemma_
        concepts.append(noun)

    return concepts
        
if __name__ == '__main__':
    app.run(debug=True, port=1001)