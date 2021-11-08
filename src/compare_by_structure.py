#!/usr/bin/env python3
"""
match onto elements based on onto structure
correspondence structure: [elem_type, iri1, iri2, relation, rating]
"""

import itertools
import sys
import rdflib
import numpy as np
import yaml

import build_query as bq
import compare_by_labels as cbl
import similarity_boundary as sb

from owlready2 import get_ontology, default_world, World, IRIS, sync_reasoner

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    INTERV_EQ = cfg["priors"]["structural"]["dp-rating"]["interval-equivalence"]
    INTERV_OV = cfg["priors"]["structural"]["dp-rating"]["interval-overlap"]
    DP_INTERV = cfg["priors"]["structural"]["dp-rating"]["interval"]
    DP_FN = cfg["priors"]["structural"]["dp-rating"]["functional"]
    DP_DOMAIN = cfg["priors"]["structural"]["dp-rating"]["domain"]
    DP_RANGE = cfg["priors"]["structural"]["dp-rating"]["range"]
    OP_DOMAIN = cfg["priors"]["structural"]["op-rating"]["domain"]
    OP_RANGE = cfg["priors"]["structural"]["op-rating"]["range"]
    OP_ATTRIBUTES = cfg["priors"]["structural"]["op-rating"]["attributes"]
    OP_BOUNDARY = cfg["priors"]["structural"]["op-rating"]["boundary"]
    DP_BOUNDARY = cfg["priors"]["structural"]["dp-rating"]["boundary"]
    THRESHOLD = cfg["settings"]["match-boundary"]
    CLASS_SEM_BOUNDARY = cfg["priors"]["semantic"]["boundary"]
    SEM_WEIGHT = cfg["priors"]["semantic"]["weighting"]
    STRUCT_DP_WEIGHT = cfg["priors"]["structural"]["dp-rating"]["weighting"]
    STRUCT_OP_WEIGHT = cfg["priors"]["structural"]["op-rating"]["weighting"]
    STRUCT_CL_WEIGHT = cfg["priors"]["structural"]["class-rating"]["weighting"]

def reasoning(path, file):
    """run reasoner and store results"""
    my_world = World()
    onto = my_world.get_ontology(path).load()
    with onto:
        sync_reasoner()
    onto.save(file)

def query_onto(path, query):
    """query onto and return results as list - onto must be already loaded"""
    my_world = World()
    onto = my_world.get_ontology(path).load()
    graph = my_world.as_rdflib_graph()
# NOTE: use of query_owlready messes up ranges of dps
    results = list(graph.query(query))
    return results

def get_basics(path):
    """get classes, object props, and datatype props from onto"""
    basics = [None, None, None]
    my_world = World()
    onto = my_world.get_ontology(path).load()
    basics[0] = onto.classes()
    basics[1] = onto.object_properties()
    basics[2] = onto.data_properties()
    return basics

def ensure_vec_length(vec_a, vec_b):
    """ensure that two vectors have the same length"""
    if len(vec_a) != len(vec_b):
        raise ValueError('vectors to be compared should have same length')

def cos_sim(vec_a, vec_b):
    """calculate cosine similarity for two vectors"""
    ensure_vec_length(vec_a, vec_b)
    # NOTE: results are w/in interval [-1; 1]
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if type(vec_a) == type(vec_b) == "numpy.ndarray":
        comparison = vec_a == vec_b
        if comparison.all():
            cos_similarity = 1.0
    elif type(vec_a) == type(vec_b) == "list" and vec_a == vec_b:
        cos_similarity = 1.0
    elif norm_a == 0.0 and norm_b != 0.0 or norm_a != 0.0 and norm_b == 0.0:
        cos_similarity = 0.0
    elif norm_a == 0.0 and norm_b == 0.0:
        cos_similarity = 1.0
    elif norm_a != 0.0 and norm_b != 0.0:
        cos_similarity = dot_product / (norm_a * norm_b)
    return cos_similarity

def positive_sim(vec_a, vec_b):
    """calculate similarity of two vectors - only count if both take value 1"""
    ensure_vec_length(vec_a, vec_b)
    similarity = 0
    baseline = max(1, sum(x == 1 or y == 1 for x, y in zip(vec_a, vec_b)))
    for i1, i2 in zip(vec_a, vec_b):
        if i1 == i2 == 1:
            similarity += 1
    similarity = similarity / baseline
    return similarity

