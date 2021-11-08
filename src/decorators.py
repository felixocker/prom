#!/usr/bin/env python3
"""generic decorators"""


import functools
import timeit


def timeme(func):
    @functools.wraps(func)
    def timeme_wrapper(*args, **kwargs):
        tic = timeit.default_timer()
        res = func(*args, **kwargs)
        toc = timeit.default_timer()
        print(f"execution time for function '{func.__name__}': {toc-tic:.6f}s")
        return res
    return timeme_wrapper

