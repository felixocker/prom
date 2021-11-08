#!/usr/bin/env python3
"""string matcher"""


import itertools as it
from Levenshtein import distance as levenshtein_dist

import alignment_selector as sel


class StringMatcher():
    """manage the string matching process"""

    def __init__(self, list1: list, list2: list, pos1: int, pos2: int, threshold: float) -> None:
        """ init

        :param threshold: acceptance threshold for similarity
        :param list1: first input list with strings to be matches
        :param list2: second input list with strings to be matches
        :param pos1: position of the relevant string in the tuples of list1
        :param pos2: position of the relevant string in the tuples of list2
        """
        self.list1: list = list1
        self.list2: list = list2
        self.pos1: int = pos1
        self.pos2: int = pos2
        self.threshold: float = threshold
        self.matches: list = []
        self.optimal_combination: list = []
        self.score: float = None


    def match_lists(self) -> None:
        """calculate similarity for all combinations of elements from two lists"""
        for combo in list(it.product(self.list1, self.list2)):
            self.matches.append((combo[0], combo[1], self.norm_levenshtein_dist(combo[0][self.pos1], combo[1][self.pos2])))


    def calc_alignment(self, method: str) -> None:
        selector = sel.AlignmentSelector(self.threshold, self.matches, uid1_pos=0, uid2_pos=1)
        selector.optimize_combination(method)
        self.optimal_combination = selector.optimal_combination
        self.score = selector.overall_score(selector.optimal_combination)


    @staticmethod
    def norm_levenshtein_dist(str1: str, str2: str) -> float:
        """ calculate levenshtein distance normalized to string length; the higher
        the value the higher similarity; similarity values are within the range [0;1]

        :param str1: first string to be compared
        :param str2: second string to be compared
        :return: similarity value normalized to string length
        """
        return 1 - levenshtein_dist(str1, str2) / max(len(str1), len(str2))



if __name__ == "__main__":

    lst1 = [("1:f","felix"), ("1:ja","jane"), ("1:a","alex"), ("1:jo","jon"), ("1:b","blex")]
    lst2 = [("2:ax","alex"), ("2:l","luis"), ("2:j","john"), ("2:ac","alec")]

    matcher = StringMatcher(lst1, lst2, -1, -1, .6)
    matcher.match_lists()
    print(f"matches are:\n{matcher.matches}")
    for mtype in "greedy", "optimal_sc", "optimal_mc":
        matcher.calc_alignment(mtype)
        print(f"{mtype} matches: {matcher.optimal_combination}")
        print(f"score: {matcher.score}")
