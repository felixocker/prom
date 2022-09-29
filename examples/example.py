#!/usr/bin/env python3
"""
example for demonstrating prom benchmark
"""

import prom
import unittest


def main():
    config = "./config.yml"
    myprom = prom.Prom(config)
    inputs = None
    if myprom.paths[0][1] == "http://www.owl-ontologies.com/mason.owl" and\
       myprom.paths[1][1] == "http://www.ohio.edu/ontologies/manufacturing-capability":
        inputs = ["y"]*31 + ["n"]
    elif myprom.paths[0][1] == "http://example.org/onto-a.owl" and\
         myprom.paths[1][1] == "http://example.org/onto-fr.owl":
        inputs = ["y"]*14
    if inputs:
        with unittest.mock.patch('builtins.input', side_effect=inputs):
            myprom.run_all()
    else:
        myprom.run_all()


if __name__ == "__main__":
    main()
