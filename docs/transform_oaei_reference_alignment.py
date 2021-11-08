#!/usr/bin/env python3
"""
transform OAEI 2012 reference alignment into CSV format for qa module

OAEI reference alignments are available here:
http://oaei.ontologymatching.org/2012/benchmarks/benchmarks.zip

INSTRUCTIONS:
1. store reference alignments to be transformed in "./"
2. adapt "files" variable according to the file names
"""

from bs4 import BeautifulSoup

def _read_file(filepath: str) -> str:
    f = open(filepath, "r", encoding="ISO-8859-1")
    return f.read()

def _write_file(filepath: str, content: str) -> None:
    f = open(filepath, "w")
    f.write(content)
    f.close()

def main(filepath: str) -> None:
    # NOTE: relations are incomplete
    relations = {
        "=": "equivalence",
        "&lt;": "hyponym",
        "<": "hyponym"
    }
    newfilepath = "../data/" + filepath.rsplit(".", -1)[0] + ".csv"
    html = _read_file(filepath)
    parsed_html = BeautifulSoup(html, features="lxml")
    iris = [a.text for a in parsed_html.find_all("a")]
    matches = [dt.text.split() for dt in parsed_html.find_all("dt")]
    alignment = [iris[0] + "##" + m[0] + "," + iris[1] + "##" + m[2] + "," + relations[m[1]] for m in matches]
    _write_file(newfilepath, "\n".join(alignment))

if __name__ == "__main__":
    files = ["refalign-103.html", "refalign-207.html", "refalign-301.html"]
    for file in files:
        print(f"transforming {file}")
        main(file)
