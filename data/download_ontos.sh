#!/bin/bash

# download mason and mfg-onto; reduce to process descriptions 
# Usage bash download_ontos.sh

curl -L 'https://sourceforge.net/projects/mason-onto/files/latest/download' -o mason.owl
curl -L 'https://raw.githubusercontent.com/kbserm/ProcessPlanningOntology-IOF/master/ontologies/mfg-resource.owl' -o mfg-resource.owl
echo "downloaded ontologies"

for file in mason.owl mfg-resource.owl
do
    sed -i '/    <owl:imports/d' "$file"
    echo "removed imports from '$file'"
done

source ../.venv/bin/activate
python reduce_ontos.py
echo "created reduced ontos"

for file in mason.owl mfg-resource.owl
do
    rm "$file"
done
echo "cleaned up original downloads"
