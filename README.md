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
* on Linux, run the bash script *dependency_installer.sh* to set up a virtual environment with the packages required
* minimal example: simply run *main.py*
* production process example:
  1. download ontologies and preprocess them using the bash script *download_ontos.sh* in *data/*
  2. adapt the config file, as a reference cp. the file *alt_config.yml* in *docs/*
  3. run *main.py*
* for running OAEI benchmarks, cp. the instructions in the utility scripts in *docs/*

# Citation
For scientific use, please cite using the following bibtex entry:
```
@article{ocker2021cii,
title = {{A Framework for Merging Ontologies in the Context of Smart Factories (accepted)}},
author = {Ocker, Felix and Vogel-Heuser, Birgit and Paredis, Christiaan JJ},
journal={Computers in Industry},
year = {2021},
publisher={Elsevier}
}
```

# License
GPL v3.0

# Contact
Felix Ocker - [felix.ocker@tum.de](mailto:felix.ocker@tum.de)\
Technical University of Munich - [Institute of Automation and Information Systems](https://www.mw.tum.de/en/ais/homepage/)
