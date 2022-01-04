#!/usr/bin/env python3
"""abox matcher within PrOM"""

import itertools as it
import numpy as np
import yaml
from owlready2 import World, IRIS, onto_path, owl, Property

import alignment_selector as alse
import string_matcher as stma


class AboxMatcher:
    """load and match ABoxes of two ontos"""

    relations = ["equivalence", "hypernym", "hyponym"]

    def __init__(self, iri1: str, iri2: str, path1: str, path2: str, tbox_al: list) -> None:
        """ load ontos from their IRIs and paths

        :param iri_i: IRI of the respective onto
        :param path_i: relative path to onto file
        :param tbox_al: existing TBox alignment [elemtype, iri1, iri2, reltype, rating]
        """
        self.iri1 = iri1
        self.iri2 = iri2
        self.path1 = path1
        self.path2 = path2
        self.tbox_al = tbox_al
        self.onto1_world = World()
        self.onto2_world = World()
        self.onto1 = self.onto1_world.get_ontology(self.path1).load()
        self.onto2 = self.onto2_world.get_ontology(self.path2).load()
        paths = [path.rsplit("/", maxsplit=1)[0]+"/" for path in (path1, path2)]
        onto_path.extend(list(dict.fromkeys(paths)))

        with open("config.yml", "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
            self.str_threshold = cfg["abox"]["string-threshold"]
            self.overall_threshold = cfg["abox"]["overall-threshold"]
            self.algtype = cfg["abox"]["algtype"]
            self.label_rating = cfg["abox"]["weighting"]["label"]
            self.structure_rating = cfg["abox"]["weighting"]["structure"]
            self.dp_rating = cfg["abox"]["weighting"]["structure-sub"]["dp"]
            self.opo_rating = cfg["abox"]["weighting"]["structure-sub"]["op-outgoing"]
            self.opi_rating = cfg["abox"]["weighting"]["structure-sub"]["op-incoming"]
            self.op_threshold = cfg["abox"]["weighting"]["structure-sub"]["op-threshold"]

    def compare_inds_by_structure(self, unbiased: bool=False) -> list:
        """ compare individuals by structure; compare values associated via
        datatype properties and both incoming and outgoing object properties;
        greedy selection sensible as individuals are unambiguously linked to a
        single class

        :param unbiased: do not use information about class similarity from tbox
            matching, i.e., ignore self.tbox_al
        :return: assessment of structural similarity of individuals [(ind1,ind2,rating)]
        """
        # set up object property value and data property value
        opv1 = [m[1] for m in self.tbox_al if m[0]=="owl:ObjectProperty"]
        opv2 = [m[2] for m in self.tbox_al if m[0]=="owl:ObjectProperty"]
        dpv1 = [m[1] for m in self.tbox_al if m[0]=="owl:DatatypeProperty"]
        dpv2 = [m[2] for m in self.tbox_al if m[0]=="owl:DatatypeProperty"]

        def _populate_dpvi(world: World, ind: owl.Thing, dpv: list) -> list:
            """ populate vector representing datatype properties with lists of values
            """
            return [_get_property_list(world, ind, dp) for dp in dpv]

        def _populate_outgoing_opvi(world: World, ind: owl.Thing, opv: list) -> list:
            """ populate vector with outgoing object porperties - count occurrences only,
            object is not considered
            """
            return [len(_get_property_list(world, ind, op)) for op in opv]

        def _populate_incoming_opvi(world: World, ind: owl.Thing, opv: list) -> list:
            """ populate vector with incoming object porperties - count occurrences only,
            object is not considered
            """
            # NOTE: for further details cp. owlready2/namespace.py/search
            return [len(world.search(**{myop.name: ind})) for myop in (world[op] for op in opv)]

        def _get_property_list(world: World, ind: owl.Thing, prop: Property) -> list:
            """ get list of objects for a given combination of an individual and
            a property - can be an ObjectProperty or a DatatypeProperty
            this is necessary, as Owlready2 may return None, a single object, or a list
            """
            objs = getattr(ind, world[prop].name)
            if isinstance(objs, list):
                objs_list = objs
            elif objs is None:
                objs_list = []
            else:
                objs_list = [objs]
            return objs_list

        def _rel_sim(vec_a: list, vec_b: list) -> float:
            assert len(vec_a) == len(vec_b), "input vectors are of different lengths"
            combis = list(zip(vec_a, vec_b))
            vec_a_r = [combi[0] for combi in combis if combi[0] or combi[1]]
            vec_b_r = [combi[1] for combi in combis if combi[0] or combi[1]]
            return _cos_sim(vec_a_r, vec_b_r)

        def _binary_cos_sim(vec_a: list, vec_b: list) -> float:
            """ cosine similarity, but vectors are reduced to binary representation.
            i.e., a match can either be present (both vector entries set to 0) or
            not present (second sector entry set to 1)
            only compares values if at least one vector includes an element, if
            list is empty, no conclusions can be drawn due to OWA
            NOTE: for non-functional data props, we rate value sets between which
            a subsumption relation holds with .5 - this is only reflected in the cosine
            similarity if not all value sets subsume each other (due to normalization)

            :param vec_a: first input vector
            :param vec_b: second input vector
            :return: cosine similarity for simplified vectors
            """
            binv_a = [1 for c, val in enumerate(vec_a) if val or vec_b[c]]
            binv_b = [1 if sorted(val) == sorted(vec_a[c])
                      else .5 if all(e in vec_a[c] for e in val) or all(e in val for e in vec_a[c])
                      else 0 for c, val in enumerate(vec_b) if val or vec_a[c]]
            return _cos_sim(binv_a, binv_b)

        def _cos_sim(vec_a: list, vec_b: list) -> float:
            """ calculate cosine similarity for two vectors
            NOTE: if number of available properties is below op-threshold (set via
            config) then the cosine similarity cannot be assessed and is set to 0

            :param vec_a: first vector
            :param vec_b: second vector
            :return: cosine similarity for the two input vectors
            """
            assert len(vec_a) == len(vec_b), "issue with vector lengths"
            dot_product = np.dot(vec_a, vec_b)
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            cos_sim = None
            if len(vec_a) < self.op_threshold or norm_a == 0.0 or norm_b == 0.0:
                cos_sim = 0.0
            elif isinstance(vec_a, np.ndarray) and isinstance(vec_b, np.ndarray):
                comparison = vec_a == vec_b
                if comparison.all():
                    cos_sim = 1.0
            elif isinstance(vec_a, list) and isinstance(vec_b, list) and vec_a == vec_b:
                cos_sim = 1.0
            elif norm_a != 0.0 and norm_b != 0.0:
                cos_sim = dot_product / (norm_a * norm_b)
            return cos_sim

        def _create_prop_vec_dict(world: World, individuals: list, dpv: list, opv: list) -> dict:
            pvdict = {}
            for ind in individuals:
                pvdict[ind] = {
                    "dpv": _populate_dpvi(world, ind, dpv),
                    "opvo": _populate_outgoing_opvi(world, ind, opv),
                    "opvi": _populate_incoming_opvi(world, ind, opv)
                }
            return pvdict

        def _calc_ratings_for_ind_sets(inds1: list, inds2: list) -> list:
            """ calculate pairwise similirity for all combinations of individuals
            from the two input lists

            :param inds1: first list of individuals to be compared
            :param inds2: second list of individuals to be compared
            :return: pairwise similarity ratings for the individuals
            """
            mydict1 = _create_prop_vec_dict(self.onto1_world, inds1, dpv1, opv1)
            mydict2 = _create_prop_vec_dict(self.onto2_world, inds2, dpv2, opv2)
            ratings: list = []
            for combi in it.product(inds1, inds2):
                dpr = _binary_cos_sim(mydict1[combi[0]]["dpv"], mydict2[combi[1]]["dpv"])
                opor = _rel_sim(mydict1[combi[0]]["opvo"], mydict2[combi[1]]["opvo"])
                opir = _rel_sim(mydict1[combi[0]]["opvi"], mydict2[combi[1]]["opvi"])
                rating = self.dp_rating * dpr + self.opo_rating * opor + self.opi_rating * opir
                ratings.append(([combi[0], combi[0].name], [combi[1], combi[1].name], rating))
            return ratings

        all_ratings: list = []
        if unbiased:
            individuals1 = list(self.onto1.individuals())
            individuals2 = list(self.onto2.individuals())
            all_ratings = _calc_ratings_for_ind_sets(individuals1, individuals2)
        else:
            for match in self.tbox_al:
                # NOTE: to reduce space complexity, it may make sense to check thresholds right away
                if match[0] == "owl:Class" and match[3] in self.relations:
                    individuals1 = self.onto1_world[match[1]].instances()
                    individuals2 = self.onto2_world[match[2]].instances()
                    all_ratings.extend(_calc_ratings_for_ind_sets(individuals1, individuals2))
        return all_ratings

    def _combine_ratings(self, lst1: list, lst2: list, weighting1: float = .5, weighting2: float = .5) -> list:
        """ combine ratings from two individual comparisons

        :param lst1: results from first prior comparison (iri1, iri2, rating)
        :param lst2: results from second prior comparison (iri1, iri2, rating)
        :param weighting1: weighting for results of first prior comparison
        :param weighting2: weighting for results of second prior comparison
        :return: combined ratings for string sim and structure
        """
        double_rating = [(e1[0], e1[1], weighting1*e1[2]+weighting2*e2[2]) for e1 in lst1 for e2 in lst2 if
                         e1[0] == e2[0] and e1[1] == e2[1]]
        double_rating_pairs = [(e[0], e[1]) for e in double_rating]
        single_rating_1 = [(e[0], e[1], weighting1*e[2]) for e in lst1 if not (e[0], e[1]) in double_rating_pairs]
        single_rating_2 = [(e[0], e[1], weighting2*e[2]) for e in lst2 if not (e[0], e[1]) in double_rating_pairs]
        matches = double_rating + single_rating_1 + single_rating_2
        selector = alse.AlignmentSelector(self.overall_threshold, matches, 0, 1, -1)
        selector.optimize_combination("greedy")
        return selector.optimal_combination

    def compare_inds_by_name(self, unbiased: bool = False) -> list:
        """ leverage TBox alignment for matching individuals

        :param unbiased: do not use information about class similarity from tbox
            matching, i.e., ignore self.tbox_al
        :return: list of matched individuals
        """
        def _string_matcher(inds1: list, inds2: list) -> list:
            """ compare names using string similarity
            """
            matcher = stma.StringMatcher(inds1, inds2, -1, -1, self.str_threshold)
            matcher.match_lists()
            return matcher.matches

        if unbiased:
            individuals1 = [[i, i.name] for i in self.onto1.individuals()]
            individuals2 = [[i, i.name] for i in self.onto2.individuals()]
            str_matches = _string_matcher(individuals1, individuals2)
        else:
            str_matches = []
            for match in self.tbox_al:
                if match[0] == "owl:Class" and match[3] in self.relations:
                    individuals1 = [[i, i.name] for i in self.onto1_world[match[1]].instances()]
                    individuals2 = [[i, i.name] for i in self.onto2_world[match[2]].instances()]
                    str_matches.extend(_string_matcher(individuals1, individuals2))
        return str_matches

    def compare_inds(self, unbiased: bool=False) -> list:
        """ compare individuals in ontos specified in

        :param unbiased: if set to true, self.abox_al is used to only compare the
            individuals of classes matched during tbox matching
        :return: tuple with selected rated matches (ind1, ind2, rating)
        """
        string_matches = self.compare_inds_by_name(unbiased)
        structure_matches = self.compare_inds_by_structure(unbiased)
        matches = self._combine_ratings(string_matches, structure_matches, self.label_rating, self.structure_rating)
        return matches


if __name__ == "__main__":
    tbox_alignment = [["owl:Class", "http://example.org/onto-a.owl#merhcandise",
                      "http://example.org/onto-fr.owl#a", "equivalence", .9],
                      ["owl:ObjectProperty", "http://example.org/onto-a.owl#produce",
                      "http://example.org/onto-fr.owl#creer", "equivalence", .8],
                      ["owl:DatatypeProperty", "http://example.org/onto-a.owl#length",
                      "http://example.org/onto-fr.owl#a_longueur", "equivalence", .8],
                      ["owl:DatatypeProperty", "http://example.org/onto-a.owl#duration",
                      "http://example.org/onto-fr.owl#du", "equivalence", .8]]

    abm = AboxMatcher(iri1="http://example.org/onto-a.owl", iri2="http://example.org/onto-fr.owl",
                      path1="../data/onto-a.owl", path2="../data/onto-fr.owl", tbox_al=tbox_alignment)

    print("=== combined matching results: ===")
    print(*abm.compare_inds(unbiased=False), sep="\n")
