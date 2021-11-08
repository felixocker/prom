#!/usr/bin/env python3
"""main module for onto merging project"""

import sys
import yaml

import cli_confirm as confirm
import cli_consistency as consistency
import compare_by_labels as cbl
import compare_by_structure as cbs
import create_link_onto as clo
import onto_a
import onto_fr
import similarity_boundary as sb
import suppress_outputs as silent
import translate_onto as to
import quality_assessment as qa

from owlready2 import get_ontology, default_world, World, sync_reasoner, owl,\
                      Nothing, onto_path, sync_reasoner_pellet

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    BENCHMARK_MODE = cfg["settings"]["benchmark"]["benchmark-mode"]
    MIN_EX = cfg["settings"]["benchmark"]["min-example"]
    ACCEPT_THRESHOLD = cfg["thresholds"]["accept"]
    REJECT_THRESHOLD = cfg["thresholds"]["reject"]
    PATHS = []
    for kg in ["onto1", "onto2"]:
        path = []
        for attr in ["file", "iri", "relpath", "lang"]:
            path.append(cfg["inputs"][kg][attr])
        PATHS.append(path)

def check_consistency(path):
    """check consistency of an onto, return inconsistent classes"""
    my_world = World()
    onto_path.append("./../data")
    onto = my_world.get_ontology(path).load()
    with onto:
        with silent.suppress():
            sync_reasoner_pellet(my_world, infer_property_values = True,\
                                 infer_data_property_values = True)
        inconsistent_classes = list(my_world.inconsistent_classes())
        if inconsistent_classes:
            inconsistent_classes.remove(owl.Nothing)
    return inconsistent_classes

def main():
    """create ontos, check consistency, preprocess, and create link onto"""
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
        inconsistent_classes = check_consistency(path[0])
        if inconsistent_classes:
            print("watch out - these notions are inconsistent:")
            print(*inconsistent_classes, sep="\n")
        else:
            print("no inconsistencies detected - adding translations")
            to.main(path[0], path[1], path[2], default_lang, path[3])
        print("----")
    # compare ontos
    matches = cbs.main(PATHS[0][1], PATHS[0][0], PATHS[1][1], PATHS[1][0], "semi")
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
        try:
            inconsistent_classes = check_consistency(path_lo[2])
        except:
            print("something went wrong, most likely the imports - continuing anyways")
            print("check link onto: " + path_lo[2])
            break
        if not inconsistent_classes:
            print("no inconsistencies detected - check link onto: " + path_lo[2])
            break
        else:
            print("inconsistent classes detected:")
            print(*inconsistent_classes, sep="\n")
            print("would you like to manually check matches? [y(es), n(o)]")
            user_input = input()
            while user_input not in ["y", "n"]:
                print("invalid choice, please try again")
                user_input = input()
            if user_input == "n":
                break
            else:
                accepted_matches = consistency.main(accepted_matches, inconsistent_classes)
    if BENCHMARK_MODE:
        print("matching quality:")
        print(qa.create_report([match[1:4] for match in accepted_matches]))

if __name__ == "__main__":
    main()
