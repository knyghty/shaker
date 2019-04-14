import collections

from .relative_import import mul


def add(x, y):
    counter = collections.Counter()
    counter["sum"] = x + y
    return counter["sum"]


def add_mul(x, y, z):
    return mul(add(x, y), z)
