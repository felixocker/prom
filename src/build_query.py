#!/usr/bin/env python3
"""module for building SPARQL queries"""

PREFIXES = "./../queries/prefixes.sparql"

def build_query(iri, body, generic_pref = PREFIXES):
    """concatenate prefixes and body"""
    gp = open(generic_pref, "r")
    sp = "PREFIX : <" + iri + "#>"
    b = open(body, "r")
    query = gp.read() + sp + "\n\n" + b.read()
    return query

if __name__ == "__main__":
    my_iri = "http://www.test.org/test"
    body = "./../queries/structure.sparql"
    print(build_query(my_iri, body))
