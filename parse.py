from textrank import extract_top_terms

import json

with open('sample4.txt', 'r', encoding='utf-8') as f:
    text = f.read().lower()

with open('lib/common.txt', 'r') as f:
    common_words = []
    for line in f:
        if line != '':
            common_words.append(line.replace('\n', ''))

with open('lib/plural_to_singular.json', 'r') as f:
    plural_to_singular = json.load(f)

# print(common_words)
# print(plural_to_singular)
terms = extract_top_terms(text, common_words=common_words, plural_to_singular=plural_to_singular)
print(terms)