#!/usr/bin/env python3
"""
debugging functionality taken from *our own repository - name removed for double-blind review*
could not directly import repo itself due to dependency clash
"""


import datetime
import logging
import os
import re
import sys
import textwrap
import traceback

from contextlib import contextmanager
from io import StringIO
from owlready2 import sync_reasoner_pellet, sync_reasoner_hermit, Thing, Nothing, World, onto_path,\
                      base, ThingClass, FunctionalProperty, InverseFunctionalProperty,\
                      TransitiveProperty, SymmetricProperty, AsymmetricProperty,\
                      ReflexiveProperty, IrreflexiveProperty, Restriction


LOGFILE = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+"_debugger.log"
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)


class OntoDebugger:
    """load and debug ontologies"""

    # NOTE: _prop_types corresponds to owlready2.prop._TYPE_PROPS; defined here to ensure order
    _prop_types = [FunctionalProperty, InverseFunctionalProperty, TransitiveProperty,\
                   SymmetricProperty, AsymmetricProperty, ReflexiveProperty, IrreflexiveProperty]
    _dp_range_types = {"boolean": bool,
                       "float": float,
                       "integer": int,
                       "string": str,
                       "date": datetime.date,
                       "time": datetime.time,
                       "datetime": datetime.datetime}

    def __init__(self, iri: str, path: str, import_paths: list=None) -> None:
        """ tries to load onto from file specified, creates new file if none is available

        :param iri: ontology's IRI
        :param path: path to local ontology file or URL; local is checked first
        :param import_paths: list of local directories to be checked for imports
        """
        self.iri = iri
        self.path = path
        self.filename = path.split(sep="/")[-1]
        self.logger = logging.getLogger(self.filename.split(".")[0])
        onto_path.extend(list(set([path.rsplit("/", 1)[0]]) - set(onto_path)))
        if import_paths:
            onto_path.extend(list(set(import_paths) - set(onto_path)))
        self.onto_world = World()
        try:
            self.onto = self.onto_world.get_ontology(self.path).load()
            self.logger.info("successfully loaded ontology specified")
        except:
            self.onto = self.onto_world.get_ontology(self.iri)
            self.onto.save(file = self.path)
            self.logger.info("ontology file did not exist - created a new one")

    @staticmethod
    def _indent_log(info: str) -> str:
        return textwrap.indent(info, '>   ')

    @contextmanager
    def _redirect_to_log(self):
        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            result_out = StringIO()
            result_err = StringIO()
            sys.stdout = result_out
            sys.stderr = result_err
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                if result_out.getvalue():
                    self.logger.info(f"reasoner output redirect: \n{self._indent_log(result_out.getvalue())}")
                if result_err.getvalue():
                    self.logger.info(f"reasoner errors redirect: \n{self._indent_log(result_err.getvalue())}")

    def reasoning(self, reasoner: str="hermit", save: bool=False, debug: bool=False) -> list:
        """ run reasoner to check consistency and infer new facts

        :param reasoner: reasoner can be eiter hermit or pellet
        :param save: bool - save inferences into original file
        :param debug: bool - log pellet explanations for inconsistencies; only
            works with Pellet
        :return: returns list of inconsistent classes if there are any
        """
        inconsistent_classes = []
        # add temporary world for inferences
        inferences = World()
        self._check_reasoner(reasoner)
        inf_onto = inferences.get_ontology(self.path).load()
        with inf_onto:
            try:
                with self._redirect_to_log():
                    if reasoner == "hermit":
                        sync_reasoner_hermit([inf_onto])
                    elif reasoner == "pellet":
                        # pellet explanations are generated if debug is set to >=2
                        sync_reasoner_pellet([inf_onto], infer_property_values=True,\
                                                infer_data_property_values=True, debug=debug+1)
                inconsistent_classes = list(inf_onto.inconsistent_classes())
            except Exception as exc:
                if reasoner == "pellet" and debug:
                    inconsistent_classes = self._analyze_pellet_results(exc)
                else:
                    inconsistent_classes = self.reasoning("pellet", False, True)
        if inconsistent_classes:
            self.logger.warning(f"the ontology is inconsistent: {inconsistent_classes}")
            if Nothing in inconsistent_classes:
                inconsistent_classes.remove(Nothing)
        elif save and not inconsistent_classes:
            inf_onto.save(file = self.filename)
            self._reload_from_file()
        return inconsistent_classes

    def _check_reasoner(self, reasoner: str) -> None:
        reasoners = ["hermit", "pellet"]
        if reasoner not in reasoners:
            self.logger.warning(f"unexpected reasoner: {reasoner} - available reasoners: {reasoners}")

    def _analyze_pellet_results(self, exc: Exception) -> list:
        """ analyze the explanation returned by Pellet, print it and return
        inconsistent classes
        IDEA: also consider restrictions on properties and facts about instances

        :param exc: exception thrown during reasoning process
        :return: list of classes identified as problematic
        """
        inconsistent_classes = []
        self.logger.error(repr(exc))
        expl = self._extract_pellet_explanation(traceback.format_exc())
        if expl[0]:
            print("Pellet provides the following explanation(s):")
            print(*expl[0], sep="\n")
            inconsistent_classes = [self.onto[ax[0]] for ex in expl[1] for ax in ex\
                                    if self.onto[ax[0]] in self.onto.classes()]
        else:
            print("There was a more complex issue, check log for traceback")
            self.logger.error(self._indent_log(traceback.format_exc()))
        return list(set(inconsistent_classes))

    @staticmethod
    def _extract_pellet_explanation(pellet_traceback: str) -> tuple:
        """ extract reasoner explanation

        :param pellet_traceback: traceback created when running reasoner
        :return: tuple of entire explanation and list of axioms included in explanation
        """
        rex = re.compile("Explanation\(s\): \n(.*?)\n\n", re.DOTALL|re.MULTILINE)
        res = set(re.findall(rex, pellet_traceback))
        axioms: list=[]
        if res:
            expls = [[l[5:] for l in expl.split("\n")] for expl in res]
            axioms = [[axiom.split() for axiom in block] for block in expls]
        return (res, axioms)

    def debug_onto(self, reasoner: str="hermit", assume_correct_taxo: bool=True) -> None:
        """ interactively (CLI) fix inconsistencies

        :param assume_correct_taxo: if True, the user interactions will be limited
            to restrictions, i.e., options to delete taxonomical relations are
            not included, e.g., A rdfs:subClassOf B
        :param reasoner: reasoner to be used for inferences
        """
        self._check_reasoner(reasoner)
        inconsistent_classes = self.reasoning(reasoner=reasoner, save=False)
        # NOTE: ensure that ics are defined in onto itself - cannot change imports anyways
        # returns load error otherwise when calling onto[ic.name]
        inconsistent_classes = [ic for ic in inconsistent_classes if self.onto[ic.name]]
        if not inconsistent_classes:
            print("No inconsistencies detected.")
        elif inconsistent_classes:
            print(f"Inconsistent classes are: {inconsistent_classes}")
            if self._bool_user_interaction("Show further information?"):
                debug = World()
                debug_onto = debug.get_ontology(self.path).load()
                with debug_onto:
                    try:
                        sync_reasoner_pellet([debug_onto], infer_property_values=True,\
                                             infer_data_property_values=True, debug=2)
                    except base.OwlReadyInconsistentOntologyError as err:
                        self.logger.error(repr(err))
                        self.logger.error(self._indent_log(traceback.format_exc()))
                        print("There was an issue with the input ontology; check the log for details.")
                        self._analyze_pellet_results(traceback.format_exc())
                    # IDEA: further analyze reasoner results to pin down cause of inconsistency
            if assume_correct_taxo:
                pot_probl_ax = {"is_a": self._get_incon_class_res("is_a", inconsistent_classes),
                                "equivalent_to": self._get_incon_class_res("equivalent_to", inconsistent_classes)}
            else:
                pot_probl_ax = {"is_a": [self.onto[ic.name].is_a for ic in inconsistent_classes],
                                "equivalent_to": [self.onto[ic.name].equivalent_to for ic in inconsistent_classes]}
            ax_msg = "Potentially inconsistent axiom: "
            for rel in "is_a", "equivalent_to":
                self._interactively_delete_axs_by_rel(rel, inconsistent_classes, pot_probl_ax, ax_msg)
            self.onto.save(file = self.path)
            self.debug_onto(reasoner, assume_correct_taxo)

    def _get_incon_class_res(self, restype: str, inconsistent_classes: list) -> list:
        """
        :param restype: type of class restriction, either is_a or equivalent_to
        :return: list of class restrictions for inconsistent_classes - does not return parent classes
        """
        return [self.get_class_restrictions(ic.name, res_only=True, res_type=restype) for ic in inconsistent_classes]

    def get_class_restrictions(self, class_name: str, res_only: bool=True, res_type: str="is_a") -> list:
        """ retrieve restrictions on specific class by restriction type

        :param class_name: name of the class for which restrictions shall be returned
        :param res_only: only returns Restrictions if set to True, if set to False
            parent class(es) are also included
        :param res_type: restriction type, either is_a or equivalent_to
        :return: list of restrictions on class
        """
        with self.onto:
            if res_type == "is_a":
                elems = self.onto[class_name].is_a
            elif res_type == "equivalent_to":
                elems = self.onto[class_name].equivalent_to
            else:
                self.logger.warning(f"unexpected res_type: {res_type}")
                sys.exit(1)
            if res_only:
                elems = [x for x in elems if isinstance(x, Restriction)]
            return elems

    def _interactively_delete_axs_by_rel(self, rel: str, classes: list, axioms: list, msg: str) -> None:
        """ delete axioms depending on user input; only axioms can be deleted
        that are stored in self.onto - imports are not modified

        :param rel: relation between class and axioms - is_a or equivalent_to
        :param classes: classes for which axioms are to be removed
        :param axioms: axioms which should be checked for removal
        :param msg: message to be displayed when prompting user
        """
        for count, ic in enumerate(classes):
            for ax in axioms[rel][count]:
                if ax is Thing:
                    continue
                if not isinstance(ax, Restriction):
                    if not self.onto[ax.name]:
                        continue
                if self._bool_user_interaction("Delete " + rel + " axiom?",\
                                                msg + ic.name + " " + rel + " " + str(ax)):
                    if isinstance(ax, ThingClass):
                        getattr(self.onto[ic.name], rel).remove(self.onto[ax.name])
                    else:
                        getattr(self.onto[ic.name], rel).remove(ax)
                    # IDEA: instead of simply deleting axioms, also allow user to edit them

    @staticmethod
    def _bool_user_interaction(question: str, info: str=None) -> str:
        """ simple CLI for yes/ no/ quit interaction
        """
        answer = {"y": True,
                  "n": False}
        if info:
            print(info)
        print(question + " [y(es), n(o), q(uit)]")
        user_input = input()
        while user_input not in ["y", "n", "q"]:
            print("invalid choice, please try again")
            user_input = input()
        if user_input in ["y", "n"]:
            return answer[user_input]
        if user_input == "q":
            print("quitting - process needs to be restarted")
            sys.exit(0)