def context_sim(set_a, set_b):
    """calculate context similarity for two sets of (predicate, object) tuples"""
    # NOTE: both sets must use the same predicates and objects for this to work
    max_length = max(len(set_a), len(set_b))
    intersection = [elem for elem in set_a if elem in set_b]
    rel_overlap = len(intersection)/max_length
    return rel_overlap

def calc_op_sim(prop_1_info, prop_2_info, class_vector, relation):
    """calculate similarity betw two ops based on op properties"""
    # op - elems 3-9 are relevant:
    # functional-inversefunctional-symmetric-asymmetric-transitive-reflexive-irreflexive
    disjoint_flag = False
    # NOTE: uninformative uniform prior - all attributes are equally likely
    v1 = [1 if not elem == None else 0 for elem in prop_1_info[3:10]]
    v2 = [1 if not elem == None else 0 for elem in prop_2_info[3:10]]
    # disjoint for symmetric[2]-asymmetric[3], reflexive[5]-irreflexive[6],
    # functional[0]-transitive[4], inversefunctional[1]-transitive[4]
    combos = [[2,3], [5,6], [0,4], [1,4]]
    if any([v1[c[0]] == 1 and v2[c[1]] == 1 or v1[c[1]] == 1 and v2[c[0]] == 1 for c in combos]):
        disjoint_flag = True
    # otherwise, use cosine similarity for vector similarity
    # NOTE: vector entries are in {0,1} - resulting cos-sim in [0,1]
    elif relation in ["equivalence", "hypernym", "hyponym"]:
        op_sim_attr = cos_sim(v1, v2)
    elif relation == "inverse":
        rating = 0
        if (v1[0] == 1 and v2[1] == 1) or (v1[0] == 1 and v2[1] == 1):
            rating += 1
        for i in range(2,7):
            if v1[i] == 1 and v2[i] == 1:
                rating += 1
        op_sim_attr = rating / (len(v1) - 1)
    elif relation == "disjoint":
        op_sim_attr = 0
    # check domain and range
    if relation in ["equivalence", "disjoint", "hypernym", "hyponym"]:
        domain_rel = domain_range_check(1, prop_1_info, prop_2_info, class_vector)
        range_rel = domain_range_check(2, prop_1_info, prop_2_info, class_vector)
        if domain_rel == "disjoint" or range_rel == "disjoint":
            disjoint_flag = True
        # NOTE: equivalence in the domain range check subsumes hypernym and hyponym relations
        elif not relation == "disjoint":
            if domain_rel == "equivalence":
                op_sim_domain = 1
            elif not domain_rel:
                op_sim_domain = 0
            if range_rel == "equivalence":
                op_sim_range = 1
            elif not range_rel:
                op_sim_range = 0
        elif relation == "disjoint":
            op_sim_domain = 0
            op_sim_range = 0
    # domain range check for inverse relations
    elif relation == "inverse":
        if domain_range_check(1, prop_1_info, prop_2_info, class_vector, inverse=True) == "inverse":
            op_sim_domain = 1
        else:
            op_sim_domain = 0
        if domain_range_check(2, prop_1_info, prop_2_info, class_vector, inverse=True) == "inverse":
            op_sim_range = 1
        else:
            op_sim_domain = 0
    # put everything together
    if relation in ["equivalence", "inverse", "hypernym", "hyponym"]:
        if disjoint_flag:
            dp_sim = 0
        else:
            op_sim = (op_sim_attr * OP_ATTRIBUTES + op_sim_domain * OP_DOMAIN + op_sim_range * OP_RANGE) /\
                     (OP_ATTRIBUTES + OP_DOMAIN + OP_RANGE)
    elif relation == "disjoint":
            if disjoint_flag:
                dp_sim = 1
            else:
                dp_sim = 0
    return op_sim

