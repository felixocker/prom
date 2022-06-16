#!/usr/bin/env python3
"""
plot benchmark results from csv (ods export)
"""

import csv
import matplotlib.pyplot as plt
import numpy as np


def load_from_csv(path: str) -> list:
    with open(path) as f:
        reader = csv.reader(f)
        data = list(reader)
    return data


def add_linebreak(label: str) -> str:
    if len(label) > 12 and len(label.split()) > 1:
        parts = label.split()
        label = " ".join(parts[:2]) + "\n" + " ".join(parts[2:])
    return label


def plot_from_csv(data: list, output_file: str) -> None:
    number_matchers = 6
    width = .12
    color_dict = {"dark grey": "#999999", "lighter blue": "#98c6ea", "dark blue": "#005293",\
                  "light grey": "#dad7cb", "light blue": "#64a0c8", "tum blue": "#0065bd",\
                  "orange": "#e37222", "green": "#a2ad00"}
    colors = list(color_dict.values())
    x = np.arange(len(data[0]) - 1)
    fig, axs = plt.subplots(3, sharex=True, sharey=True, figsize=(10, 5))
    r1 = range(1, 1+number_matchers)
    r2 = range(3+number_matchers, 3+2*number_matchers)
    r3 = range(5+2*number_matchers, 5+3*number_matchers)
    for ci, ri in enumerate([r1, r2, r3]):
        for c, r in enumerate(ri):
            br = axs[ci].bar(x - (number_matchers-1)/2*width + width*c, [float(i) for i in data[r][1:]],\
                             width, color=colors[c], label=data[r][0])
        axs[ci].set_ylabel(data[ri[0]-1][0])
    fig.legend(axs[0].get_children(),
               labels=[data[l][0] for l in range(1,number_matchers+1)],
               loc="upper center",
               ncol=6,
               title="Frameworks",
               borderaxespad=.2)
    plt.xticks(x, [add_linebreak(l) for l in data[0][1:]], rotation=0)
    plt.ylim(0, 1.0)
    plt.xlabel("Data sets")
    plt.savefig(output_file, bbox_inches='tight')


if __name__ == "__main__":
    output_file = './benchmark.pdf'
    csv_data = load_from_csv("./benchmark-results.csv")
    plot_from_csv(csv_data, output_file)

