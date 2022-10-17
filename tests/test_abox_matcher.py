#!/usr/bin/env python3
"""
test abox matcher
"""

import unittest
import unittest.mock
from pathlib import Path

import abox_matcher as abm


class TestCore(unittest.TestCase):

    test_dir = Path(__file__).parent
    cfg_snippet = {
        "abox": {
            "string-threshold": .95,
            "overall-threshold": .1,
            "algtype": "greedy",
            "weighting": {
                "label": .2,
                "structure": .8,
                "structure-sub": {
                    "dp": .4,
                    "op-outgoing": .3,
                    "op-incoming": .3,
                    "op-threshold": 1,
                }
            }
        }
    }
    tbox_alignment = [["owl:Class", "http://example.org/onto-a.owl#merhcandise",
                       "http://example.org/onto-fr.owl#a", "equivalence", .9],
                      ["owl:Class", "http://example.org/onto-a.owl#car",
                       "http://example.org/onto-fr.owl#voiture", "equivalence", .9],
                      ["owl:ObjectProperty", "http://example.org/onto-a.owl#produce",
                       "http://example.org/onto-fr.owl#creer", "equivalence", .8],
                      ["owl:DatatypeProperty", "http://example.org/onto-a.owl#length",
                       "http://example.org/onto-fr.owl#a_longueur", "equivalence", .8],
                      ["owl:DatatypeProperty", "http://example.org/onto-a.owl#duration",
                       "http://example.org/onto-fr.owl#du", "equivalence", .8]]
    ref_align = [(["onto-a.mm5", "mm5"], ["onto-fr.aa1", "aa1"], 0.5599999999999999),
                 (["onto-a.mm4", "mm4"], ["onto-fr.aa2", "aa2"], 0.5435786553761645),
                 (["onto-a.mm3", "mm3"], ["onto-fr.aa3", "aa3"], 0.3866666666666667),
                 (["onto-a.mm2", "mm2"], ["onto-fr.aa4", "aa4"], 0.32000000000000006),
                 (["onto-a.mm1", "mm1"], ["onto-fr.aa5", "aa5"], 0.32000000000000006)]

    def test_abm(self):
        abmi = abm.AboxMatcher(iri1="http://example.org/onto-a.owl", iri2="http://example.org/onto-fr.owl",
                               path1=str(self.test_dir)+"/../data/onto-a.owl", path2=str(self.test_dir)+"/../data/onto-fr.owl",
                               tbox_al=self.tbox_alignment, cfg=self.cfg_snippet)
        alignment = abmi.compare_inds(unbiased=False)
        p_align = [([str(t[0][0]), str(t[0][1])], [str(t[1][0]), str(t[1][1])], t[2]) for t in alignment]
        self.assertEqual(p_align, self.ref_align, "abox alignment not as expected")


if __name__ == "__main__":
    unittest.main()
