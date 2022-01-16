#!/usr/bin/env python3
"""main module for onto merging project"""

import unittest
import unittest.mock
import yaml

import cli_confirm as confirm
import compare_by_labels as cbl
import compare_by_structure as cbs
import create_link_onto as clo
import onto_a
import onto_fr
import similarity_boundary as sb
import translate_onto as to
import quality_assessment as qa
import baseline_string_matcher as bsm
import onto_debugger as odb
import alignment_selector as als
import abox_matcher as am

from owlready2 import onto_path

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    BENCHMARK_MODE = cfg["settings"]["benchmark"]["benchmark-mode"]
    MIN_EX = cfg["settings"]["benchmark"]["min-example"]
    ACCEPT_THRESHOLD = cfg["thresholds"]["accept"]
    REJECT_THRESHOLD = cfg["thresholds"]["reject"]
    SELECTION_ALGO = cfg["settings"]["alignment-algo"]
    PATHS = []
    for kg in ["onto1", "onto2"]:
        path = []
        for attr in ["file", "iri", "relpath", "lang"]:
            path.append(cfg["inputs"][kg][attr])
        PATHS.append(path)


def main():
    """create ontos, check consistency, preprocess, and create link onto"""
    # set onto directory globally
    onto_path.append("../data")
    # load settings
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    default_lang = cfg["settings"]["default-language"]
    match_boundary = cfg["settings"]["match-boundary"]
    if MIN_EX:
        # create ontos
        print("creating ontos")
        onto_a.main()
        onto_fr.main()
    # check ontos for consistency and translate if consistent
    print("checking consistency")
    print("----")
    for path in PATHS:
        print(path[0])
        debugger = odb.OntoDebugger(iri=path[1], path=path[2])
        debugger.debug_onto(assume_correct_taxo=False)
        to.main(path[0], path[1], path[2], default_lang, path[3])
        print("----")
    # compare ontos
    matches = cbs.main(PATHS[0][1], PATHS[0][0], PATHS[1][1], PATHS[1][0], "semi")

    # NOTE: do not include disjoints in selector, run own selector for inverse
    disj_matches = [m for m in matches if m[3] == "disjoint"]
    inv_matches = [m for m in matches if m[3] == "inverse"]
    other_matches = [m for m in matches if not m[3] in ["disjoint", "inverse"]]
    selector = als.AlignmentSelector(REJECT_THRESHOLD, other_matches, 1, 2, -1)
    selector.optimize_combination(method=SELECTION_ALGO)
    inv_selector = als.AlignmentSelector(REJECT_THRESHOLD, inv_matches, 1, 2, -1)
    inv_selector.optimize_combination(method=SELECTION_ALGO)
    matches = selector.optimal_combination + inv_selector.optimal_combination + disj_matches

    # NOTE: the following two lines introduce an exemplary inconsistency - uncomment to test debugging mode
    # requires manual confirmation of matches and manual debugging interactions
    # change accordingly in program mode (set inputs to None)
    # matches.append(['owl:Class', 'http://www.owl-ontologies.com/mason.owl#Drilling',\
    #                 'http://www.ohio.edu/ontologies/manufacturing-capability#Drilling', 'disjoint', 0.9])

    print(f"all {len(matches)} potential matches are:")
    print(*matches, sep="\n")
    # auto_accepted_matches = sb.check_boundary(matches, 4, match_boundary)
    accepted_matches = confirm.main(matches, REJECT_THRESHOLD, ACCEPT_THRESHOLD)
    print("accepted matches are:")
    print(*accepted_matches, sep="\n")
    # run loop until no more inconsistencies detected or user opts out; initially no info for link onto defined
    path_lo = None
    while True:
        print("creating link onto")
        path_lo = clo.create_link_onto(PATHS[0][1], PATHS[0][0], PATHS[1][1], PATHS[1][0], accepted_matches, path_lo)
        print("running consistency check")
        joint_debugger = odb.OntoDebugger(iri=path_lo[0], path=path_lo[1])
        inconsistent_classes = joint_debugger.reasoning()
        if not inconsistent_classes:
            print("no inconsistencies detected - check link onto: " + path_lo[2])
            break
        else:
            print("inconsistent classes detected:")
            print(*inconsistent_classes, sep="\n")
            print("would you like to interactively debug the link ontology [i] or quit [q]?")
            user_input = input()
            while user_input not in ["i", "q"]:
                print("invalid choice, please try again")
                user_input = input()
            if user_input == "q":
                break
            elif user_input == "i":
                # NOTE: debugging does not change list of accepted_matches
                joint_debugger.debug_onto(assume_correct_taxo=False)
                break
    # abox matching
    abm = am.AboxMatcher(iri1=PATHS[0][1], iri2=PATHS[1][1],
                         path1=PATHS[0][0], path2=PATHS[1][0], tbox_al=accepted_matches)
    ind_matches = abm.compare_inds(unbiased=False)
    clo.add_abox_to_link_onto(path_lo, ind_matches)
    if BENCHMARK_MODE:
        print("matching quality:")
        print(qa.create_report([match[1:4] for match in accepted_matches]))
        print("baseline matching quality (string similarity based):")
        bsm.create_baseline(configfile="config.yml", algtype="greedy", acceptance_threshold=.9)


if __name__ == "__main__":
    inputs = None
    if PATHS[0][1] == "http://www.owl-ontologies.com/mason.owl" and\
       PATHS[1][1] == "http://www.ohio.edu/ontologies/manufacturing-capability":
        inputs = ["y"]*31 + ["n"]
    elif PATHS[0][1] == "http://example.org/onto-a.owl" and\
         PATHS[1][1] == "http://example.org/onto-fr.owl":
        inputs = ["y"]*14
    if inputs:
        with unittest.mock.patch('builtins.input', side_effect=inputs):
            main()
    else:
        main()
