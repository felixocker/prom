#!/usr/bin/env python3
"""suppress outputs"""

import os
import sys
from contextlib import contextmanager

@contextmanager
def suppress():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

if __name__ == "__main__":
    print("You can see this")
    with suppress():
        print("You cannot see this")
    print("And you can see this again")
