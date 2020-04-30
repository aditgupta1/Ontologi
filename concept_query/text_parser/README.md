# Text Parser

## Setup

Install language model:

```
python -m spacy download en_core_web_sm
```

https://spacy.io/usage/models

## Keyterm Extraction Process

Entity recognition:
- Get all (singular, plural) noun pairs from English corpus using WordNet
- POS tag all words and singularize all nouns while maintaining case (for Named Entity Recognition)
- Identify entities (ignore case when creating unique set but preserve case for final set) using local information
- Identify abbreviations (CNN = Convolutional Neural Network) using dependency structure (appositional clauses)

Phrases ("deep learning"): global information
- Tokenize
- Find frequency and co-occurrence
- Rank n-gram phrases using normalized score
- Get top 10%

Construct Graph:
- Update token corpus with entities and phrases
- Tokenize text and sentences
- Get dependency information for each sentence
- Edge from subject to object, ignoring predicates

Run TextRank to get most important terms
