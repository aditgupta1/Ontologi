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
g = GoogleSearch(engine='google')
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

# Get most common pattern for each id
common_pattern = {}
for ent_id in entities.keys():
    sorted_patterns = sorted(entities[ent_id], key=entities[ent_id].get, reverse=True)
    common_pattern[ent_id] = sorted_patterns[0]

@app.route('/', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        if 'search_path' in request.form:
            search_text = request.form['search_path']
            print('63>', search_text)
            concepts = parse(nlp, search_text)
            print('58>', concepts)
            
            if len(concepts) > 0:
                query = ';'.join(concepts)
                link_data = g.search(search_text, full=True, n_results=15)
                print('27>', query)
                return render_template('testd3-adit.html', 
                    query_name=query, links = link_data, concepts=[commonize(x) for x in concepts],
                    search_text=search_text)

    # return render_template('testd3-adit.html', query_name='tensorflow', 
    #     links = g.search('tensorflow', full=True, n_results=15), concepts=[])
    return render_template('testd3-adit.html', query_name='', links=[], concepts=[])

@app.route('/data/<query>')
def get_data(query):
    # with open('static/data/miserables.json', 'r') as f:
    #     data = json.load(f11)
    # query = 'tensorflow'
    concept_names = query.split(';')
    gr = client.get_result(*concept_names, prune=True, use_cache=True)
    # print('35>', gr.nodes)

    data = {}
    data['nodes'] = []
    data['links'] = []

    for node, attr in gr.nodes(data=True):
        data['nodes'].append({
            'id' : node, 
            'group': 1 if node in concept_names else 0, 
            'score' : round(attr['weight'], 2),
            'pattern' : commonize(node)
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
    doc = nlp(text.strip())

    # Retokenize
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    
    # Get nouns and entities
    concepts = []
    for token in doc:
        print(token, token.pos_)
        if token.ent_id_ != '':
            concepts.append(token.ent_id_)
        elif token.pos_ in ['NOUN', 'PROPN', 'X'] and len(token.text) > 1:
            concepts.append(token.lemma_)

    return concepts

def commonize(concept):
    if concept in common_pattern.keys():
        return common_pattern[concept]
    return concept
        
if __name__ == '__main__':
    app.run(debug=True, port=1001)