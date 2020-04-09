from textrank import extract_key_phrases

with open('sample.txt', 'r') as f:
    text = f.read()

modified_keyphrases, all_keyphrases = extract_key_phrases(text)

print(all_keyphrases[:20])