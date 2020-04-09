"""Python implementation of the TextRank algoritm.

From this paper:
    https://web.eecs.umich.edu/~mihalcea/papers/mihalcea.emnlp04.pdf

Based on:
    https://gist.github.com/voidfiles/1646117
    https://github.com/davidadamojr/TextRank
"""
import editdistance
import io
import itertools
import networkx as nx
import nltk
import os


def setup_environment():
    """Download required resources."""
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    print('Completed resource downloads.')

def filter_for_tags(tagged, tags=['NN', 'JJ', 'NNP']):
    """Apply syntactic filters based on POS tags."""
    return [item[0] for item in tagged if item[1] in tags]

def build_graph(sentences):
    """Return a networkx graph instance.

    :param nodes: List of sentences
    """

    unique_word_set = set([])
    edges = {}

    for s in sentences:
        # tokenize the text using nltk
        word_tokens = nltk.word_tokenize(s)

        # assign POS tags to the words in the text
        tagged = nltk.pos_tag(word_tokens)
        word_list = filter_for_tags(tagged)
        word_list.sort()

        for word in word_list:
            if word not in unique_word_set:
                unique_word_set.add(word)

        for pair in itertools.combinations(word_list, 2):
            if pair in edges.keys():
                edges[pair] = 1
            else:
                edges[pair] += 1

    gr = nx.Graph()  # initialize an undirected graph
    gr.add_nodes_from(unique_word_set)

    for key, weight in edges.items():
        gr.add_edge(key[0], key[1], weight=weight)

    return gr, unique_word_set


def extract_key_phrases(text):
    """Return a set of key phrases.

    :param text: A string.
    """
    
    # this will be used to determine adjacent words in order to construct
    # keyphrases with two words
    sentences = text.split('. ')
    graph, unique_word_set = build_graph(sentences)

    # pageRank - initial value of 1.0, error tolerance of 0,0001,
    calculated_page_rank = nx.pagerank(graph, weight='weight')
    # print(calculated_page_rank)

    # most important words in ascending order of importance
    all_keyphrases = sorted(calculated_page_rank, key=calculated_page_rank.get,
                        reverse=True)
    for kp in all_keyphrases[:100]:
        print(kp, calculated_page_rank[kp])

    # the number of keyphrases returned will be relative to the size of the
    # text (a third of the number of vertices)
    one_third = len(word_set_list) // 3
    keyphrases = all_keyphrases[0:one_third + 1]

    # take keyphrases with multiple words into consideration as done in the
    # paper - if two words are adjacent in the text and are selected as
    # keywords, join them together
    modified_key_phrases = set([])
    # keeps track of individual keywords that have been joined to form a
    # keyphrase
    dealt_with = set([])
    i = 0
    j = 1
    while j < len(textlist):
        first = textlist[i]
        second = textlist[j]
        if first in keyphrases and second in keyphrases:
            keyphrase = first + ' ' + second
            modified_key_phrases.add(keyphrase)
            dealt_with.add(first)
            dealt_with.add(second)
        else:
            if first in keyphrases and first not in dealt_with:
                modified_key_phrases.add(first)

            # if this is the last word in the text, and it is a keyword, it
            # definitely has no chance of being a keyphrase at this point
            if j == len(textlist) - 1 and second in keyphrases and \
                    second not in dealt_with:
                modified_key_phrases.add(second)

        i = i + 1
        j = j + 1

    return modified_key_phrases, keyphrases

