import get_links
from parse import Parser

import scrapy
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

class TestSpider(scrapy.Spider):
    name = "test"

    start_urls = get_links.get_query_links()

    def __init__(self):
        super()
        self.parser = Parser()
        self.counter = 1

    def parse(self, response):
        print(response.url)
        # filename = response.url.split("/")[-1] + '.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)

        paragraphs = response.xpath('//p/text()').extract()
        # Initialize parser with terms
        self.parser.extract_terms('\n'.join(paragraphs))
        print(self.parser.terms)

        print('Building document heirarchy...')
        headings = []
        _extract_headings(response, headings)
        # print(headings)

        # Exit function if no headers
        if len(headings) == 0:
            return        
        
        tokenized_headings = []
        for tag, text in headings:
            extracted_terms = self.parser.extract_heading_terms(text)
            if len(extracted_terms) > 0:
                tokenized_headings.append( (tag,  extracted_terms) )
        print(tokenized_headings)

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

        # print(trees)
        idx = np.argmax([len(gr.nodes) for gr in trees])
        filepath = f'images/{self.counter}.png'
        _plot_tree(trees[idx], heading_levels[idx], savepath=filepath)
        
        with open('images.txt', 'a', encoding='utf-8') as f:
            f.write(response.url + '\n')

        self.counter += 1

def _extract_headings(response, headers=[],
                    heading_tags=[f'h{i}' for i in range(1,7)]):
    """
    generates list of headers in the dom
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

        if tag in heading_tags:
            text = child.xpath('.//text()')
            # print(tag, ' '.join(child.xpath('.//text()').extract()))
            # print()
            # print('match', child, )
            if len(text) > 0:
                headers.append( (int(tag[1]), ' '.join(text.extract())) )
        else:
            _extract_headings(child, headers, heading_tags)

def _plot_tree(gr, heading_level={}, n_levels=6, savepath=None):
    """
    Plots word heirarchy as a tree
    args:
        gr: graph
        heading_level: dict of (word, tag) pairs
        n_levels: total number of heading levels
        savepath: file path to save drawing
    """
    print(gr.nodes)
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