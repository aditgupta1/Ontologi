from concept_query.text_parser import Parser
from concept_query.db import SqlDB #, DynamoDB
from concept_query.utils import TaskQueue

import os
import scrapy
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import boto3
import time
import json

class PageGraphSpider(scrapy.Spider):
    name = "page_graph"

    def __init__(self, *args, **kwargs):
        """
        kwargs:
            url_path: path to list of urls to scrape
            dynamodb_region_name: region name
            dynamodb_uri: endpoint url
            save_name: (optional) spider name to save graphs and urls
            sql_path: path to sql database
            task_queue_path: path to task queue sql database
        """
        
        super().__init__(*args, **kwargs)
        self.parser = Parser()
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

        '''Get starting url'''
        with open(kwargs['url_path'], 'r') as f:
            start_urls = f.readlines()
        self.start_urls = [x.strip('\n') for x in start_urls]

        # self.task_queue = TaskQueue(kwargs['task_queue_path'])
        # print('48>', self.task_queue.select())

        # if self.task_queue.is_empty():
        #     self.start_urls = []
        # else:
        #     self.task_id, url = self.task_queue.peek()
        #     self.start_urls = [url,]

        print('page_graph:54>start urls', self.start_urls)

        '''Save results'''
        if 'save_name' in kwargs.keys():
            # Create test results folder
            self.save_dir = f'../test_results/{kwargs["save_name"]}'
            os.makedirs(os.path.join(self.save_dir, 'page_graphs'), exist_ok=True)
        else:
            self.save_dir = None

        '''Database'''
        # Connect database to get entity patterns
        # self.db = DynamoDB(region_name=kwargs['dynamodb_region_name'],
        #     endpoint_url=kwargs['dynamodb_uri'])
        # self.table = self.db.get_patterns_table()

        sql_config = json.loads(kwargs['sql_config'])
        print('73>', sql_config)
        self.sql = SqlDB.fromconfig(sql_config)
        self.last_read = 0
        # Store parameters for pipeline initialization
        self.kwargs = kwargs
        self.kwargs['sql_config'] = sql_config

    # def parse(self, response):
    #     try:
    #         yield self._parse(response)
    #     except:
    #         print('ERROR')
    #         pass

    #     self.task_queue.update_completed(self.task_id)

    #     '''Get next task'''
    #     # End spider if no more URLs to process 
    #     if self.task_queue.is_empty():
    #         return None

    #     self.task_id, url = self.task_queue.peek()
    #     yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        print('page_graph:49>', response.url)

        # Update task status to working
        # print('page_graph:77>', self.task_id)
        # self.task_queue.update_working(self.task_id)

        # print('page_graph:80>', self.task_queue.select())

        # Get paragraph text
        paragraphs = response.xpath('//p//text()').extract()
        body_text = ' '.join(paragraphs).replace('\n', ' ')

        start = time.time()

        # Initialize parser with terms
        # Only get patterns from database (since last read)
        tmp = self.last_read
        self.last_read = int(time.time())
        db_response = self.sql.execute('SELECT * FROM PATTERNS WHERE TIMESTAMP >= ?', (tmp,))
        print('page_graph:65>read database', time.time() - start)

        patterns = []
        for it in db_response:
            # (id, pattern, ent, timestamp)
            patterns.append({'label':'CUSTOM', 'pattern':it[1], 'id':it[2]})
        print('page_graph:69>', time.time() - start)
        print('page_graph:69> #new patterns', len(patterns))
        
        _, new_patterns, freq_data = self.parser.extract_terms(body_text, patterns=patterns)
        # print(self.parser.terms)
        print('page_graph:72>', time.time() - start)

        # print('Building document heirarchy...')
        headings = []
        _extract_headings(response, headings, self.TAGS)
        # print(headings)

        # Exit function if no headers
        if len(headings) == 0:
            print('page_graph:113> NO HEADINGS')
            if self.save_dir is not None:
                with open(os.path.join(self.save_dir, 'scraped_urls.txt'), 'a', encoding='utf-8') as f:
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

        if self.save_dir is not None:            
            filepath = os.path.join(self.save_dir, f'page_graphs/{self.counter}.png')
            _plot_tree(largest_tree, heading_levels[idx], savepath=filepath)
            
            with open(os.path.join(self.save_dir, 'scraped_urls.txt'), 'a', encoding='utf-8') as f:
                f.write(response.url + ', TRUE\n')

            self.counter += 1

        yield {
            'graph' : _networkx_to_dict(largest_tree),
            'patterns' : new_patterns,
            'url' : response.url,
            'freq_data' : freq_data
        }

        # self.task_queue.update_completed(self.task_id)

        # '''Get next task'''
        # # End spider if no more URLs to process 
        # if self.task_queue.is_empty():
        #     return None

        # self.task_id, url = self.task_queue.peek()
        # yield scrapy.Request(url, callback=self.parse)

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

# def _get_query_links(query='tensorflow', n=10):
# 	# query = input("Enter Your Query: ")

# 	urls = []

# 	for url in search(query, stop=n):
# 		urls.append(url)

# 	return urls

def _networkx_to_dict(gr):
    return {
        'nodes' : list(gr.nodes),
        'edges' : [list(e) for e in gr.edges]
    }