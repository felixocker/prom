#!/usr/bin/env python3
"""check for elements in 4-tuple if similarity value is acceptable"""

BOUNDARY = .9
TEST_TUPLE = [["a", "b", "c", "d", .7], ["d", "e", "f", "g", .99]]

def check_boundary(tuples, position, boundary=BOUNDARY):
    """remove all elements w an inacceptable similarity measure"""
    matches = []
    matches = list(filter(lambda x: x[position] >= boundary, tuples))
    return matches

if __name__ == "__main__":
    print(check_boundary(TEST_TUPLE, 4))
