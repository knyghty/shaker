#!/usr/bin/env python
import importlib

import pkg2

from mypkg.nested import n_a, n_b


dunder = __import__("mypkg.dunder", fromlist=("greet",))


def main():
    from mypkg import mymodule

    il_dunder = importlib.__import__("il.dunder", fromlist=("something_else",))
    if True:
        il_im = importlib.import_module("il.im")

    print(dunder.greet())
    n_b.print_foo()
    n_a.print_bar()
    print(il_im.something())
    print(il_dunder.something_else())
    print(f"Version: {pkg2.VERSION}")
    print(mymodule.add(1, 2))
    print(mymodule.add_mul(1, 2, 3))


if __name__ == "__main__":
    main()
