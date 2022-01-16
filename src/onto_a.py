#!/usr/bin/env python3
"""minimal example - ontology a"""

from owlready2 import get_ontology, Thing, DatatypeProperty, ObjectProperty,\
                      locstr, FunctionalProperty, ConstrainedDatatype, TransitiveProperty

IRI = "http://example.org/onto-a.owl"
FILE = "../data/onto-a.owl"


def main():
    """create onto a and save to file"""
    onto = get_ontology(IRI)

    with onto:
        class merhcandise(Thing): pass
        class car(merhcandise): pass
        class resource(Thing): pass
        class someVeryGoodResource(resource): pass
        class huge_resource(resource): pass
        class business(Thing): pass
        class BoringTool(resource): pass
        class process(Thing): pass
        class transfer(process): pass
        # lower added to check antonym detection
        class lower(ObjectProperty): pass
        class produce(ObjectProperty):
            domain = [resource]
            range = [merhcandise]
        class is_created_by(ObjectProperty, FunctionalProperty):
            label = [locstr("is created by", lang = "en")]
        class succeeds(ObjectProperty, TransitiveProperty):
            domain = [process]
            range = [process]
        class distance(DatatypeProperty):
            domain = [process]
            range = [float]
        class duration(DatatypeProperty):
            domain = [process]
            range = [float]
        class length(DatatypeProperty, FunctionalProperty): pass
        class width(DatatypeProperty):
            domain = [merhcandise]
            range = [ConstrainedDatatype(float, min_inclusive = 0, max_inclusive = 13)]
        merhcandise.is_a.append(length.some(float))
        merhcandise.is_a.append(width.some(float))
        resource.is_a.append(produce.some(merhcandise))
        transfer.is_a.append(distance.some(float))
        transfer.is_a.append(duration.some(float))

    for i in range(2, 8):
        m = merhcandise("mm" + str(i))
        m.length = float(i)
    mm1 = car("mm1")
    mm1.length = 1.0
    onto["mm4"].produce.append(onto["mm5"])
    onto["mm4"].duration.append(10.0)

    onto.save(file=FILE)


if __name__ == "__main__":
    main()
