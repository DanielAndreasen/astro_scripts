#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division
from astropy.io import fits
from pydoc import pager
import argparse


def _parser():
    parser = argparse.ArgumentParser(description='View the header of a fits file')
    parser.add_argument('input', help='File name of fits file')
    parser.add_argument('-key', help='Look up a given key (case insensitive)', default=None)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parser()
    h = fits.getheader(args.input)
    h.keys = map(str.lower, h.keys())

    if args.key:
        args.key = args.key.lower()
        try:
            print h[args.key]
        except KeyError:
            raise KeyError('Key was not found')
    else:
        string = '\n'.join("{!s} : {!r}".format(key, val) for (key, val) in h.items())
        pager(string)
