#!/usr/bin/env python3
"""
module for translating labels to en in an ontology.
explicitly supported languages are [en, fr, de], should also work with other languages though
if specified by user and if the input is English, run spellchecker
"""

import re
import spacy
import sys
import time
import yaml
import googletrans as gt
import spelchek

import extract_electropedia as ee

from langdetect import detect
from owlready2 import get_ontology, IRIS, locstr, World
from spacy.matcher import Matcher
from transformers import MarianTokenizer, MarianMTModel
from translate import Translator
from typing import List

NLP = spacy.load("en_core_web_sm")
GTRANS = gt.Translator()

# preload huggingface MarianMT models
DE_EN_model = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-de-en')
DE_EN_tok = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-de-en')
FR_EN_model = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-fr-en')
FR_EN_tok = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-fr-en')

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    DEFAULT_LANG = cfg["settings"]["default-language"]
    DOMAIN_DICT = cfg["settings"]["domain-specific-dict"]
    SPELLCHECK = cfg["settings"]["spellchecking"]

def create_query(iri, element_type):
    """SPARQL query to extract classes, labels, and language tags"""
    query = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX : <""" + iri + """#>
        SELECT DISTINCT ?elem ?label ?language WHERE {
        ?elem a """ + element_type + """ . 
        OPTIONAL {
            ?elem rdfs:label ?label . 
            BIND ( lang(?label) AS ?language ) . 
        }
        }
        ORDER BY ?elem ?language"""
    return query

def query_onto(path, query):
    """query onto and return results as list - onto must be already loaded"""
    my_world = World()
    onto = my_world.get_ontology(path).load()
    graph = my_world.as_rdflib_graph()
    results = list(graph.query(query))
    return results

def reduce_to_class(elem):
    """return only actual class name"""
    # NOTE: assumes that # is used to separate entity name from onto name
    return elem.split("#")[-1]

def huggingface_translate(text, src, trg):
    """translate text using the huggingface translator"""
    # NOTE: German and French language models are globally preloaded to improve performance
    if src == "de" and trg == "en":
        model = DE_EN_model
        tok = DE_EN_tok
    elif src == "fr" and trg == "en":
        model = FR_EN_model
        tok = FR_EN_tok
    else:
        mname = f'Helsinki-NLP/opus-mt-{src}-{trg}'
        model = MarianMTModel.from_pretrained(mname)
        tok = MarianTokenizer.from_pretrained(mname)
    batch = tok.prepare_seq2seq_batch(src_texts=[text])
    gen = model.generate(**batch)
    words: List[str] = tok.batch_decode(gen, skip_special_tokens=True)
    return words[0]

def translate_w_google(text, source, sink):
    """translate a word using the googletrans package"""
    # NOTE: does not work reliably
    translation = GTRANS.translate(text, dest=sink, src=source).text
    print(translation)
    time.sleep(1)
    return translation

def translate(text, source, sink):
    """translate a word using the translate package"""
    translator = Translator(from_lang=source, to_lang=sink)
    translation = translator.translate(text)
    return translation

def two_stage_translate(text, src, trg, translator="hf"):
    """try translating via domain-specific dict first, otherwise default to translator"""
    funcs = {"hf": huggingface_translate,
             "twg": translate_w_google,
             "t": translate}
    try:
        func = funcs[translator]
    except KeyError:
        print("unknown translator", translator)
        sys.exit(1)
    if DOMAIN_DICT:
        translation = ee.get_translation(text, str(src), str(trg))
    if not DOMAIN_DICT or not translation:
        translation = func(text, src, trg)
    return translation

def tknzr(text):
    """tokenizer for spaces, underscores, camelcase, and dromedacase"""
    regex = r'[A-ZÁÀÂÇÉÈÊÔÚÙÛÄÖÜ]?[a-záàâçéèêôúùûäöü]+|[A-ZÁÀÂÇÉÈÊÔÚÙÛÄÖÜ]+(?=[A-ZÁÀÂÇÉÈÊÔÚÙÛÄÖÜ]|$)'
    return " ".join(re.findall(regex, text)).lower()

def extract_label(elem, elem_type):
    """extract certain POS for classes, ops, and dps"""
    # NOTE: add 'DEP':'advmod' and 'DEP':'amod' for further restrictions
    class_pattern_1 = [{'POS':'ADV','OP':'*'},{'POS':'ADJ','OP':'*'},{'POS':'VERB','OP':'*'},{'POS':'PROPN', 'OP':'*'},{'POS':'NOUN','OP':'+'}]
    op_pattern_1 = [{'POS':'AUX','OP':'*'},{'POS':'ADV','OP':'*'},{'POS':'VERB'},{'POS':'ADP','OP':'*'}]
    # NOTE: op_pattern_2 catches cases of misclassification such as "lower"
    op_pattern_2 = [{'POS':'ADJ'}]
    dp_pattern_1 = [{'POS':'ADV','DEP':'advmod','OP':'*'},{'POS':'ADJ','DEP':'amod','OP':'*'},{'POS':'NOUN'}]
    dp_pattern_2 = [{'POS':'ADV','OP':'*'},{'POS':'ADJ','OP':'*'},{'POS':'PROPN'}]
    matcher = Matcher(NLP.vocab)
    if elem_type == "owl:Class":
        matcher.add("class_matcher", None, class_pattern_1)
    elif elem_type == "owl:ObjectProperty":
        matcher.add("op_matcher", None, op_pattern_1, op_pattern_2)
    elif elem_type == "owl:DatatypeProperty":
        matcher.add("dp_matcher", None, dp_pattern_1, dp_pattern_2)
    label = elem
    doc = NLP(elem)
    matched = [doc[start:end].text for match_id, start, end in matcher(doc)]
    if matched:
        label = sorted(matched, key=len, reverse=True)[0]
    return label

def add_label(elem, elem_type, target_lang, source_lang):
    """translate input and add respective label"""
    # NOTE: language detection does not work reliably for single words
    # NOTE: language detection does not work in case of typos
    label_default = None
    classname = reduce_to_class(str(elem[0]))
    if elem[1] and elem[2] and elem[2] != target_lang:
        label_default = two_stage_translate(tknzr(str(elem[1])), elem[2], target_lang).lower()
    elif elem[1] and not elem[2]:
        if not source_lang:
            detected_lang = detect(tknzr(elem[1]))
        else:
            detected_lang = source_lang
        if detected_lang == target_lang:
            if SPELLCHECK and target_lang == "en":
            # NOTE: as of now, spellchecker only works for English
                label_default = spelchek.correct(tknzr(elem[1]))
            else:
                label_default = tknzr(elem[1])
        else:
            label_default = two_stage_translate(tknzr(str(elem[1])), detected_lang, target_lang).lower()
    elif not elem[1] and not elem[2] and len(classname) > 1:
        if not source_lang:
            detected_lang = detect(tknzr(classname))
        else:
            detected_lang = source_lang
        # possibly use spacy instead to improve reliability
        if detected_lang == target_lang:
            if SPELLCHECK and target_lang == "en":
            # NOTE: as of now, spellchecker only works for English
                label_default = spelchek.correct(tknzr(classname))
            else:
                label_default = tknzr(classname)
        else:
            label_default = two_stage_translate(tknzr(classname), detected_lang, target_lang).lower()
    elif not elem[1] and not elem[2] and len(classname) <= 1:
        label_default = classname
    if label_default:
        getattr(IRIS[str(elem[0])], "label").extend([locstr(extract_label(label_default, elem_type), lang=target_lang)])

def main(onto, iri, target, target_lang=DEFAULT_LANG, source_lang=None):
    """add labels in language specified, defaults to English"""
    classes = query_onto(onto, create_query(iri, "owl:Class"))
    objprops = query_onto(onto, create_query(iri, "owl:ObjectProperty"))
    dataprops = query_onto(onto, create_query(iri, "owl:DatatypeProperty"))
    # remove BNodes from classes
    classes = [c for c in classes if str(type(c[0])) != "<class 'rdflib.term.BNode'>"]
    # NOTE: this removes multiple labels - does not prioritize yet though
    classes = [c for n, c in enumerate(classes) if c[0] not in [cl[0] for cl in classes[:n]]]
    objprops = [c for n, c in enumerate(objprops) if c[0] not in [cl[0] for cl in objprops[:n]]]
    dataprops = [c for n, c in enumerate(dataprops) if c[0] not in [cl[0] for cl in dataprops[:n]]]
    onto = get_ontology(onto).load()
    with onto:
        for elem in classes:
            if not any(e[0] == elem[0] and str(e[2]) == target_lang for e in classes):
                add_label(elem, "owl:Class", target_lang, source_lang)
        for op in objprops:
            if not any(e[0] == op[0] and str(e[2]) == target_lang for e in objprops):
                add_label(op, "owl:ObjectProperty", target_lang, source_lang)
        for dp in dataprops:
            if not any(e[0] == dp[0] and str(e[2]) == target_lang for e in dataprops):
                add_label(dp, "owl:DatatypeProperty", target_lang, source_lang)
    onto.save(file=target)

if __name__ == "__main__":
    onto = "file://./../data/onto-fr.owl"
    iri = "http://example.org/onto-fr.owl"
    filename = "../data/onto-fr.owl"
    main(onto, iri, filename)
