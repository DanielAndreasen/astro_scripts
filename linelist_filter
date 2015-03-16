#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import numpy as np
import argparse


def ll_filter(fname, col, limit, sign, element):
    data = np.loadtxt(fname, skiprows=1, unpack=True)
    if sign > 0 and element:
        i = (data[col] > limit) | (data[1] == element)
    elif sign < 0 and element:
        i = (data[col] < limit) | (data[1] == element)
    elif sign > 0 and not element:
        i = data[col] > limit
    elif sign < 0 and not element:
        i = data[col] < limit

    return data[:, i].T

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter the linelist by a\
    column and an upper limit')
    parser.add_argument('input', help='Input linelist')
    parser.add_argument('col', help='Column to be sorted (starting at 0)',
                        type=int)
    parser.add_argument('limit', help='The upper limit on the column',
                        type=float)
    parser.add_argument('-o', '--output', help='The output linelist',
                        default=None)
    parser.add_argument('-s', '--sign', help='Positive (default) for including\
                                              values above, negative for\
                                              including values below',
                        default=1, type=int)
    parser.add_argument('-e', '--element', help='If value is 26.1 then FeII\
                                                 lines will not be removed.',
                        default=None, type=float)
    args = parser.parse_args()

    fname = args.input
    col = args.col
    limit = args.limit
    sign = args.sign
    element = args.element
    if not args.output:
        t = fname.split('.')
        t[0] += '_filtered_%s_%s' % (col, limit)
        output = '.'.join(t)
    else:
        output = args.output

    data = ll_filter(fname, col, limit, sign, element)
    print('Result saved in %s' % output)
    np.savetxt(output, data, fmt=('%9.3f', '%10.1f', '%9.2f', '%9.3f',
                                  '%28.1f'),
               header='Wavelength\tEle\t  excit\t  log gf\t\t\t EW',
               comments='')
