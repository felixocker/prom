#!/usr/bin/env python3
"""
compare sets of entitites based on labels
assumes that labels in default_lang have already been added
matches have form [elem_type, iri1, iri2, relation, rating]
"""

import itertools
import spacy
import sys
import types
import yaml

import extract_nltk_wordnet as extr
import load_vocab as lv

from collections import defaultdict
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from owlready2 import get_ontology, default_world, World, IRIS, Thing,\
                      ObjectProperty, DatatypeProperty
from spacy.lemmatizer import Lemmatizer
from spacy.matcher import Matcher

NLP = spacy.load("en_core_web_sm")
NLTK_LEMMATIZER = WordNetLemmatizer()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    DEFAULT_LANG = '"' + cfg["settings"]["default-language"] + '"'
    EXPLICIT_RATING = cfg["priors"]["semantic"]["explicit"]
    IMPLICIT_DOMAIN_RATING = cfg["priors"]["semantic"]["domain-specific"]
    IMPLICIT_SYN_RATING = cfg["priors"]["semantic"]["implicit-syn"]
    IMPLICIT_ANT_RATING = cfg["priors"]["semantic"]["implicit-ant"]

def create_query(iri, elem_type):
    """SPARQL query to extract classes, labels, and language tags"""
    query = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX : <""" + iri + """#>
        SELECT DISTINCT ?elem ?label ?language WHERE {
            ?elem a """ + elem_type + """ ; 
                rdfs:label ?label . 
            BIND ( lang(?label) AS ?language ) . 
            FILTER ( ?language = """ + DEFAULT_LANG + """ ) . 
        }
        ORDER BY ?elem"""
    return query

def get_labels(path, iri, elem_type):
    """query onto and return results as list - onto must already be loaded"""
    query = create_query(iri, elem_type)
    my_world = World()
    onto = my_world.get_ontology(path).load()
    graph = my_world.as_rdflib_graph()
    results = list(graph.query(query))
    return results

def analyze_label(elem_iri, label, elem_type):
    """
    split label into parts and analyze
    consists of: [IRI, label, [[text, lemma, pos, tag, dep], ...], passive]
    passive is only set for ops
    """
    label_infos = [elem_iri, label, [], None]
    assert len(label.split()) >= 1, "analyze_label: empty label"
    # nltk tokenizer more reliable if label consists of only one word - use elem_type info
    my_types = {"owl:Class": "n",
                "owl:ObjectProperty": "v",
                "owl:DatatypeProperty": "n"}
    pos = {"owl:Class": "NOUN",
           "owl:ObjectProperty": "VERB",
           "owl:DatatypeProperty": "NOUN"}
    if len(label.split()) == 1:
        if elem_type == "owl:ObjectProperty" and\
           extr.get_syns(str(NLTK_LEMMATIZER.lemmatize(label, "n")), "n") and\
           not extr.get_syns(str(NLTK_LEMMATIZER.lemmatize(label, "v")), "v"):
            label_infos[2].append([label, str(NLTK_LEMMATIZER.lemmatize(label,\
                                   my_types[elem_type])), "NOUN", "XX", "ROOT"])
            label_infos[-1] = True
        else:
            label_infos[2].append([label, str(NLTK_LEMMATIZER.lemmatize(label,\
                                   my_types[elem_type])), pos[elem_type], "XX", "ROOT"])
            if elem_type == "owl:ObjectProperty":
                label_infos[-1] = False
    # use spacy if label consists of more than one word
    elif len(label.split()) > 1:
        doc = NLP(label)
        for token in doc:
            # NOTE: keep only specific POS
            if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV", "ADP", "PROPN", "X"]:
                label_infos[2].append([token.text, token.lemma_, token.pos_, token.tag_, token.dep_])
            # NOTE: these are hard coded exceptions
            if token.pos_ == "PROPN" or token.pos_ == "X" and elem_type in ["owl:Class", "owl:DatatypeProperty"]:
                label_infos[2][-1][2] = "NOUN"
            elif token.pos_ == "X" and elem_type == "owl:ObjectProperty":
                label_infos[2][-1][2] = "VERB"
        if elem_type == "owl:ObjectProperty":
            passive_match = None
            active_reified_match = None
            passive_prop_pattern_1 = [{'DEP':'aux','OP':'*'},{'DEP':'auxpass'},{'TAG':'VBN'}]
            passive_prop_pattern_2 = [{'POS':'VERB'},{'POS':'ADP'}]
            reified_prop_pattern = [{'POS':{'IN':['PROPN','NOUN']}}]
            active_reified_prop_pattern = [{'POS':{'IN':['PROPN','NOUN']}},{'POS':'ADP'}]
            # NOTE: spacy cannot ignore reified labels w _optional_ ADP - have to remove those manually
            matcher = Matcher(NLP.vocab)
            matcher.add("passive_prop", None, passive_prop_pattern_1, passive_prop_pattern_2, reified_prop_pattern)
            passive = matcher(doc)
            for match_id, start, end in passive:
                string_id = NLP.vocab.strings[match_id]
                span = doc[start:end]
                passive_match = span.text
            matcher.remove("passive_prop")
            matcher.add("active_reified_prop", None, active_reified_prop_pattern)
            active = matcher(doc)
            for match_id, start, end in active:
                string_id = NLP.vocab.strings[match_id]
                span = doc[start:end]
                active_reified_match = span.text
            if passive_match and not active_reified_match:
                label_infos[-1] = True
            else:
                label_infos[-1] = False
    return label_infos

def analyze_all_labels(path, iri):
    """get all labels from onto and analyze them"""
    elem_types = ["owl:Class", "owl:ObjectProperty", "owl:DatatypeProperty"]
    # extract all iris with labels
    all_labels = [None, None, None]
    for counter, elem_type in enumerate(elem_types):
        all_labels[counter] = get_labels(path, iri, elem_type)
    # analyze the label for every iri
    all_label_infos = [[], [], []]
    for counter, label_subset in enumerate(all_labels):
        for elem in label_subset:
            all_label_infos[counter].append(analyze_label(elem[0], str(elem[1]).lower(), elem_types[counter]))
    return all_label_infos

def explicit_compare(label_info_1, label_info_2, elem_type):
    """compare two sets of elements based on labels in default_lang and return overlap"""
    explicit_overlap = []
    all_combinations = [(x,y) for x in label_info_1 for y in label_info_2]
    for combination in all_combinations:
        explicit_match = []
        # equivalence
        if len(combination[0][2]) == len(combination[1][2]) and combination[0][-1] == combination[1][-1]:
            if all([elem1[1] in [elem2[1] for elem2 in combination[1][2]] for elem1 in combination[0][2]]):
                explicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  "equivalence", EXPLICIT_RATING]
        # subsumption
        elif len(combination[1][2]) < len(combination[0][2]) and combination[0][-1] == combination[1][-1]:
            if all([elem1[1] in [elem2[1] for elem2 in combination[0][2]] for elem1 in combination[1][2]]):
                explicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  "hyponym", EXPLICIT_RATING]
        elif len(combination[0][2]) < len(combination[1][2]) and combination[0][-1] == combination[1][-1]:
            if all([elem1[1] in [elem2[1] for elem2 in combination[1][2]] for elem1 in combination[0][2]]):
                explicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  "hypernym", EXPLICIT_RATING]
        if explicit_match:
            explicit_overlap.append(explicit_match)
    return explicit_overlap

def append_vocabulary(elems, elem_type, rel):
    """
    create dictionary with words that have relation specified
    :param elems: consists of [IRI, label, [[text, lemma, pos, tag, dep], ...], passive]
    :param elem_type: OP, DP, or class
    """
    funcs = {"syn": extr.get_syns,
             "ant": extr.get_ants,
             "hype": extr.get_hypes,
             "hypo": extr.get_hypos}
    spacy_to_nltk_pos = {"NOUN": "n",
                         "VERB": "v",
                         "ADJ": "a",
                         "ADV": "r",
                         "ADP": "a"}
    try:
        func = funcs[rel]
    except KeyError:
        print("unknown function", rel)
        sys.exit(1)
    vocabulary = defaultdict(list)
    for elem in elems:
        elem_vocab = {"NOUN": [],
                      "VERB": [],
                      "ADJ": [],
                      "ADV": [],
                      "ADP": []}
        if len(elem[2]) < 1:
            raise ValueError("elem must include tokens")
        # increase resilience using elem_type info if there is only one token
        elif len(elem[2]) == 1:
            if elem_type in ["owl:Class", "owl:DatatypeProperty"]:
                elem_vocab["NOUN"].extend([word for word in func(elem[2][0][1], "n")\
                                           if not word in elem_vocab["NOUN"]])
            elif elem_type == "owl:ObjectProperty":
                if extr.get_syns(elem[2][0][1], "n") and not extr.get_syns(elem[2][0][1], "v"):
                    elem_vocab["NOUN"].extend([word for word in func(elem[2][0][1], "n")\
                                               if not word in elem_vocab["NOUN"]])
                else:
                    elem_vocab["VERB"].extend([word for word in func(elem[2][0][1], "v")\
                                               if not word in elem_vocab["VERB"]])
        # more than one token
        else:
            for token in elem[2]:
                if token[2] in elem_vocab.keys():
                    elem_vocab[token[2]].extend([word for word in func(token[1],\
                                                 spacy_to_nltk_pos[token[2]])\
                                                 if not word in elem_vocab[token[2]]])
        vocabulary[str(elem[0])] = elem_vocab
    return vocabulary

def tokens_by_type(token_list, token_pos, token_dep=None):
    """
    :param elems: list of tuples [text, lemma, pos, tag, dep]
    """
    if token_dep:
        return [token[1] for token in token_list if token[2] == token_pos and token[4] == token_dep]
    else:
        return [token[1] for token in token_list if token[2] == token_pos]

def check_xor_label_reification(elem_type, label_1, label_2, passive_equal):
    """
    :param label_x: [uri, label, [token, lemma, POS, TAG, DEP], passive]
    :param passive_equal: boolean; True if both labels should have the same passive value
    """
    if elem_type == "owl:ObjectProperty" and\
       any(tokens_by_type(label_1[2], "NOUN")) and\
       not any(tokens_by_type(label_2[2], "NOUN")) and\
       tokens_by_type(label_2[2], "VERB", "ROOT") and\
       (label_1[-1] == label_2[-1] and passive_equal or\
        label_1[-1] != label_2[-1] and not passive_equal):
        return True
    else:
        return False

def arrange_impl_match(elem_type, elem1, elem2, rel, rating, iter):
    """
    :elem_type, elem1, elem2, rel, rating: info for implicit match
    :iter: indicates if order of elem1 and elem2 should be inverte (yes if 1)
    """
    if iter == 0:
        return [elem_type, elem1, elem2, rel, rating]
    elif iter == 1:
        return [elem_type, elem2, elem1, rel, rating]

def implicit_compare(label_info_1, label_info_2, elem_type):
    """
    check two sets of elements for implicit semantic matches
    :param label_info_x: list of [uri, label, [token, lemma, POS, TAG, DEP], passive]
    :return: list of implicit matches
    """
    rels = {"syn": "equivalence",
            "dis": "disjoint",
            "ant": "inverse",
            "hype": "hypernym",
            "hypo": "hyponym"}
    implicit_overlap = []
    all_combinations = [(x,y) for x in label_info_1 for y in label_info_2]

    syn_dict_1 = dict(append_vocabulary(label_info_1, elem_type, "syn"))
    syn_dict_2 = dict(append_vocabulary(label_info_2, elem_type, "syn"))
    ant_dict_1 = dict(append_vocabulary(label_info_1, elem_type, "ant"))
    ant_dict_2 = dict(append_vocabulary(label_info_2, elem_type, "ant"))
    hype_dict_1 = dict(append_vocabulary(label_info_1, elem_type, "hype"))
    hype_dict_2 = dict(append_vocabulary(label_info_2, elem_type, "hype"))

    for combination in all_combinations:
        implicit_match = []
        dsvocab = lv.csv_to_nested_list()
        if dsvocab:
            # check if entire labels are in same domain synset
            if any([str(combination[0][1]) in synset and str(combination[1][1]) in synset for synset in dsvocab]):
                implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  rels["syn"], IMPLICIT_DOMAIN_RATING]
            # check if entire labels are in different domain synsets
            for synset1, synset2 in itertools.product(dsvocab, dsvocab):
                if synset1 != synset2 and str(combination[0][1]) in synset1 and str(combination[1][1]) in synset2:
                    implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                      rels["dis"], IMPLICIT_DOMAIN_RATING]
        if not implicit_match:
            # equivalent
            # NOTE: there may be limitations due to translation issues, eg, "very very fast car" eq_to "very fast car"
            if all([elem2[1] in syn_dict_1[str(combination[0][0])][elem2[2]] for elem2 in combination[1][2]]) and\
               all([elem1[1] in syn_dict_2[str(combination[1][0])][elem1[2]] for elem1 in combination[0][2]]) and\
               combination[0][-1] == combination[1][-1]:
                implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  rels["syn"], IMPLICIT_SYN_RATING]
            # derivationally related form
            for iter, combo in enumerate(((combination[0], combination[1]), (combination[1], combination[0]))):
                if check_xor_label_reification(elem_type, combo[0], combo[1], True):
                    if tokens_by_type(combo[1][2], "VERB", "ROOT")[0] in\
                    extr.get_derivationally_related_verbs(tokens_by_type(combo[0][2], "NOUN")[0], "n"):
                        implicit_match = arrange_impl_match(elem_type, str(combo[0][0]), str(combo[1][0]),\
                                                            rels["syn"], IMPLICIT_SYN_RATING, iter)
            if implicit_match:
                implicit_overlap.append(implicit_match)
                continue
            # disjoint
            elif elem_type in ["owl:Class", "owl:DatatypeProperty"] and\
               any([elem2[1] in ant_dict_1[str(combination[0][0])][elem2[2]] for elem2 in combination[1][2]]):
                implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  rels["dis"], IMPLICIT_ANT_RATING]
            elif elem_type == "owl:ObjectProperty":
                verbs2 = tokens_by_type(combination[1][2], "VERB", "ROOT")
                adjs2 = tokens_by_type(combination[1][2], "ADJ")
                advs2 = tokens_by_type(combination[1][2], "ADV")
                if len(verbs2) == 1:
                    # NOTE: len(verbs2) may be 0 in case of reified OP label
                    # disjoint
                    if verbs2[0] in syn_dict_1[str(combination[0][0])]["VERB"] and \
                       (any([adj[1] in ant_dict_1[str(combination[0][0])]["ADJ"] for adj in adjs2]) or\
                        any([adv[1] in ant_dict_1[str(combination[0][0])]["ADJ"] for adv in advs2])) or\
                       verbs2[0] in ant_dict_1[str(combination[0][0])]["VERB"]:
                        implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                          rels["dis"], IMPLICIT_ANT_RATING]
                    # inverse - antonyms or passive-active combo
                    elif (combination[0][-1] and not combination[1][-1] or not combination[0][-1] and combination[1][-1])\
                         and verbs2[0] in syn_dict_1[str(combination[0][0])]["VERB"]:
                        implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                          rels["ant"], IMPLICIT_ANT_RATING]
                for iter, combo in enumerate(((combination[0], combination[1]), (combination[1], combination[0]))):
                    if check_xor_label_reification(elem_type, combo[0], combo[1], False):
                        if tokens_by_type(combo[1][2], "VERB", "ROOT")[0] in\
                           extr.get_derivationally_related_verbs(tokens_by_type(combo[0][2], "NOUN")[0], "n"):
                            implicit_match = arrange_impl_match(elem_type, str(combo[0][0]), str(combo[1][0]),\
                                                                rels["ant"], IMPLICIT_ANT_RATING, iter)
            # subsumption - hypernyms and hyponyms - analogously to explicit matching
            # RFE: consider checking hyponyms/ hypernyms also based on dsvocab
            # RFE: consider checking hyponyms/ hypernyms also for reified OP labels
            elif len(combination[1][2]) <= len(combination[0][2]) and\
                 all([elem2[1] in hype_dict_1[str(combination[0][0])][elem2[2]] or\
                     elem2[1] in syn_dict_1[str(combination[0][0])][elem2[2]] for elem2 in combination[1][2]]):
                implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  rels["hypo"], IMPLICIT_ANT_RATING]
            elif len(combination[0][2]) <= len(combination[1][2]) and\
                 all([elem1[1] in hype_dict_2[str(combination[1][0])][elem1[2]] or\
                     elem1[1] in syn_dict_2[str(combination[1][0])][elem1[2]] for elem1 in combination[0][2]]):
                implicit_match = [elem_type, str(combination[0][0]), str(combination[1][0]),\
                                  rels["hype"], IMPLICIT_ANT_RATING]
        if implicit_match:
            implicit_overlap.append(implicit_match)
    return implicit_overlap

def reduce_vector(matches):
    """remove possibly contradictory tuples from matching vector"""
    duplicates = []
    # NOTE: duplicates may be returned for iterative approach
    for elem1, elem2 in itertools.combinations(matches, 2):
        # same notions
        if elem1[:3] == elem2[:3]:
            if elem1[-1] < elem2[-1]:
                duplicates.append(elem1)
            elif elem1[-1] > elem2[-1]:
                duplicates.append(elem2)
            elif elem1[3] == "equivalence" and elem2[3] in ["hyponym", "hypernym"]:
                duplicates.append(elem2)
            elif elem2[3] == "equivalence" and elem1[3] in ["hyponym", "hypernym"]:
                duplicates.append(elem1)
        # one notion same, different equivalents
        elif (elem1[1] == elem2[1] or elem1[2] == elem2[2]) and elem1[3] == elem2[3] == "equivalence":
            if elem1[-1] < elem2[-1]:
                duplicates.append(elem1)
            else:
                duplicates.append(elem2)
        # either equivalent class or superclass
        elif elem1[1] == elem2[1] and elem1[3] in ["equivalence", "hyponym"] and elem2[3] == "hyponym" or\
             elem1[2] == elem2[2] and elem1[3] in ["equivalence", "hypernym"] and elem2[3] == "hypernym":
            if elem1[-1] < elem2[-1]:
                duplicates.append(elem1)
            else:
                duplicates.append(elem2)
    unique_matches = [elem for elem in matches if not elem in duplicates]
    return unique_matches

def main(iri1, path1, iri2, path2):
    """find explicit and implicit matches"""
    elem_types = ["owl:Class", "owl:ObjectProperty", "owl:DatatypeProperty"]
    analyzed_labels_1 = analyze_all_labels(path1, iri1)
    analyzed_labels_2 = analyze_all_labels(path2, iri2)
    matches = []
    for counter, elem_type in enumerate(elem_types):
        matches.extend(explicit_compare(analyzed_labels_1[counter], analyzed_labels_2[counter], elem_type))
        matches.extend(implicit_compare(analyzed_labels_1[counter], analyzed_labels_2[counter], elem_type))
    # remove duplicates, higher rating counts
    matches = reduce_vector(matches)
    return matches

if __name__ == "__main__":
    # ontologies
    PATH1 = "file://./../data/onto-a.owl"
    IRI1 = "http://example.org/onto-a.owl"
    PATH2 = "file://./../data/onto-fr.owl"
    IRI2 = "http://example.org/onto-fr.owl"
    print(*main(IRI1, PATH1, IRI2, PATH2), sep="\n")