def calc_dp_sim(prop_1_info, prop_2_info, class_vector, relation):
    """calculate similarity betw two dps based on dp properties"""
    # confirmation flag for disjoints
    disjoint_flag = False
    # check domain
    domain_rel = domain_range_check(1, prop_1_info, prop_2_info, class_vector)
    if domain_rel == "disjoint":
        disjoint_flag = True
    elif relation == "disjoint":
        dp_sim = 0
    elif relation in ["equivalence", "hypernym", "hyponym"] and domain_rel == "equivalence":
        dp_sim_domain = 1
    else:
        dp_sim_domain = 0
    # check range - in case the values are actually the same
    range_rel = domain_range_check(2, prop_1_info, prop_2_info, class_vector)
    if range_rel == "equivalence":
        dp_sim_range = 1
    else:
        dp_sim_range = 0
    # dp - elems 3-7 are relevant
    # interval def
    if not prop_1_info[3] == None:
        min1 = float(prop_1_info[3])
    elif not prop_1_info[4] == None:
        min1 = float(prop_1_info[4])
    else:
        min1 = None
    if not prop_1_info[5] == None:
        max1 = float(prop_1_info[5])
    elif not prop_1_info[6] == None:
        max1 = float(prop_1_info[6])
    else:
        max1 = None
    if not prop_2_info[3] == None:
        min2 = float(prop_2_info[3])
    elif not prop_2_info[4] == None:
        min2 = float(prop_2_info[4])
    else:
        min2 = None
    if not prop_2_info[5] == None:
        max2 = float(prop_2_info[5])
    elif not prop_2_info[6] == None:
        max2 = float(prop_2_info[6])
    else:
        max2 = None
    # equivalent - no information for disjoints
    if prop_1_info[3:7] == prop_2_info[3:7]:
        dp_sim_interv = INTERV_EQ
    # both are bounded
    elif min1 != None and min2 != None and max1 != None and max2 != None:
        overlap = max(0, min(max1, max2) - max(min1, min2))
        dp_sim_interv = overlap / max(max1-min1, max2-min2)
    # at least one is unbounded - no relevant information
    elif min1 == None and max1 == None or min2 == None and max2 == None:
        dp_sim_interv = 0
    # both are half-bounded
    elif (min1 != None and max1 == None or min1 == None and max1 != None) and\
         (min2 != None and max2 == None or min2 == None and max2 != None):
        if min1 != None and min2 != None and min1 == min2 or\
           max1 != None and max2 != None and max1 == max2:
            dp_sim_interv = INTERV_EQ
        elif min1 != None and max2 != None and min1 < max2 or\
             max1 != None and min2 != None and min2 < max1 or\
             min1 != None and min2 != None or \
             max1 != None and max2 != None:
            dp_sim_interv = INTERV_OV
        elif min1 != None and max2 != None and min1 > max2 or\
             max1 != None and min2 != None and min2 > max1:
            disjoint_flag = True
    # one bounded, one half-bounded
    elif min1 != None and max1 != None and\
         (min2 != None and max2 == None or min2 == None and max2 != None) or\
         min2 != None and max2 != None and\
              (min1 != None and max1 == None or min1 == None and max1 != None):
        if min1 != None and max2 != None and min1 < max2 or\
           max1 != None and min2 != None and min2 < max1:
            dp_sim_interv = INTERV_OV
        elif min1 != None and max2 != None and min1 > max2 or\
             max1 != None and min2 != None and min2 > max1:
            disjoint_flag = True
    # are both dps functional
    if str(prop_1_info[7]) == str(prop_2_info[7]) == "true":
        dp_sim_fn = 1
    else:
        dp_sim_fn = 0
    if relation in ["equivalence", "hypernym", "hyponym"]:
        if disjoint_flag:
            dp_sim = 0
        else:
            dp_sim = (dp_sim_interv * DP_INTERV + dp_sim_domain * DP_DOMAIN + dp_sim_range * DP_RANGE +\
                      dp_sim_fn * DP_FN) / (DP_INTERV + DP_DOMAIN + DP_RANGE + DP_FN)
    elif relation == "disjoint":
            if disjoint_flag:
                dp_sim = 1
            else:
                dp_sim = 0
    return dp_sim

def domain_range_check(position, axiom1, axiom2, class_vector, inverse=False):
    """check domain or range for props from different ontos"""
    # NOTE: in axioms position = 1 for domain and position = 2 for range
    rel = None
    class_vector = sb.check_boundary(class_vector, 4, CLASS_SEM_BOUNDARY)
    # check domain/ range transposition
    if inverse and position == 1 and\
       axiom1[1] and axiom2[2] and any([class_tuple[1] == str(axiom1[1]) and\
       class_tuple[2] == str(axiom2[2]) and class_tuple[3] in ["equivalence", "hypernym", "hyponym"]\
       for class_tuple in class_vector]):
        rel = "inverse"
    elif inverse and position == 2 and\
         axiom1[2] and axiom2[1] and any([class_tuple[1] == str(axiom1[2]) and\
         class_tuple[2] == str(axiom2[1]) and class_tuple[3] in ["equivalence", "hypernym", "hyponym"]\
         for class_tuple in class_vector]):
        rel = "inverse"
    # check domain/ range equivalence via class vector match or direct match for ops
    elif axiom1[position] and axiom2[position] and any([class_tuple[1] == str(axiom1[position]) and\
         class_tuple[2] == str(axiom2[position]) and class_tuple[3] in ["equivalence", "hypernym", "hyponym"]\
         for class_tuple in class_vector]) or\
         axiom1[position] and axiom2[position] and axiom1[position] == axiom2[position]:
        rel = "equivalence"
    elif axiom1[position] and axiom2[position] and any([class_tuple[1] == str(axiom1[position]) and\
         class_tuple[2] == str(axiom2[position]) and class_tuple[3] in ["disjoint"]\
         for class_tuple in class_vector]):
        rel = "disjoint"
    return rel

