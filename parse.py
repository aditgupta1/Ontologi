from textrank import extract_top_terms, get_word_list

import nltk
import json

class Parser(object):
    def __init__(self):
        self.terms = None
        self.max_compound_len = 1

        with open('lib/common.txt', 'r') as f:
            common_words = []
            for line in f:
                if line != '':
                    common_words.append(line.replace('\n', ''))

        stopwords = nltk.corpus.stopwords.words('english')
        self.skipwords = stopwords + common_words

        with open('lib/plural_to_singular.json', 'r') as f:
            self.plural_to_singular = json.load(f)

    def extract_terms(self, text, ratio=0.33):
        """
        Extracts keywords/phrases given string text
        args:
            text: string
            ratio: fraction of all terms to return
        returns:
            list of top terms
        """
        self.terms = extract_top_terms(text, skipwords=self.skipwords, 
                                plural_to_singular=self.plural_to_singular, 
                                ratio=ratio)
        self.max_compound_len = max([len(x) for x in self.terms] + [1,])
        print('Top terms extracted successfully!')

        return self.terms

    def extract_heading_terms(self, heading):
        """
        extracts terms from header
        if terms were not extracted beforehand, all non-skipwords will be returned
        args:
            header: string
        returns:
            list of unique terms
        """
        word_tokens = get_word_list(heading.lower(), skipwords=self.skipwords, 
                                plural_to_singular=self.plural_to_singular)
        # print(word_tokens)

        if self.terms is None:
            # Remove duplicates
            return list(set(word_tokens))

        word_list = []
        term_set = set(self.terms)
        i = 0
        while i < len(word_tokens):
            l = self.max_compound_len
            while l > 1:
                word = ' '.join(word_tokens[i:i+l])
                if i <= len(word_tokens) - l and word in term_set:
                    word_list.append(word)
                    i += l
                    break
                l -= 1

            if l == 1:
                if word_tokens[i] in term_set:
                    word_list.append(word_tokens[i])
                i += 1

        # print(word_list)
        return list(set(word_list))

if __name__ == '__main__':
    with open('samples/sample.txt', 'r') as f:
        text = f.read().lower()

    parser = Parser()

    # print(common_words)
    # print(plural_to_singular)
    print(parser.extract_terms(text))