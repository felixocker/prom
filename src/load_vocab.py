#!/usr/bin/env python3
"""load synsets from domain specific vocabulary file"""

import csv
import yaml

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    VOCAB = cfg["inputs"]["vocab"]

def csv_to_nested_list(vocab=VOCAB):
    """read csv and return nested list with synsets"""
    if vocab:
        with open(vocab, 'r') as csvfile:
            reader = csv.reader(csvfile)
            synsets = list(reader)
    else:
        synsets = None
    return synsets

if __name__ == "__main__":
    synsets = csv_to_nested_list()
    if type(synsets) == list:
        print(*synsets, sep="\n")
    else:
        print(synsets)