def create_class_vector(class_vector, class_axioms_1, class_axioms_2, prop_vector, extended=True):
    """
    create vectors for classes based on props
    set extended to False to only consider axioms in which class is subject
    """
    # create reduced class vector only considering equivalent and subsuming properties
    # NOTE: possibly extend for inverse relations
    reduced_prop_vec = [elem for elem in prop_vector if elem[3] in ["equivalence", "hypernym", "hyponym"]]
    for c in class_vector:
        if extended:
            length = 2
        else:
            length = 1
        prop_vec_1 = [0] * len(reduced_prop_vec) * length
        prop_vec_2 = [0] * len(reduced_prop_vec) * length
        if c[3] in ["equivalence", "hypernym", "hyponym"]:
            for case in range(2):
                if not extended and case == 1:
                    break
                for counter, prop in enumerate(reduced_prop_vec):
                    if any([c[1] == str(class_axiom[4 * case]) and prop[1] == str(class_axiom[3])\
                            for class_axiom in class_axioms_1]):
                        prop_vec_1[counter + len(reduced_prop_vec) * case] = 1
                    if any([c[2] == str(class_axiom[4 * case ]) and prop[2] == str(class_axiom[3])\
                            for class_axiom in class_axioms_2]):
                        prop_vec_2[counter + len(reduced_prop_vec) * case] = 1
            # NOTE: cos_sim may be used as an alternative similarity measure
            c[-1] = positive_sim(prop_vec_1, prop_vec_2)
        # NOTE: (missing) relations to other nodes are not an indicator for disjoints
        # NOTE: disjoints can semantically be confirmed via a TLO
    return class_vector

def check_disjoints(entity_1, entity_2):
    """check if two entities have disjoint parent classes"""
    # TODO: use methods ancestors() + disjoints()
    raise NotImplementedError

def combine_ratings(semantic_vec, structural_vec):
    """combine the ratings of two vectors"""
    # NOTE: assumes that elems are in positions 1 and 2, ratings are in position 3
    # NOTE: assumes that there are no duplicate elements in vectors
    # NOTE: assumes that structural_vec subsumes semantic_vec
    assert all([sema[:4] in [stru[:4] for stru in structural_vec] for sema in semantic_vec]),\
           "combine_ratings: structural vector does not subsume semantic vector"
    integrated_vec = []
    for stru in structural_vec:
        rating = stru[-1] * STRUCT_CL_WEIGHT / (SEM_WEIGHT + STRUCT_CL_WEIGHT)
        for sema in semantic_vec:
            if sema[:4] == stru[:4]:
                rating = (sema[-1] * SEM_WEIGHT + stru[-1] * STRUCT_CL_WEIGHT) /\
                         (SEM_WEIGHT + STRUCT_CL_WEIGHT)
        integrated_vec.append(stru[:4] + [rating])
    return integrated_vec

def create_prop_vector(op_vector, op_axioms_1, op_axioms_2, dp_vector, dp_axioms_1, dp_axioms_2, class_vector):
    """create vector of common properties"""
    # NOTE: assumes that there is exactly one axiom per property
    for prop_tuple in op_vector:
        if prop_tuple[3] in ["equivalence", "hyponym", "hypernym"]:
            for axiom in op_axioms_1:
                if str(axiom[0]) == prop_tuple[1]:
                    p1i = axiom
            for axiom in op_axioms_2:
                if str(axiom[0]) == prop_tuple[2]:
                    p2i = axiom
            prop_tuple[-1] = (SEM_WEIGHT*prop_tuple[-1] +\
                              STRUCT_OP_WEIGHT*calc_op_sim(p1i, p2i, class_vector, prop_tuple[3])) /\
                             (SEM_WEIGHT + STRUCT_OP_WEIGHT)
    for prop_tuple in dp_vector:
        if prop_tuple[3] in ["equivalence", "hyponym", "hypernym"]:
            for axiom in dp_axioms_1:
                if str(axiom[0]) == prop_tuple[1]:
                    p1i = axiom
            for axiom in dp_axioms_2:
                if str(axiom[0]) == prop_tuple[2]:
                    p2i = axiom
            prop_tuple[-1] = (SEM_WEIGHT*prop_tuple[-1] +\
                              STRUCT_DP_WEIGHT*calc_dp_sim(p1i, p2i, class_vector, prop_tuple[3])) /\
                             (SEM_WEIGHT + STRUCT_DP_WEIGHT)
