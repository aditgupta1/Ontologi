from .textrank_spacy import extract_top_terms

import nltk
import json
import os
import spacy

class Parser(object):
    def __init__(self, lib_path='.'):
        self.terms = None

        gpu = spacy.prefer_gpu()
        if gpu:
            print('GPU activated successfully!')

        self.nlp = spacy.load("en_core_web_sm")
        self.entity_ruler = spacy.pipeline.EntityRuler(self.nlp)
        self.nlp.add_pipe(self.entity_ruler, before='ner')
        self.ruler_patterns_set = set([])

        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        with open(os.path.join(lib_path, 'plural_to_singular.json'), 'r') as f:
            self.plural_to_singular = json.load(f)

    def extract_terms(self, text, patterns=[]):
        """
        Extracts keywords/phrases given string text
        args:
            text: string
            ratio: fraction of all terms to return
        returns:
            list of top terms
        """
        self.terms, self.nlp, self.entity_ruler, self.ruler_patterns_set, new_patterns = \
            extract_top_terms(text, self.nlp, self.entity_ruler,
                            ruler_patterns_set=self.ruler_patterns_set,
                            stopwords=self.stopwords, 
                            plural_to_singular=self.plural_to_singular,
                            patterns=patterns)
        print('Top terms extracted successfully!')

        return self.terms, new_patterns

    def extract_heading_terms(self, text):
        """
        extracts terms from header
        if terms were not extracted beforehand, all non-stopwords will be returned
        args:
            header: string
        returns:
            list of unique terms
        """
        doc = self.nlp(text)

        result = []

        if self.terms is None:
            # Remove duplicates
            for token in doc:
                term = token.text.lower()
                if term not in self.stopwords:
                    result.append(term)
        else:
            term_set = set(self.terms)
            for token in doc:
                term = token.ent_id_ if token.ent_id_ != '' else token.lemma_
                if term in term_set:
                    result.append(term)

        return list(set(result))

if __name__ == '__main__':
    """
    Test parser
    """
    with open('../samples/sample.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    parser = Parser()

    # print(common_words)
    # print(plural_to_singular)
    print(parser.extract_terms(text))