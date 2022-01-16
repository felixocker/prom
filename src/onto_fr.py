#!/usr/bin/env python3
"""exemplary onto w language tags, see https://pythonhosted.org/Owlready2/annotations.html"""

from owlready2 import get_ontology, Thing, DatatypeProperty, ObjectProperty,\
                      locstr, ConstrainedDatatype, FunctionalProperty, AllDisjoint,\
                      TransitiveProperty

IRI = "http://example.org/onto-fr.owl"
FILE = "../data/onto-fr.owl"


def main():
    """create onto fr and save to file"""
    onto = get_ontology(IRI)

    with onto:
        # classes
        class a(Thing):
            label = [locstr("produit", lang="fr")]
        class voiture(a):
            label = [locstr("voiture", lang="fr")]
        class b(Thing):
            label = [locstr("ressource")]  # , lang="fr")]
        class entreprise(Thing): pass
        class c(Thing): pass
        # d is somewhat similar to a, but not as good a fit for onto-a-product
        class d(Thing): pass
        class e(b):
            label = [locstr("une ressource très bonne", lang="fr")]
        class grande_ressource(b):
            label = [locstr("ressource énorme", lang="fr")]
        class processus(Thing):
            label = [locstr("processus", lang="fr")]
        class transport(Thing):
            label = [locstr("transport", lang="fr")]
        class f(Thing):
            label = [locstr("engrenage à vis sans fin", lang="fr")]
        class ex_op(ObjectProperty):
            label = [locstr("produire", lang="fr")]
            domain = [b]
            range = [a]
        # added to check antonym detection
        class souleve(ObjectProperty):
            label = [locstr("souleve", lang="fr")]
            domain = [b]
        class creer(ObjectProperty):
            label = [locstr("créer", lang="fr")]
        class est_cree_par(ObjectProperty, FunctionalProperty):
            label = [locstr("est créé par", lang="fr")]
        class successeur(ObjectProperty, TransitiveProperty):
            label = [locstr("successeur", lang="fr")]
            domain = [processus]
            range = [processus]
        class a_longueur(DatatypeProperty): pass
        class rel(DatatypeProperty):
            label = [locstr("grande largeur", lang="fr")]
            domain = [a]
            range = [ConstrainedDatatype(float, min_inclusive=10, max_inclusive=30)]
        class di(DatatypeProperty):
            label = [locstr("distance", lang="fr")]
            domain = [processus]
            range = [float]
        class du(DatatypeProperty):
            label = [locstr("durée", lang="fr")]
            domain = [processus]
            range = [float]
        # axioms
        a.equivalent_to.append(c)
        a.equivalent_to.append(a_longueur.some(float))
        a.equivalent_to.append(rel.some(float))
        b.equivalent_to.append(ex_op.some(a))
        d.equivalent_to.append(a_longueur.some(float))
        d.equivalent_to.append(est_cree_par.some(b))
        transport.is_a.append(di.some(float))
        transport.is_a.append(du.some(float))
        AllDisjoint([souleve, creer])

    for i in range(1, 5):
        m = a("aa" + str(i), a_longueur=[float(6-i)])
    aa5 = voiture("aa5", a_longueur=[1.0])
    for i in range(1, 3):
        m = b("am" + str(i), a_longueur=[float(6-i)])
    # onto["aa1"].creer.append(onto["am1"])
    onto["aa2"].creer.append(onto["aa1"])
    onto["aa2"].a_longueur.append(10.0)
    onto["aa2"].du.append(10.0)

    onto["am2"].creer.append(onto["aa1"])
    onto["am2"].du.append(10.0)

    onto.save(file=FILE)


if __name__ == "__main__":
    main()
