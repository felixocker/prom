#!/usr/bin/env python3
"""
process data from onto_data.txt for LaTeX table
"""


def process_and_print(input_file="./onto_data.txt") -> None:
    with open(input_file, "r") as f:
        data = f.readlines()[2:10]
    r = [l.strip().split(",") for l in data]
    # change order to: a, fr, mason, mfg, 101, 103, 207, 301
    rc: list = []
    for i in (6, 7, 4, 5, 0, 1, 2, 3):
        rc.append(r[i])
    # rotate right
    rr = list(zip(*rc))
    # print table
    fr = ["\textbf{" + e + "}" for e in rr[0]]
    print(repr(" & ".join(fr) + " \\"))
    print("\hline")
    for row in rr[1:]:
        print(repr(" & ".join(row) + " \\"))
        print("\hline")


if __name__ == "__main__":
    process_and_print()
