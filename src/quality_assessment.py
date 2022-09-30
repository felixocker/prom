#!/usr/bin/env python3
"""
assess alignment quality by comparing against reference alignment
input alignments are expected to be lists of 3-tuples
"""

import csv


def csv_to_nested_list(ref_file):
    """read csv and return nested list with synsets"""
    with open(ref_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        reference = list(reader)
    return reference


def intersect(list_1, list_2):
    """get intersection of two lists"""
    intersection = [elem for elem in list_1 if elem in list_2]
    return intersection


def calc_precision(alignment, ref_alignment, details):
    """calculate precision: R cap A / A"""
    if not alignment:
        precision = 0
    else:
        precision = len(intersect(alignment, ref_alignment)) / len(alignment)
        if details:
            print("wrongfully identified matches:")
            print(*[m for m in alignment if not m in ref_alignment], sep="\n")
    return precision


def calc_recall(alignment, ref_alignment, details):
    """calculate recall: R cap A / R"""
    if not ref_alignment:
        recall = 0
    else:
        recall = len(intersect(alignment, ref_alignment)) / len(ref_alignment)
        if details:
            print("unidentified matches:")
            print(*[m for m in ref_alignment if not m in alignment], sep="\n")
    return recall


def calc_fmeasure(precision, recall):
    """calculate f-measure"""
    if precision + recall == 0:
        fmeasure = 0
    else:
        fmeasure = 2*precision*recall/(precision+recall)
    return fmeasure


def create_report(cfg: dict, alignment) -> dict:
    """calculate measures and return dict with values"""
    path = cfg["settings"]["benchmark"]["reference-alignment"]
    details = cfg["settings"]["benchmark"]["show-faulty-matches"]

    ref_alignment = csv_to_nested_list(path)
    assert(len(alignment[0]) == len(ref_alignment[0]) == 3), "unexpected input format"
    assessment = {"precision": None,
                  "recall": None,
                  "fmeasure": None}
    assessment["precision"] = calc_precision(alignment, ref_alignment, details)
    assessment["recall"] = calc_recall(alignment, ref_alignment, details)
    assessment["fmeasure"] = calc_fmeasure(assessment["precision"], assessment["recall"])
    return assessment


if __name__ == "__main__":
    cfg_snippet = {
        "settings": {
            "benchmark": {
                "reference-alignment": "../data/reference_alignment.csv",
                "show-faulty-matches": True,
            }
        }
    }

    alignment = [['http://example.org/onto-a.owl#is_created_by', 'http://example.org/onto-fr.owl#est_cree_par', 'equivalence'],\
                 ["http://example.org/onto-a.owl#produce", "http://example.org/onto-fr.owl#ex_op", "equivalence"]]
    print(create_report(cfg_snippet, alignment))
