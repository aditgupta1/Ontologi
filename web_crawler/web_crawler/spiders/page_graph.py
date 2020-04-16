import sys
sys.path.append('.')
sys.path.append('..')

from text_parser import Parser
from ..settings import ENDPOINT_URL

import os
import scrapy
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from googlesearch import search
import boto3

class PageGraphSpider(scrapy.Spider):
    name = "page_graph"

    def __init__(self, category='tensorflow', nstart='10', save='False'):
        super()
        self.parser = Parser(lib_path='../lib')
        self.counter = 1

        self.TAGS = {
            'h1' : 1,
            'h2' : 2,
            'h3' : 3,
            'h4' : 4,
            'h5' : 5,
            'h6' : 6,
            'p' : 7
        }

        self.start_urls = _get_query_links(category, n=int(nstart))

        self.save_results = save.lower() in ['true', '1']

        # Create test results folder
        if self.save_results and not os.path.isdir('../test_results'):
            os.mkdir('../test_results')
            os.mkdir('../test_results/page_graphs')

        # Connect database to get entity patterns
        self.db = boto3.resource('dynamodb', region_name='us-west-2', 
                                endpoint_url=ENDPOINT_URL)
        self.table = self.db.Table('Patterns')

    def parse(self, response):
        print('SPIDER>', response.url)

        paragraphs = response.xpath('//p//text()').extract()
        # Initialize parser with terms
        _, new_patterns = self.parser.extract_terms('\n'.join(paragraphs))
        # print(self.parser.terms)

        # print('Building document heirarchy...')
        headings = []
        _extract_headings(response, headings, self.TAGS)
        # print(headings)

        # Exit function if no headers
        if len(headings) == 0:
            print('NO HEADINGS')
            if self.save_results:
                with open('../test_results/scraped_urls.txt', 'a', encoding='utf-8') as f:
                    f.write(response.url + ', FALSE\n')
                self.counter += 1
            return None
        
        tokenized_headings = []
        for tag, text in headings:
            extracted_terms = self.parser.extract_heading_terms(text)
            if len(extracted_terms) > 0:
                tokenized_headings.append( (tag,  extracted_terms) )
        # print(tokenized_headings)

        trees = []
        heading_levels = []
        gr = nx.DiGraph()
        level = {}

        for i, (tag, terms) in enumerate(tokenized_headings):
            # Find nearest largest heading
            j = i-1
            while j >= 0 and tokenized_headings[j][0] >= tag:
                j -= 1

            if j == -1:
                if i > 0:
                    trees.append(gr)
                    heading_levels.append(level)
                    gr = nx.DiGraph()
                    level = {}
                gr.add_nodes_from(terms)
                
                for word in terms:
                    level[word] = tag
            else:
                # Find terms that are not yet in the graph
                new_terms = []
                for word in terms:
                    if word not in gr.nodes:
                        new_terms.append(word)
                    # Update node if a higher level instance is found
                    if word in gr.nodes and tag < level[word]:
                        gr.remove_node(word)
                        new_terms.append(word)
                gr.add_nodes_from(new_terms)

                for word in new_terms:
                    level[word] = tag

                _, nearest_terms = tokenized_headings[j]
                for a in nearest_terms:
                    for b in new_terms:
                        gr.add_edge(a, b)

        trees.append(gr)
        heading_levels.append(level)

        idx = np.argmax([len(gr.nodes) for gr in trees])
        largest_tree = trees[idx]

        if self.save_results:            
            filepath = f'../test_results/page_graphs/{self.counter}.png'
            _plot_tree(largest_tree, heading_levels[idx], savepath=filepath)
            
            with open('../test_results/scraped_urls.txt', 'a', encoding='utf-8') as f:
                f.write(response.url + ', TRUE\n')

            self.counter += 1

        return {
            'graph' : _networkx_to_dict(largest_tree),
            'patterns' : new_patterns
        }

        # for term in list(largest_tree.nodes):
        #     for url in _get_query_links(term.replace('-', ' ')):
        #         yield scrapy.Request(url, callback=self.parse)

def _extract_headings(response, headers=[], tags={}):
    """
    generates list of headers (+ paragraphs) in the DOM
    args:
        response: scrapy response object
        headers: list
    returns:
        list of (tag #, text) tuples
    """
    
    children = response.xpath('child::*')
    # print(children)

    for child in children:
        tag = child.xpath('name()')[0].extract()
        # print(tag)

        if tag in tags.keys():
            text = child.xpath('.//text()')
            if len(text) > 0:
                headers.append( (tags[tag], ' '.join(text.extract())) )
        else:
            _extract_headings(child, headers, tags)

def _plot_tree(gr, heading_level={}, n_levels=7, savepath=None):
    """
    Plots word heirarchy as a tree
    args:
        gr: graph
        heading_level: dict of (word, tag) pairs
        n_levels: total number of heading levels
        savepath: file path to save drawing
    """
    # print(gr.nodes)
    # Transpose heading level dict
    inverse_heading_level = {}

    for word in heading_level.keys():
        level = heading_level[word]
        if level not in inverse_heading_level.keys():
            inverse_heading_level[level] = []
        inverse_heading_level[level].append(word)

    # explicitly set positions
    pos = {}
    labels = {}
    for level in inverse_heading_level.keys():
        n_words = len(inverse_heading_level[level])
        for i, word in enumerate(inverse_heading_level[level]):
            x_pos = i / n_words
            y_pos = (n_levels - level) / n_levels
            pos[word] = (x_pos, y_pos)
            labels[word] = word

    # print(pos)

    plt.figure(figsize=(20,15))
    nx.draw_networkx_labels(gr, pos, labels, font_size=12)
    nx.draw_networkx_edges(gr, pos, alpha=0.5, width=2)
    plt.axis('off')

    if savepath is None:
        plt.show()
    else:
        plt.savefig(savepath)

def _get_query_links(query='tensorflow', n=10):
	# query = input("Enter Your Query: ")

	urls = []

	for url in search(query, stop=n):
		urls.append(url)

	return urls

def _networkx_to_dict(gr):
    return {
        'nodes' : list(gr.nodes),
        'edges' : list(gr.edges)
    }