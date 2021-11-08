#!/bin/bash

# install requirements 
# Usage bash dependency-installer.sh

cp requirements.txt temp_file
sed -i '/torch/d' temp_file
sed -i '/en-core-web-sm/d' temp_file

python3.7 -m venv .venv
source .venv/bin/activate
# download pytorch wout cuda
pip install torch==1.7.0+cpu torchvision==0.8.1+cpu torchaudio==0.7.0 -f https://download.pytorch.org/whl/torch_stable.html
# install requirements
pip3 install -r temp_file
# download spacy medium language model
python3 -m spacy download en_core_web_sm
python3 <<EOF
import nltk
nltk.download('wordnet')
EOF

rm temp_file
