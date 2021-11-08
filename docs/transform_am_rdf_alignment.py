#!/usr/bin/env python3
"""
transform AgreementMaker alignment export (RDF) to CSV and create quality report

AgreementMaker is available online:
https://github.com/agreementmaker/agreementmaker

OAEI 2012 data sets are available here:
http://oaei.ontologymatching.org/2012/benchmarks/benchmarks.zip

INSTRUCTIONS:
1. run AgreementMaker with selected algorithms
2. store matching results in "./benchmark_outputs/"
3. store the respective reference alignments in "../data/"
4. OAEI HTML reference alignments can be transformed into the required CSV format
    using the transform_oaei_reference_alignment.py module
5. adapt the file names for matching results and ref alignments defined in "data"
"""

from bs4 import BeautifulSoup
import sys
sys.path.append('../src/')
from quality_assessment import create_report

def _read_file(filepath: str) -> str:
    f = open(filepath, "r", encoding="ISO-8859-1")
    return f.read()

def _write_file(filepath: str, content: str) -> None:
    f = open(filepath, "w")
    f.write(content)
    f.close()

def transform(filepath: str) -> None:
    relations = {
        "=": "equivalence",
        "&lt;": "hyponym",
        "<": "hyponym"
    }
    newfilepath = filepath.rsplit(".", -1)[0] + ".csv"
    rdf = _read_file(filepath)
    parsed_rdf = BeautifulSoup(rdf, features="lxml")
    iris = [e.text for e in (parsed_rdf.find("onto1"), parsed_rdf.find("onto2"))]
    print(iris)
    matches = parsed_rdf.find_all("cell")
    alignment = []
    for m in matches:
        e1 = m.find("entity1")
        l1 = "##".join(e1["rdf:resource"].split("#"))
        e2 = m.find("entity2")
        l2 = "##".join(e2["rdf:resource"].split("#"))
        r = m.find("relation")
        rel = relations[r.text]
        alignment.append([l1, l2, rel])
    return alignment

if __name__ == "__main__":
    data = {
        "refalign-103.csv": ["101_103_result_bsm.rdf", "101_103_result_vbmwm.rdf", "101_103_result_bssm.rdf"],
        "refalign-207.csv": ["101_207_result_bsm.rdf", "101_207_result_vbmwm.rdf", "101_207_result_bssm.rdf"],
        "refalign-301.csv": ["101_301_result_bsm.rdf", "101_301_result_vbmwm.rdf", "101_301_result_bssm.rdf"]
    }
    for refalign in data.keys():
        print(refalign)
        for align in data[refalign]:
            alignpath = "./benchmark_outputs/" + align
            print(f"transforming {align}")
            alignment = transform(alignpath)
            print(alignment)
            print(create_report(alignment, "../data/"+refalign, False))
