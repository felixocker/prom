#!/usr/bin/env python3
"""remove unnecessary classes"""

from owlready2 import get_ontology, destroy_entity, IRIS

def reduce_mfg(source, target):
    mfg_keep = ["http://www.ohio.edu/ontologies/manufacturing-capability#MachiningProcess",\
                "http://www.ontologyrepository.com/CommonCoreOntologies/ArtifactFunction"]
    mfg_except = ["obo.BFO_0000040",\
                  "mfg-resource.ArtifactCapability",\
                  "CommonCoreOntologies.Artifact",\
                  "mfg-resource.DrillingTool",\
                  "CommonCoreOntologies.Tool",\
                  "mfg-resource.capability"]
    mfg_manual = ["http://www.ohio.edu/ontologies/manufacturing-capability#ArtifactCapability",\
                  "http://www.ohio.edu/ontologies/manufacturing-capability#capability",\
                  "http://purl.obolibrary.org/obo/BFO_0000040",\
                  "http://www.ontologyrepository.com/CommonCoreOntologies/Artifact",\
                  "http://www.ohio.edu/ontologies/manufacturing-capability#DrillingTool"]
    onto = get_ontology(source).load()
    with onto:
        classes = onto.classes()
        rm = [elem for elem in classes if not any([IRIS[iri] in elem.ancestors() for iri in mfg_keep])]
        rm = [elem for elem in rm if not str(elem) in mfg_except]
        while rm:
            for elem in rm:
                if not elem.descendants().remove(elem):
                    try:
                        destroy_entity(elem)
                        rm.remove(elem)
                    except:
                        pass
        for iri in mfg_manual:
            destroy_entity(IRIS[iri])
    onto.save(file=target)

def reduce_mason(source, target):
    mason_rm = ["http://www.owl-ontologies.com/mason.owl#Entity",\
                "http://www.owl-ontologies.com/mason.owl#Human_operation",\
                "http://www.owl-ontologies.com/mason.owl#Resource"]
    onto = get_ontology(source).load()
    descendents = []
    with onto:
        for iri in mason_rm:
            descendents = IRIS[iri].descendants()
            for elem in descendents:
                destroy_entity(elem)
        destroy_entity(IRIS["http://www.owl-ontologies.com/mason.owl#Manufacturing_concept"])
    onto.save(file=target)

if __name__ == "__main__":
    reduce_mfg("file://./mfg-resource.owl", "./mfg-resource_reduced.owl")
    reduce_mason("file://./mason.owl", "./mason_reduced.owl")
