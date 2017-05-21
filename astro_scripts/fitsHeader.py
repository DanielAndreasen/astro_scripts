#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division
from astropy.io import fits
from pydoc import pager
import argparse


def _parser():
    parser = argparse.ArgumentParser(description='View the header of a fits file')
    parser.add_argument('input', help='File name of fits file', nargs='+')
    parser.add_argument('-key', help='Look up a given key (case insensitive)', default=None)
    return parser.parse_args()


def main():
    args = _parser()

    if args.key:
        args.key = args.key.lower()
        for fname in args.input:
            h = fits.getheader(fname)
            h.keys = map(str.lower, h.keys())
            try:
                print '%s:  %s' % (fname, h[args.key])
            except KeyError:
                print 'Key was not found in: %s' % fname
                pass
    else:
        h = fits.getheader(args.input[0])
        string = '\n'.join("{!s} : {!r}".format(key, val) for (key, val) in h.items())
        pager(string)


if __name__ == '__main__':
    main()
