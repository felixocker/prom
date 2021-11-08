#!/usr/bin/env python3
"""some wordnet testing combined w nltk"""
# NOTE: wordnet lemma names are returned with underscores for compound words
# tokenizer may be used to resolve this if required

from nltk.corpus import wordnet as wn

POS = ["n", "v", "a", "r"]

def get_syns(word, word_pos):
    """get synonyms from wordnet"""
    assert word_pos in POS, "invalid POS key"
    synonyms = []
    for elem in wn.synsets(word, pos=word_pos):
        synonyms.extend([lemma.name() for lemma in elem.lemmas()])
    synonyms = list(dict.fromkeys(synonyms))
    return synonyms

def get_ants(word, word_pos):
    """get antonyms from wordnet"""
    assert word_pos in POS, "invalid POS key"
    antonyms = []
    for elem in wn.synsets(word, pos=word_pos):
        for l in elem.lemmas():
            antonyms.extend([ant.name() for ant in l.antonyms()])
    antonyms = list(dict.fromkeys(antonyms))
    return antonyms

def get_hypos(word, word_pos):
    """get hyponyms from wordnet"""
    assert word_pos in POS, "invalid POS key"
    hyponyms = []
    for elem in wn.synsets(word, pos=word_pos):
        for l in elem.lemmas():
            for hype in l.synset().hyponyms():
                hyponyms.extend([lemma.name() for lemma in hype.lemmas()])
    hyponyms = list(dict.fromkeys(hyponyms))
    return hyponyms

def get_hypes(word, word_pos):
    """get hypernyms from wordnet"""
    assert word_pos in POS, "invalid POS key"
    hypernyms = []
    for elem in wn.synsets(word, pos=word_pos):
        for l in elem.lemmas():
            for hype in l.synset().hypernyms():
                hypernyms.extend([lemma.name() for lemma in hype.lemmas()])
    hypernyms = list(dict.fromkeys(hypernyms))
    return hypernyms

def get_derivationally_related_verbs(word, word_pos):
    """get derivationally related verbs for noun, e.g., 'precede' for 'predecessor'"""
    assert word_pos == "n", "invalid POS key"
    drvs = []
    for elem in wn.synsets(word, pos=word_pos):
        for l in elem.lemmas():
            drvs.extend([drf.synset().lemmas()[0].name() for drf in l.derivationally_related_forms() if drf.synset().pos() == "v"])
    drvs = list(dict.fromkeys(drvs))
    return drvs

if __name__ == "__main__":
    word = "predecessor"
    pos = "n"
    funcs = {"synonyms": get_syns,
             "antonyms": get_ants,
             "hyponyms": get_hypos,
             "hypernyms": get_hypes,
             "drvs": get_derivationally_related_verbs}
    for f in funcs.keys():
        elems = funcs[f](word, pos)
        if elems:
            if not f == list(funcs.keys())[0]:
                print("-" * 10)
            print(f + " for " + word + " are:")
            print(*elems, sep="\n")
