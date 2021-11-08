# Production Ontology Merging (PrOM) Framework
OWL 2 DL ontology merging framework

# contents
* data - input data such as vocabularies, ontos, and reference alignments
* docs - some documentation
* queries - queries for information extraction
* src - sources for loading, matching, and merging the ontologies

# requirements
* Python 3.7
* bash recommended

# instructions
* on Linux, run the bash script *dependency_installer.sh* to set up a virtual environment with the packages required
* minimal example: simply run *main.py*
* production process example:
  1. download ontologies and preprocess them using the bash script *download_ontos.sh* in data/
  2. adapt the config file, as a reference cp. the file *alt_config.yml* in docs/
  3. run *main.py*

# copyright
Copyright © The authors of the paper "A Framework for Merging Ontologies in the Context of Smart Factories" submitted to CII.
All rights reserved.
NOTE: Details omitted to comply with the double anonymized review.

# contact
NOTE: Details omitted to comply with the double anonymized review.
