#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
import argparse
import gzip
import os


def _parser():
    parser = argparse.ArgumentParser(description='Prepare the data downloaded '
                                     'from VALD.')
    parser.add_argument('input', help='input compressed file', type=str)
    parser.add_argument('-o', '--output',
                        help='Optional output',
                        default=False, type=str)
    return parser.parse_args()


def main(inp, output=False):

    if not os.path.isfile(inp):
        raise IOError('File: {} does not exists'.format(inp))

    fname = inp.rpartition('.')[0]
    if not output:
        output = '{}.dat'.format(fname)

    fout = ''
    with gzip.open(inp, 'r') as lines:
        for i, line in enumerate(lines):
            if i < 2:
                fout += '# {}'.format(line.replace("'", ''))
            else:
                fout += line.replace("'", '')
            if 'References' in line:
                break

    with open(output, 'w') as fo:
        fo.write(fout)


def runner():
    args = _parser()
    inp, output = args.input, args.output
    main(inp, output)


if __name__ == '__main__':
    runner()
