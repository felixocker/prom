#!/usr/bin/env python3
"""
plot results for timing as boxplots and scatter
"""

import csv
import matplotlib.pyplot as plt


def load_from_csv(path: str) -> list:
    with open(path) as f:
        reader = csv.reader(f)
        data = list(reader)
    return data


def preprocess_times(data: list) -> list:
    # expects entries to be in the format "SSS.MMM"
    for r in data:
        for c, e in enumerate(r[1:]):
            r[c+1] = float(e)
    return data


def plot_boxplot(data: list, output_file: str) -> None:
    labels = [r[0] for r in data]
    fig, ax = plt.subplots(figsize=(20/2.54, 10/2.54))
    ax.set_title("Performance by data set")
    vals = [r[1:] for r in data]
    ax.boxplot(vals,
               notch=False,
               patch_artist=True,
               boxprops=dict(facecolor="white"),
               medianprops=dict(color="#0065bd"),
               labels=labels)
    # add grid
    ax.yaxis.grid(True)
    ax.set_xlabel("Data sets")
    ax.set_ylabel("Execution time [s]")
    plt.savefig(output_file)


def get_onto_sizes(input_file="./onto_data.txt") -> dict:
    onto_sizes = dict()
    with open(input_file, "r") as f:
        data = f.readlines()[2:10]
    for o in data:
        elems = o.strip().split(",")
        od = {
            "cls": int(elems[1]),
            "ops": int(elems[2]),
            "dps": int(elems[3]),
        }
        onto_sizes[elems[0]] = od
    return onto_sizes


def calc_combinations(onto_sizes: dict) -> dict:
    combos = {
        "MEXO": ["onto-a", "onto-fr"],
        "MEXT": ["onto-a", "onto-fr"],
        "MVSP": ["mason", "mfg"],
        "OAEI103": ["onto101", "onto103"],
        "OAEI207": ["onto101", "onto207"],
        "OAEI301": ["onto101", "onto301"],
    }

    def calc_size(o1: str, o2: str) -> int:
        """calculate number of interactions"""
        ias = [onto_sizes[o1][k]*onto_sizes[o2][k] for k in ("cls", "ops", "dps")]
        return sum(ias)

    return {k: calc_size(*combos[k]) for k in combos}


def plot_scatter(data: list, output_file: str) -> None:
    # NOTE: this assumes that ontology sizes and timing results are sorted in the same way
    sizes = list(calc_combinations(get_onto_sizes()).values())
    annotes = [a[0] for a in data]
    print(annotes)
    print(sizes)
    avgs = [sum(l[1:])/len(l[1:]) for l in data]
    fig, ax = plt.subplots(figsize=(20/2.54, 10/2.54))
    ax.set_title("Performance by number of comparisons")
    ax.yaxis.grid(True)
    ax.set_xlabel("Number of comparisons")
    ax.set_ylabel("Execution time [s]")
    plt.scatter(sizes, avgs)
    plt.ylim(20, 140)
    for i, txt in enumerate(annotes):
        ax.annotate(txt, (sizes[i], avgs[i]+2.5))
    plt.savefig(output_file)


if __name__ == "__main__":
    boxplot_file = "./timing-boxplot.pdf"
    scatter_file = "./timing-scatter.pdf"
    data_path = "./timing-results.csv"
    data = load_from_csv(data_path)
    data = preprocess_times(data)
    plot_boxplot(data, boxplot_file)
    plot_scatter(data, scatter_file)

