#!/usr/bin/env python3
"""module for ontology merging baseline using string similarity"""


import string_matcher as sm
from owlready2 import World

import decorators
import quality_assessment as qa
import translate_onto as to


def extract_class_info(paths: list) -> list:
    """ extract English labels for all classes and properties if available,
    otherwise default to entity names

    :param paths: ontology paths
    """
    class_info = {}

    def _get_label_or_name(entity):
        name = entity.label.en.first()
        if not name:
            name = entity.name
        return name

    for path in set(paths):
        world = World()
        onto = world.get_ontology(path).load()
        # assert all([len(c.label.en)==1 for c in onto.classes()]),\
        #     f"more than one English label def'ed per class"
        classes = [(c.iri, _get_label_or_name(c).lower()) for c in onto.classes()]
        props = [(c.iri, _get_label_or_name(c).lower()) for c in onto.properties()]
        class_info[path] = classes + props
    return class_info


@decorators.timeme
def create_baseline_alignment(lst1: list, lst2: list, algtype: str, threshold: float) -> list:
    matcher = sm.StringMatcher(lst1, lst2, -1, -1, threshold)
    matcher.match_lists()
    matcher.calc_alignment(algtype)
    print(matcher.score)
    return matcher.optimal_combination


def run_n_print(path1: str, path2: str, threshold: float) -> None:
    print(f"baseline for {path1} and {path2}")
    class_info = extract_class_info([path1, path2])
    for algtype in "greedy", "optimal_sc", "optimal_mc":
        combination = create_baseline_alignment(class_info[path1], class_info[path2], algtype, threshold)
        print(f"{algtype} alignment:\n{combination}")


def create_baseline(cfg: dict, algtype: str="greedy", acceptance_threshold: float=.9) -> None:
    ontopath1 = cfg["inputs"]["onto1"]["file"]
    ontopath2 = cfg["inputs"]["onto2"]["file"]
    class_info = extract_class_info([ontopath1, ontopath2])
    combination = create_baseline_alignment(class_info[ontopath1], class_info[ontopath2], algtype, acceptance_threshold)
    print(qa.create_report(cfg, [[c[0][0], c[1][0], "equivalence"] for c in combination]))



if __name__ == "__main__":
    cfg_snippet = {
        "settings": {
            "default-language": "en",
            "domain-specific-dict": True,
            "spellchecking": True,
            "benchmark": {
                "reference-alignment": "../data/reference_alignment.csv",
                "show-faulty-matches": True,
            }
        },
        "inputs": {
            "onto1": {
                "file": "../data/onto-a.owl",
            },
            "onto2": {
                "file": "../data/onto-fr.owl",
            }
        }
    }

    m1 = ["file://./../data/onto-a.owl", "file://./../data/onto-fr.owl"]
    m2 = ["file://./../data/mason_reduced.owl", "file://./../data/manufacturing-capability"]

    # translate ontos if English labels are not available
    m1_info = {"file://./../data/onto-a.owl": ["http://example.org/onto-a.owl",\
                                               "../data/onto-a.owl", "en", "en"],
               "file://./../data/onto-fr.owl": ["http://example.org/onto-fr.owl",\
                                                "../data/onto-fr.owl", "en", "fr"]}
    m2_info = {"file://./../data/mason_reduced.owl": ["http://www.owl-ontologies.com/mason.owl",\
                                                      "../data/mason_reduced.owl", "en", "en"],
               "file://./../data/manufacturing-capability": ["http://www.ohio.edu/ontologies/manufacturing-capability",\
                                                             "../data/manufacturing-capability", "en", "en"]}
    for path in m2:
        world = World()
        onto = world.get_ontology(path).load()
        if not all([len(c.label.en)==1 for c in onto.classes()]):
            to.main(path, m2_info[path][0], m2_info[path][1], cfg_snippet, m2_info[path][2], m2_info[path][3])

    for m in [m1, m2]:
        run_n_print(m[0], m[1], .9)
