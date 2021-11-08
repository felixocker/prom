#!/usr/bin/env python3
"""cli for deciding how to cope with inconsistent classes"""

import sys

def main(matches, inconsistencies):
    """iterate over matches and prompt user to confirm"""
    rejected_matches = []
    print("please indicate if a match should be rejected [y(es),n(o),q(uit)]")
    for match in matches:
        for incon in inconsistencies:
            if incon in match[1:3]:
                print(match)
                user_input = input()
                while user_input not in ["y", "n", "q"]:
                    print("invalid choice, please try again")
                    user_input = input()
                if user_input == "y":
                    rejected_matches.append(match)
                elif user_input == "q":
                    print("quit - if you wish to continue restart the integration process")
                    sys.exit(0)
    accepted_matches = [m for m in matches if not m in rejected_matches]
    return accepted_matches

if __name__ == "__main__":
    example_matches = [["class", "iri1a", "iri1b", "relation1", .9],\
                       ["op", "iri2a", "iri2b", "relation2", .5],\
                       ["dp", "iri3a", "iri3b", "relation3", .7],\
                       ["class", "iri4a", "iri4b", "relation4", .2]]
    inconsistencies = ["iri1a", "iri4b"]
    accepted_matches = main(example_matches, inconsistencies)
    print("accepted matches are:")
    print(*accepted_matches, sep="\n")
