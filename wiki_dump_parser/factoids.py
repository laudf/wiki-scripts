import pandas as pd
import numpy as np
import nltk

def generate_factoids(edit_content):
    '''
    Generate the factoids in a page revision:
    *A link to another page is a factoid.
    *A word declared as an NNP by the NLTK pos tagger is a factoid.
    '''
    text = str(edit_content)
    tokens = nltk.word_tokenize(text)
    parts_of_speech = nltk.pos_tag(tokens)
    factoids = set([y[0] for y in parts_of_speech if str(y[1]) == 'NNP'])
    factoid_str = ''
    while factoids:
        elem = factoids.pop()
        factoid_str = factoid_str + elem + ','

    return factoid_str[:-1]