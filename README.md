# Production Ontology Merging (PrOM) Framework
OWL 2 DL ontology merging framework tailored to the production domain

# Features
* preprocessing: translations, spell checks, and interactive debugging
* matching: string-similarity-based, terminological, and structural algorithms
* correspondence selection: greedy and optimal regarding the overall similarity score
* postprocessing: link ontology creation and interactive debugging
* quality assessment: calculation of precision, recall, and F-measure

# Contents
* *data/*: production vocabulary, helper scripts for downloading ontos, and reference alignments
* *docs/*: configuration files for various examples, utilities for processing OAEI outputs and reference alignments, graphical abstract
* *queries/*: queries for information extraction
* *src/*: sources for creating, loading, preprocessing, matching, and merging the ontologies
* *dependency-installer.sh*: bash utility for installing dependencies
* *cleanup.sh*: bash utility for removing temporary and generated files

# Requirements
* Python 3.7
* bash recommended

# Instructions
* set up:
  * create venv: ```python -m venv .venv```
  * activate venv: ```source .venv/bin/activate```
  * install in editable mode: ```pip install -e .```
* minimal example: run ```python example.py``` in *examples/* folder
* production process example:
  1. download ontologies and preprocess them using the bash script ```bash download_ontos.sh``` in *data/* folder
  2. adapt the config file, as a reference cp. the file *alt_config.yml* in *docs/*
  3. run ```python example.py``` in *examples/* folder
* for running OAEI benchmarks, cp. the instructions in the utility scripts in *docs/*

# Citation
For scientific use, please cite as follows:
```
@article{ocker2022merging,
  title = {A framework for merging ontologies in the context of smart factories},
  author = {Ocker, Felix and Vogel-Heuser, Birgit and Paredis, Christiaan JJ},
  journal={Computers in Industry},
  volume={135},
  pages={103571},
  year = {2022},
  publisher={Elsevier},
  doi={10.1016/j.compind.2021.103571}
}
```

# License
GPL v3.0

# Contact
Felix Ocker - [felix.ocker@tum.de](mailto:felix.ocker@tum.de)\
Technical University of Munich - [Institute of Automation and Information Systems](https://www.mw.tum.de/en/ais/homepage/)
