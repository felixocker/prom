#!/usr/bin/env python3
"""
alignment selection
"""

import copy
import itertools as it
import multiprocessing as mp
import timeit


class AlignmentSelector:
    """optimize the alignment for a set of matches"""

    def __init__(self, threshold: float, matches: list, uid1_pos: int,
                 uid2_pos: int, rating_pos: int = -1) -> None:
        """ init

        :param threshold: acceptance threshold for similarity
        :param matches: set of matches for which an alignment shall be created
        :param uid1_pos: position of the first element's name in the match
        :param uid2_pos: position of the second element's name in the match
        :param rating_pos: position of the rating in the match, default is last slot
        """
        self.threshold: float = threshold
        self.matches: list = matches
        self.optimal_combination: list = []
        self.uid1_pos: int = uid1_pos
        self.uid2_pos: int = uid2_pos
        self.rating_pos: int = rating_pos

    def optimize_combination(self, method: str) -> None:
        """ calculate similarity for all combinations of elements from two lists

        :param method: selection method - greedy or optimal
        :return: list of tuples for all combinations and their ratings (e1, e2, rating)
        """
        methods = {"greedy": self._greedy_selection,
                   "greedy_depr": self._greedy_selection_deprecated,
                   "optimal_sc": self._optimal_selection,
                   "optimal_mc": self._optimal_selection_multicore}
        reduced_combinations = self._enforce_threshold(self.matches)
        try:
            selection = methods[method]
            self.optimal_combination = selection(reduced_combinations)
        except KeyError:
            print(f"invalid method {method} - should be one of {list(methods.keys())}")

    def _enforce_threshold(self, combinations: list) -> list:
        """ remove elements from list if their similarity is below threshold

        :param combinations: list tuples with potential matches (elem1, elem2, similarity)
        :return: accepted matches
        """
        return [e for e in combinations if e[self.rating_pos] > self.threshold]

    def _optimal_selection_multicore(self, matches: list) -> list:
        """ optimize overall matching quality assuming that only two elements can
        be matched; directly write to list of lists - use all available cores
        NOTE: helpful for larger numbers of matches (break-even at about 8 matches)

        :param matches: list of all potential matches
        :return: one possible combination w/ the highest score
        """
        if not matches:
            results: list = [[[[]]]]
        else:
            reps = len(matches)
            tasks: list = zip(it.repeat([], reps), it.repeat(.0, reps), [[m] for m in matches], it.repeat(matches, reps))
            with mp.Pool(processes=None) as pool:
                results = pool.starmap(self._next_level, tasks)
            results.sort(key=lambda x: x[1], reverse=True)
        return results[0][0][0]

    def _optimal_selection(self, matches: list) -> list:
        """ optimize overall matching quality assuming that only two elements can
        be matched; directly write to list of lists
        NOTE: helpful for smaller numbers of matches

        :param matches: list of all potential matches
        :return: one possible combination w/ the highest score
        """
        if not matches:
            combos: list = [[]]
        else:
            combos, _ = self._next_level([], 0.0, [], matches)
        return combos[0]

    @staticmethod
    def _remove_duplicates(lst: list) -> list:
        """ sort nested list and remove duplicates from nested list

        :param lst: input list of the form [[2, 3], [1, 2], [2, 3]]
        :return: sorted and simplified list of the form [[1, 2], [2, 3]]
        """
        for elem in lst:
            elem.sort()
        lst.sort()
        reduced = list(k for k, _ in it.groupby(lst))
        return reduced

    def _next_level(self, combos: list, highscore: float, option: list,
                    matches: list, mult: bool=False) -> tuple:
        """ recursive function to add to the list of combinations; always tries
        to add as many matches as possible, as all matches have a positive rating

        :param combos: (currently) best combination
        :param option: current list of matches being checked for further additions
        :param matches: list of matches, those that are already added to option are removed
        :param mult: if set to True and there exist multiple combos w/ same maximum
            score, all combos are returned
        """
        if option:
            new_matches = [m for m in matches if not m[self.uid1_pos] == option[-1][self.uid1_pos] and
                           not m[self.uid2_pos] == option[-1][self.uid2_pos]]
        else:
            new_matches = copy.copy(matches)
        new_options = []
        for m in new_matches:
            new_option = option + [m]
            new_options.append(new_option)
        if not new_options:
            if self.overall_score(option) > highscore:
                combos = [option]
                highscore = self.overall_score(option)
            elif mult and self.overall_score(option) == highscore:
                combos.append(option)
        else:
            for new_option in new_options:
                combos, highscore = self._next_level(combos, highscore, new_option, new_matches)
        return combos, highscore

    def _greedy_selection_deprecated(self, matches: list) -> list:
        """ greedy selection of best matches; a string may only be listed in one match
        NOTE: this is significantly slower than the greedy_selection that uses sort

        :param matches: list of all potential matches
        :return: greedily selected list of matches
        """
        # NOTE: in case of several matches involving the same element w the same rating
        # the first one is chosen - for performance reasons, this is not ordered and
        # may result in non-deterministic results
        selection: list = []
        for m in matches:
            match_ratings = [e[-1] for e in matches if e[self.uid1_pos] == m[self.uid1_pos] or\
                             e[self.uid2_pos] == m[self.uid2_pos]]
            selection_ratings = [e[-1] for e in selection if e[self.uid1_pos] == m[self.uid1_pos] or\
                                 e[self.uid2_pos] == m[self.uid2_pos]]
            if not any(r > m[-1] for r in match_ratings) and not any(r >= m[-1] for r in selection_ratings):
                selection.append(m)
        return selection

    def _greedy_selection(self, matches: list) -> list:
        """ greedy selection of best matches; a string may only be listed in one match
        sorts the matches first to improve performance

        :param matches: list of all potential matches
        :return: greedily selected list of matches
        """
        # NOTE: in case of several matches involving the same element w the same rating
        # the first one is chosen - may result in non-deterministic results
        selection: list = []
        matches.sort(key=lambda x: x[-1], reverse=True)
        for m in matches:
            selection_related = [e for e in selection if e[self.uid1_pos] == m[self.uid1_pos] or
                                 e[self.uid2_pos] == m[self.uid2_pos]]
            if not selection_related:
                selection.append(m)
        return selection

    def overall_score(self, elems: list) -> float:
        """ calculate overall score

        :param elems: list of elements with scores, e.g., ("a", "b", 2.3)
        :return: cumulative score of all elems
        """
        return sum([m[self.rating_pos] for m in elems])


