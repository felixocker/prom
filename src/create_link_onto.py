#!/usr/bin/env python3
"""create link onto"""

import random
import string
import sys
import types
from owlready2 import get_ontology, IRIS, Thing, DatatypeProperty,\
                      ObjectProperty, TransitiveProperty, AllDisjoint

def gen_ids(length = 10):
    """create name and iri for link onto"""
    # ids[0] is the IRI, ids[1] is the filename, ids[2] is the respective path
    ids = [None, None, None]
    options = string.ascii_letters + string.digits
    base = ''.join((random.choice(options) for i in range(length)))
    ids[0] = "http://merge.org/" + base + ".owl"
    ids[1] = "../data/" + base + ".owl"
    ids[2] = "file://./" + ids[1]
    return ids

def insert_relation(class1, class2, relation, elem_type):
    """insert a relation between two ontos"""
    # NOTE: specifying disjoints in Owlready2 requires AllDisjoint()
    relations = {"equivalence": "equivalent_to",
                 "hypernym": "is_a", #superclass
                 "hyponym": "is_a", #subclass
                 "inverse": "inverse_property"}
    elem_types = {"owl:Class": Thing,
                  "owl:ObjectProperty": ObjectProperty,
                  "owl:DatatypeProperty": DatatypeProperty}
    # storing correspondence only is useless, as it would be added as an annotation
    # create two placeholder elements in the link onto, one for each input onto, and link them
    my_class1 = types.new_class("A_" + str(class1).split('#')[-1], (elem_types[elem_type],))
    my_class1.equivalent_to.append(IRIS[class1])
    my_class2 = types.new_class("B_" + str(class2).split('#')[-1], (elem_types[elem_type],))
    my_class2.equivalent_to.append(IRIS[class2])
    try:
        if relation == "hypernym":
            getattr(my_class2, relations[relation]).append(my_class1)
        elif relation == "inverse":
            setattr(my_class1, relations[relation], my_class2)
        elif relation == "disjoint":
            AllDisjoint([my_class1, my_class2])
        else:
            getattr(my_class1, relations[relation]).append(my_class2)
    except KeyError:
        print("unknown relation")
        sys.exit(1)

def create_link_onto(iri1, path1, iri2, path2, matches, spec_ids=None):
    """create link onto and insert matches"""
    description = "This is a link ontology generated for combining " + iri1 +\
                  " and " + iri2 + "."
    # generate ids if not specified
    if spec_ids:
        ids = spec_ids
    else:
        ids = gen_ids()
    # load ontos required
    onto1 = get_ontology(path1).load()
    onto2 = get_ontology(path2).load()
    # create link onto last to minimize information stored
    onto = get_ontology(ids[0])
    with onto:
        onto.imported_ontologies.append(onto1)
        onto.imported_ontologies.append(onto2)
    # add comment which ontos are linked
        onto.metadata.comment.append(description)
    # insert link relations for classes
        for elem in class_matches:
            insert_class_relation(elem[1], elem[2], elem[3], elem[0])
    onto.save(file=ids[1])
    return ids


def add_abox_to_link_onto(ids: list, ind_matches: list) -> None:
    onto = get_ontology(ids[0])
    with onto:
        for elem in ind_matches:
            insert_individual_relation(onto, elem[0][0], elem[1][0])
    onto.save(file=ids[1])


if __name__ == "__main__":
    create_link_onto("http://example.org/onto-a.owl", "file://./../data/onto-a.owl",
                     "http://example.org/onto-fr.owl", "file://./../data/onto-fr.owl", [])
