#!/usr/bin/env python3
"""
main module for the ontology merging project
"""

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


class Prom:
    """
    production ontology merging framework main class
    """

    def __init__(self, configfile: str, onto_dir: str="../data", verbose: bool=True) -> None:
        """ initialize with data from config file
        
        :param configfile: path to yaml configuration file
        :param onto_dir: path to directory where ontologies are stored
        """
        self.configfile = configfile
        self.path_lo = None
        self.verbose = verbose
        # load settings
        with open(self.configfile, "r") as ymlfile:
            self.cfg = yaml.safe_load(ymlfile)
            self.benchmark_mode = self.cfg["settings"]["benchmark"]["benchmark-mode"]
            self.min_ex = self.cfg["settings"]["benchmark"]["min-example"]
            self.accept_threshold = self.cfg["thresholds"]["accept"]
            self.reject_threshold = self.cfg["thresholds"]["reject"]
            self.selection_algo = self.cfg["settings"]["alignment-algo"]
            self.default_lang = self.cfg["settings"]["default-language"]
            self.match_boundary = self.cfg["settings"]["match-boundary"]
            self.paths = []
            for kg in ["onto1", "onto2"]:
                path = []
                for attr in ["file", "iri", "relpath", "lang"]:
                    path.append(self.cfg["inputs"][kg][attr])
                self.paths.append(path)
        # set onto directory globally
        onto_path.append(onto_dir)


    def setup_min(self) -> None:
        """ create ontos for minimal example
        """
        if self.verbose:
            print("creating ontos")
        onto_a.main()
        onto_fr.main()
    

    def check_inputs(self) -> None:
        """ check input ontos for consistency and translate if consistent
        """
        if self.verbose:
            print("checking consistency")
            print("----")
        for path in self.paths:
            if self.verbose:
                print(path[0])
            debugger = odb.OntoDebugger(iri=path[1], path=path[2])
            debugger.debug_onto(assume_correct_taxo=False)
            to.main(path[0], path[1], path[2], self.cfg, self.default_lang, path[3])
            if self.verbose:
                print("----")


    def match_tbox(self) -> list:
        """ terminological and structural matching of the input ontologies' tboxes
        """
        matches = cbs.main(self.paths[0][1], self.paths[0][0], self.paths[1][1], self.paths[1][0], "semi")

        # NOTE: do not include disjoints in selector, run own selector for inverse
        disj_matches = [m for m in matches if m[3] == "disjoint"]
        inv_matches = [m for m in matches if m[3] == "inverse"]
        other_matches = [m for m in matches if not m[3] in ["disjoint", "inverse"]]
        selector = als.AlignmentSelector(self.reject_threshold, other_matches, 1, 2, -1)
        selector.optimize_combination(method=self.selection_algo)
        inv_selector = als.AlignmentSelector(self.reject_threshold, inv_matches, 1, 2, -1)
        inv_selector.optimize_combination(method=self.selection_algo)
        matches = selector.optimal_combination + inv_selector.optimal_combination + disj_matches

        # NOTE: the following two lines introduce an exemplary inconsistency - uncomment to test debugging mode
        # requires manual confirmation of matches and manual debugging interactions
        # change accordingly in program mode (set inputs to None)
        # matches.append(['owl:Class', 'http://www.owl-ontologies.com/mason.owl#Drilling',\
        #                 'http://www.ohio.edu/ontologies/manufacturing-capability#Drilling', 'disjoint', 0.9])

        if self.verbose:
            print(f"all {len(matches)} potential matches are:")
            print(*matches, sep="\n")
        # auto_accepted_matches = sb.check_boundary(matches, 4, self.match_boundary)
        return matches


    def confirm_matches(self, matches: list) -> list:
        """ interactive confirmation of matches by the user

        :param matches: automatically identified matches
        """
        accepted_matches = confirm.main(matches, self.reject_threshold, self.accept_threshold)
        if self.verbose:
            print("accepted matches are:")
            print(*accepted_matches, sep="\n")
        return accepted_matches


    def create_lo(self, accepted_matches: list) -> None:
        """ create the base link ontology

        :param accepted_matches: matches to be inserted; confirmed by user in not fully-automated mode
        """
        if self.verbose:
            print("creating link onto")
        self.path_lo = clo.create_link_onto(self.paths[0][1], self.paths[0][0],
                                            self.paths[1][1], self.paths[1][0],
                                            accepted_matches, self.path_lo)


    def ensure_consistency(self, accepted_matches: list) -> None:
        """ interactive consistency checking of the link ontology created
        runs loop until no more inconsistencies detected or user opts out
        initially no info for link onto defined

        :param accepted_matches: matches to be inserted; confirmed by user in not fully-automated mode
        """
        while True:
            self.create_lo(accepted_matches)
            if self.verbose:
                print("running consistency check")
            joint_debugger = odb.OntoDebugger(iri=self.path_lo[0], path=self.path_lo[1])
            inconsistent_classes = joint_debugger.reasoning()
            if not inconsistent_classes:
                if self.verbose:
                    print("no inconsistencies detected - check link onto: " + self.path_lo[2])
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


    def match_abox(self, accepted_matches: list) -> list:
        """ matching the aboxes of the two input ontologies

        :param accepted_matches: list of accepted_matches from the tbox matching process
        """
        abm = am.AboxMatcher(iri1=self.paths[0][1], iri2=self.paths[1][1],
                             path1=self.paths[0][0], path2=self.paths[1][0],
                             tbox_al=accepted_matches, cfg=self.cfg)
        return abm.compare_inds(unbiased=False)


    def add_abox_matches(self, ind_matches: list) -> None:
        """ writes abox matches to the link onto

        :param ind_matches: list of accepted matches from the abox matching process
        """
        clo.add_abox_to_link_onto(self.path_lo, ind_matches)


    def assess_results(self, accepted_matches) -> None:
        """ check quality of the alignment created

        :param accepted_matches: list of accepted_matches from the tbox matching process
        """
        print("matching quality:")
        print(qa.create_report(cfg=self.cfg, alignment=[match[1:4] for match in accepted_matches]))
        print("baseline matching quality (string similarity based):")
        bsm.create_baseline(cfg=self.cfg, algtype="greedy", acceptance_threshold=.9)


    def run_all(self):
        """ create ontos, check consistency, preprocess, and create link onto
        """
        if self.min_ex:
            self.setup_min()
        self.check_inputs()
        tbox_matches = self.match_tbox()
        accepted_matches = self.confirm_matches(tbox_matches)
        self.ensure_consistency(accepted_matches)
        abox_matches = self.match_abox(accepted_matches)
        self.add_abox_matches(abox_matches)
        if self.benchmark_mode:
            self.assess_results(accepted_matches)