#    op_vector = sb.check_boundary(op_vector, 4, OP_BOUNDARY)
#    dp_vector = sb.check_boundary(dp_vector, 4, DP_BOUNDARY)
    prop_vector = op_vector + dp_vector
    prop_vector = reduce_prop_vector(prop_vector)
    return prop_vector

def reduce_prop_vector(matches):
    """remove possibly contradictory tuples from matching vector"""
    duplicates = []
    for elem1, elem2 in itertools.combinations(matches, 2):
    # NOTE: in case of disjoints, hypernyms, and hyponyms, there may be several matches
        if not elem1 is elem2 and elem1[-1] >= elem2[-1] and\
           ((elem1[1] == elem2[1] or elem1[2] == elem2[2]) and\
           elem1[3] == elem2[3] and elem1[3] not in ["hypernym", "hyponym", "disjoint"] or\
           (elem1[1] == elem2[1] and elem1[2] == elem2[2]) and\
           elem1[3] == elem2[3] and elem1[3] in ["hypernym", "hyponym", "disjoint"]):
            duplicates.append(elem2)
    unique_matches = [elem for elem in matches if not elem in duplicates]
    return unique_matches

def extract_axioms(iri1, path1, iri2, path2):
    """extract axioms for classes, ops, and dps"""
    classes_body = "./../queries/class_axioms.sparql"
    ops_body = "./../queries/op_axioms.sparql"
    dps_body = "./../queries/dp_axioms.sparql"
    class_axioms_1 = query_onto(path1, bq.build_query(iri1, classes_body))
    op_axioms_1 = query_onto(path1, bq.build_query(iri1, ops_body))
    dp_axioms_1 = query_onto(path1, bq.build_query(iri1, dps_body))
    class_axioms_2 = query_onto(path2, bq.build_query(iri2, classes_body))
    op_axioms_2 = query_onto(path2, bq.build_query(iri2, ops_body))
    dp_axioms_2 = query_onto(path2, bq.build_query(iri2, dps_body))
    axioms = [[class_axioms_1, op_axioms_1, dp_axioms_1],\
             [class_axioms_2, op_axioms_2, dp_axioms_2]]
    return axioms

def get_semantic_elem_combos(iri1, path1, iri2, path2):
    """get elem combos for semantic matches"""
    supported_relations = ["equivalence", "disjoint", "inverse", "hypernym", "hyponym"]
    class_vector = []
    op_vector = []
    dp_vector = []
    semantic_matches = cbl.main(iri1, path1, iri2, path2)
    for elem in semantic_matches:
        if elem[3] not in supported_relations:
            raise ValueError("get_semantic_elem_combos: relation not supported")
        else:
            if elem[0] == "owl:Class":
                class_vector.append(elem)
            elif elem[0] == "owl:ObjectProperty":
                op_vector.append(elem)
            elif elem[0] == "owl:DatatypeProperty":
                dp_vector.append(elem)
    return [class_vector, op_vector, dp_vector]

def get_all_elem_combos(path1, path2):
    """get all combos of elems, ie classes, ops, and dps, from two ontos"""
    supported_relations = ["equivalence", "disjoint", "inverse", "hypernym", "hyponym"]
    onto1 = get_ontology(path1).load()
    onto2 = get_ontology(path2).load()
    # entities from ontos
    classes_1 = [elem.iri for elem in onto1.classes()]
    classes_2 = [elem.iri for elem in onto2.classes()]
    ops_1 = [elem.iri for elem in onto1.object_properties()]
    ops_2 = [elem.iri for elem in onto2.object_properties()]
    dps_1 = [elem.iri for elem in onto1.data_properties()]
    dps_2 = [elem.iri for elem in onto2.data_properties()]
    # create combos of entities
    class_combos = list(itertools.product(classes_1, classes_2))
    op_combos = list(itertools.product(ops_1, ops_2))
    dp_combos = list(itertools.product(dps_1, dps_2))
    # init vectors
    class_vector, op_vector, dp_vector = ([] for i in range(3))
    # create combos for supported rels
    for rel in supported_relations:
        class_vector.extend([["owl:Class", combo[0], combo[1], rel, 0] for combo in class_combos])
        op_vector.extend([["owl:ObjectProperty", combo[0], combo[1], rel, 0] for combo in op_combos])
        dp_vector.extend([["owl:DatatypeProperty", combo[0], combo[1], rel, 0] for combo in dp_combos])
    return [class_vector, op_vector, dp_vector]

