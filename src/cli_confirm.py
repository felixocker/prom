#!/usr/bin/env python3
"""cli for confirming matches"""

import sys

def main(matches, lower_threshold, upper_threshold):
    """iterate over matches and prompt user to confirm"""
    accepted_matches = []
    print("please assess the following matches [y(es),n(o),q(uit)]")
    for match in matches:
        if match[-1] >= upper_threshold:
            accepted_matches.append(match)
        if lower_threshold <= match[-1] < upper_threshold:
            print(match)
            user_input = input()
            while user_input not in ["y", "n", "q"]:
                print("invalid choice, please try again")
                user_input = input()
            if user_input == "y":
                accepted_matches.append(match)
            elif user_input == "q":
                print("quit - if you wish to continue restart the integration process")
                sys.exit(0)
    return accepted_matches

if __name__ == "__main__":
    lower_threshold = .4
    upper_threshold = .6
    example_matches = [["class", "iri1a", "iri1b", "relation1", .9],\
                       ["op", "iri2a", "iri2b", "relation2", .5],\
                       ["dp", "iri3a", "iri3b", "relation3", .7],\
                       ["class", "iri4a", "iri4b", "relation4", .2]]
    accepted_matches = main(example_matches, lower_threshold, upper_threshold)
    print("accepted matches are:")
    print(*accepted_matches, sep="\n")
