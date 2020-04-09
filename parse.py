from textrank import extract_top_terms

with open('sample.txt', 'r') as f:
    text = f.read().lower()

terms = extract_top_terms(text)
print(terms)