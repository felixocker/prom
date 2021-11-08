#!/usr/bin/env python3
"""
module for finding words related to input in electropedia
http://www.electropedia.org/
"""

import bs4
import requests
import sys
import webbrowser

SOURCE_LANGS = ["ar", "cs", "de", "en", "es", "fi", "fr", "it", "ja", "ko", "nb",\
                "nn", "pl", "pt", "ru", "sl", "sr", "sv", "zh"]
SINK_LANGS = ["ar", "de", "en", "es", "fr", "it", "ko", "ja", "pl", "pt", "zh"]

def get_id(search_term, source_lang):
    """get ID for specific term"""
    base_address_pt1a = 'http://www.electropedia.org/iev/iev.nsf/SearchView?'
    base_address_pt1b = 'SearchView&Query=field+SearchFields+contains+'
    base_address_pt2 = '+and+field+Language='
    base_address_pt3 = '&SearchOrder=4&SearchMax=0'
    ids = []
    this_id = None
    adapted_term = '%20'.join(search_term.split())
    if source_lang in SOURCE_LANGS:
        address = base_address_pt1a + base_address_pt1b + adapted_term + base_address_pt2 +\
                  source_lang + base_address_pt3
    else:
        print("extract_electropedia: source language not supported")
        sys.exit()
    res = requests.get(address)
    res.raise_for_status()
    wordnet_soup = bs4.BeautifulSoup(res.text, features="html.parser")
    elems = wordnet_soup.select('tr > td > a')
    for elem in elems:
        parent = elem.find_parent('tr')
        elem_id = parent.select('td > a')[0].getText()
        elem_name = parent.select('td > div')[0].getText().split(", ")[0]
        if elem_name == search_term:
            ids.append(elem_id)
    if len(ids) == 1:
        this_id = ids[0]
    # NOTE: there may either be too many fits or zero fits so that this_id is returned as None
    return this_id

def get_translation(search_term, source_lang, sink_lang):
    """get translation for term with ID in specified language"""
    base_address = 'http://www.electropedia.org/iev/iev.nsf/display?openform&ievref='
    translation = None
    id = get_id(search_term, source_lang)
    if id:
        address = base_address + id
#    webbrowser.get(using='google-chrome').open(address,new=2)
        res = requests.get(address)
        res.raise_for_status()
        wordnet_soup = bs4.BeautifulSoup(res.text, features="html.parser")
        elems = wordnet_soup.select('tr')
        for elem in elems:
            elem_lang = elem.select('td > div > font')
            if elem_lang:
                l = elem_lang[0].getText()
                if l == sink_lang:
                    elem_text = elem.select('td:nth-of-type(3)')
                    if elem_text[0].select('b'):
                        translation = elem_text[0].select('b')[0].getText().strip().split(',', 1)[0]
                    elif elem_text:
                        translation = elem_text[0].getText().strip().split(',', 1)[0]
    else:
        translation = None
    return translation

if __name__ == "__main__":
    print(get_translation("worm gear", "en", "fr"))
    print(get_translation("engrenage à vis sans fin", "fr", "en"))
    print(get_translation("entreprise", "fr", "en"))