if __name__ == "__main__":
    matches = [("c", ('1:f', 'felix'), ('2:ax', 'alex'), "d", 0.4),
               ("c", ('1:f', 'felix'), ('2:l', 'luis'), "d", 0.19999999999999996),
               ("c", ('1:f', 'felix'), ('2:j', 'john'), "d", 0.0),
               ("c", ('1:f', 'felix'), ('2:ac', 'alec'), "d", 0.19999999999999996),
               ("c", ('1:ja', 'jane'), ('2:ax', 'alex'), "d", 0.25),
               ("c", ('1:ja', 'jane'), ('2:l', 'luis'), "d", 0.0),
               ("c", ('1:ja', 'jane'), ('2:j', 'john'), "d", 0.25),
               ("c", ('1:ja', 'jane'), ('2:ac', 'alec'), "d", 0.25),
               ("c", ('1:a', 'alex'), ('2:ax', 'alex'), "d", 1.0),
               ("c", ('1:a', 'alex'), ('2:l', 'luis'), "d", 0.0),
               ("c", ('1:a', 'alex'), ('2:j', 'john'), "d", 0.0),
               ("c", ('1:a', 'alex'), ('2:ac', 'alec'), "d", 0.75),
               ("c", ('1:jo', 'jon'), ('2:ax', 'alex'), "d", 0.0),
               ("c", ('1:jo', 'jon'), ('2:l', 'luis'), "d", 0.0),
               ("c", ('1:jo', 'jon'), ('2:j', 'john'), "d", 0.75),
               ("c", ('1:jo', 'jon'), ('2:ac', 'alec'), "d", 0.0),
               ("c", ('1:b', 'blex'), ('2:ax', 'alex'), "d", 0.75),
               ("c", ('1:b', 'blex'), ('2:l', 'luis'), "d", 0.0),
               ("c", ('1:b', 'blex'), ('2:j', 'john'), "d", 0.0),
               ("c", ('1:b', 'blex'), ('2:ac', 'alec'), "d", 0.5)]
    selector = AlignmentSelector(.6, matches, 1, 2, -1)

    for mtype in "greedy", "greedy_depr", "optimal_sc", "optimal_mc":
        tic = timeit.default_timer()
        selector.optimize_combination(mtype)
        toc = timeit.default_timer()
        print(f"{mtype} matches: {selector.optimal_combination}")
        print(f"score: {selector.overall_score(selector.optimal_combination)} in: {toc - tic}")
