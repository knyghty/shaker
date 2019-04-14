#!/usr/bin/env python
import argparse
import pprint

from shaker import shake


parser = argparse.ArgumentParser(description="Find some imports")
parser.add_argument("infile", type=str, help="path to the entry point")
args = parser.parse_args()


def main():
    pprint.pprint(shake.shake(args.infile))


if __name__ == '__main__':
    main()
