#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
This small script converts an array with wavelength, excitation potential,
element, log gf, and EW to a MOOG file for abfind.
"""

# My imports
from __future__ import division, print_function
import os
import numpy as np
import argparse


def numpy2moog_ew(arr, output=None, header=None):
    """Script to convert a numpy array to the MOOG format for abfind.

    :arr: Either the name of an inputfile or an numpy array
    :output: output filename. Needs to be specified if arr is an array
    :header: Header of the MOOG file (1 line only)
    """
    if not header:  # Default header
        header = 'Wavelength\tEle\t  excit\t  log gf\t\t\t EW'

    if isinstance(arr, str):
        if not output:  # Call the output file for .moog
            tmp = arr.rpartition('.')
            if tmp[0]:
                output = '%s.moog' % tmp[0]
            else:
                output = '%s.moog' % arr
        try:
            data = np.loadtxt(arr, skiprows=header.count('\n') + 1)
        except ValueError:
            print('Was not able to load %s' % arr)
            raise
    elif isinstance(arr, list):
        data = np.array(arr, dtype=str)
        data = np.reshape(data, (1, 5))
        if not output:
            print('Need to specify an output')
            raise SystemExit
    else:
        print('Unexpected datatype: %s' % type(arr))
        raise SystemExit

    fmt_ = ('%9.2f', '%7.1f', '%11.2f', '%10.3f', '%27.1f')
    np.savetxt(output, data, fmt=fmt_, header=header)
    print('Output file: %s' % output)


def numpy2moog_synth(arr, output=None, header=None):
    """Script to convert a numpy array to the MOOG format for abfind.
    Most of this script is from:
    http://stackoverflow.com/questions/28885617/read-and-save-data-file-with-variable-number-of-columns-in-python
    """
    import pandas as pd
    if not header:  # Default header
        header = 'Wavelength\t   Ele\t  excit\t  log gf\t   D0'
    if not output:  # Call the output file for .moog
        tmp = arr.rpartition('.')
        if tmp[0]:
            output = '%s.moog' % tmp[0]
        else:
            output = '%s.moog' % arr

    df = pd.read_csv(arr, sep='\s+')

    formatters = ['{: >8.3f}'.format, '{: >6.1f}'.format,
                  '{: >8.2f}'.format, '{: >13.3f}'.format,
                  lambda x: ' '*16 if np.isnan(x) else '{: >11.2f}'.format(x)]
    lines = df.to_string(index=False, header=header, formatters=formatters)

    # Write output and remove trailing whitespaces
    with open(output, 'w') as f:
        for line in lines.split('\n'):
            f.write(line.rstrip() + '\n')


def vald2numpy(input, output=None):
    """Converts the VALD output to a numpy array with only the name,
    wavelength, excitation potential, and log gf
    """

    try:
        from periodic.table import element
    except ImportError:
        print('Could not import periodic')
        print('Install with: pip install periodic')
        raise SystemExit

    if not output:  # Call the output file for .moog
        tmp = input.rpartition('.')
        if tmp[0]:
            output = '%s.npy' % tmp[0]
        else:
            output = '%s.npy' % input

    with open(input, 'r') as lines:
        newFile = ''
        for line in lines:
            if line.startswith('#') or line.startswith('*'):
                pass
            else:
                newFile += line
    with open(input, 'w') as f:
        f.write(newFile)

    f = np.loadtxt(input,
                   dtype={
                       'names': ('elements', 'w', 'excit', 'loggf'),
                       'formats': ('S4', 'f4', 'f4', 'f4')
                   },
                   comments='#',
                   delimiter=',',
                   usecols=(0, 1, 2, 3))

    mol1 = ['CH', 'OH', 'C2', 'CN', 'CO']
    mol2 = ['106', '108', '606', '607', '608']
    mol3 = [3.47, 4.395, 6.25, 7.5, 11.09]
    mol = dict(zip(mol1, [m for m in zip(mol2, mol3)]))

    numpy_out = 'Wavelength\tEle\tExcit\tloggf\t\tD0\n'
    for e, w, ex, l in zip(f['elements'], f['w'], f['excit'], f['loggf']):
        w = str(round(w, 3)).ljust(9, '0')
        iso = e[-1]
        e = e[:-1].strip(' ')
        if e in mol.keys():
            ele_moog = '%s.%s' % (mol[e][0], str(int(iso) - 1))
            l = str(l).ljust(6, '0')
            z = '\t'.join([w, ele_moog, str(ex), l, str(mol[e][1])]) + '\n'
        else:
            try:
                t = element(e)
                ele_moog = str(t.atomic) + '.' + str(int(iso) - 1)
                l = str(l).ljust(6, '0')
                z = '\t'.join([w, ele_moog, str(ex), l]) + '\n'
            except AttributeError:
                print('The following element does not exist in the dictionary'
                      'yet: %s' % e)
                raise

        numpy_out += z

    with open(output, 'w') as f:
        f.write(numpy_out)
    print('Output file: %s' % output)


def _parser():
    """Take care of all the argparse stuff.

    :returns: the args
    """
    parser = argparse.ArgumentParser(description='Numpy to moog readable'
                                     'converter for the abfind routine.')
    parser.add_argument('input', help='Input numpy file')
    parser.add_argument('-m', '--mode',
                        default='ew',
                        help='Which function to evoke [ew|synth|asc].'
                        'ew: converts an ASCII array to a MOOG EW array.\n'
                        'synth: converts an ASCII array to a MOOG\n'
                        'synthesis array.\n'
                        'asc: converts a VALD array to a ASCII array.')

    parser.add_argument('-o', '--output',
                        default=None,
                        help='Output file, if not an extension is specified'
                        ' will be .moog or .vald depending on the mode.')

    parser.add_argument('-H', '--header',
                        default=None,
                        help='The header for the file. If not given, a'
                        ' standard header will be provided')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = _parser()

    # Always add a .moog to the output if none extension is provided.
    if args.mode == 'ew':
        numpy2moog_ew(args.input, args.output, args.header)

    if args.mode == 'synth':
        numpy2moog_synth(args.input, args.output, args.header)

    if args.mode == 'asc':
        vald2numpy(args.input, args.output)