def main(iri1, path1, iri2, path2, comparison_type):
    """similarity check"""
    semantic_combos = get_semantic_elem_combos(iri1, path1, iri2, path2)
    all_combos = get_all_elem_combos(path1, path2)
    axioms = extract_axioms(iri1, path1, iri2, path2)
    if comparison_type == "all":
        prop_vector = create_prop_vector(all_combos[1], axioms[0][1], axioms[1][1],\
                                         all_combos[2], axioms[0][2], axioms[1][2], semantic_combos[0])
        structural_class_matches = create_class_vector(all_combos[0], axioms[0][0], axioms[1][0], prop_vector)
    if comparison_type  == "semi":
        prop_vector = create_prop_vector(semantic_combos[1], axioms[0][1], axioms[1][1],\
                                         semantic_combos[2], axioms[0][2], axioms[1][2], semantic_combos[0])
        structural_class_matches = create_class_vector(all_combos[0], axioms[0][0], axioms[1][0], prop_vector)
    elif comparison_type == "semantic":
        prop_vector = create_prop_vector(semantic_combos[1], axioms[0][1], axioms[1][1],\
                                         semantic_combos[2], axioms[0][2], axioms[1][2], semantic_combos[0])
        structural_class_matches = create_class_vector(semantic_combos[0], axioms[0][0], axioms[1][0], prop_vector)
    class_vector = combine_ratings(semantic_combos[0], structural_class_matches)
    matches = prop_vector + class_vector
    # remove non-matches and duplicates, greedy approach - cp cbl module
    matches = sb.check_boundary(matches, 4, .01)
    matches = cbl.reduce_vector(matches)
    return matches

def print_axioms(path, iri):
    """print axioms for classes, ops, and dps"""
    classes_body = "./../queries/class_axioms.sparql"
    ops_body = "./../queries/op_axioms.sparql"
    dps_body = "./../queries/dp_axioms.sparql"
    class_axioms = query_onto(path, bq.build_query(iri, classes_body))
    print(len(class_axioms), " axiomatized class(es)")
    reduced_cas = [[c, r, p, o, mie, mii, mae, mai] for (c, e, r, p, o, mie, mii, mae, mai) in class_axioms]
    for i in reduced_cas:
        if str(i[1]) == "http://www.w3.org/2002/07/owl#equivalentClass":
            i[1] = "equivalent"
        elif str(i[1]) == "http://www.w3.org/2000/01/rdf-schema#subClassOf":
            i[1] = "subclass"
        elif str(i[1]) == "http://www.w3.org/2002/07/owl#disjointWith":
            i[1] = "disjoint"
    print("[class - relation - prop (optional) - object]")
    for i in reduced_cas:
        print(" - ".join(map(str, list(i))))
    op_axioms = query_onto(path, bq.build_query(iri, ops_body))
    print(len(op_axioms), " axiomatized op(s)")
    print("[objectprop - domain - range - functional - inversefunctional - symmetric - "\
          "asymmetric - transitive - reflexive - irreflexive - parent - inverseparent - "\
          "equivalent - inverse - disjoint - propchain]")
    for i in op_axioms:
        print(" - ".join(map(str, list(i))))
    dp_axioms = query_onto(path, bq.build_query(iri, dps_body))
    print(len(dp_axioms), " axiomatized dp(s)")
    print("[dataprop - domain - range - minex - minin - maxex - maxin - functional - "\
          "equivalent - parent - disjoint]")
    for i in dp_axioms:
        print(" - ".join(map(str, list(i))))

if __name__ == "__main__":
    path1 = "file://./../data/onto-a.owl"
    iri1 = "http://example.org/onto-a.owl"
    path2 = "file://./../data/onto-fr.owl"
    iri2 = "http://example.org/onto-fr.owl"
    print(*main(iri1, path1, iri2, path2, "semi"), sep="\n")
    #print_axioms(path1, iri1)
