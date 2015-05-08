#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import numpy as np
try:
    from astroquery.vizier import Vizier
except ImportError:
    url = 'https://astroquery.readthedocs.org/'
    raise ImportError('astroquery is needed (pip). More info here: %s' % url)
import argparse
import warnings


def _q2a(lst):
    """
    Convert list of quantities to numpy array
    """
    lst_new = []
    for li in lst:
        li = li.value
        for value in li:
            lst_new.append(value)
    return np.array(lst_new)


def _parser():
    parser = argparse.ArgumentParser(description='Look up an object in VizieR'
                                                 ' and print mean/median'
                                                 ' values of given parameters')
    parser.add_argument('object', help='Object, e.g. HD20010')
    parser.add_argument('-p', '--params',
                        help='List of parameters (Teff, logg, [Fe/H] be'
                             ' default)',
                        nargs='*')
    parser.add_argument('-m', '--method',
                        help='Which method to print values (mean or median).'
                             ' Default is both',
                        choices=['median', 'mean', 'both'],
                        default='both')
    return parser.parse_args()


def vizier_query(object, params=None, method='both'):
    """Give mean/median values of some parameters for an object.
    This script use VizieR for looking up the object.

    :object: The object to query (e.g. HD20010).
    :parama: Extra parameters to look for (default is Teff, logg, __Fe_H_).
    :method: Print median, main or both

    :returns: A dictionary with the parameters

    """

    methods = ('median', 'mean', 'both')
    if method not in methods:
        raise ValueError('method must be one of:', methods)

    print('-' * 34)
    print(' Receiving catalogues from VizieR\n Object: %s' % object)
    print('-' * 34)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cat = Vizier.query_object(object)
    parameters = {'Teff': [], 'logg': [], '__Fe_H_': []}
    if params:
        for param in params:
            parameters[param] = []

    for ci in cat:
        for column in parameters.keys():
            try:
                parameters[column].append(ci[column].quantity)
            except KeyError:
                pass

    for key in parameters.keys():
        pi = parameters[key]
        parameters[key] = _q2a(pi)
        mean = np.nanmean(parameters[key])
        median = np.nanmedian(parameters[key])
        if key.startswith('__'):
            key = '[Fe/H]'
        if method == 'mean':
            print('\n%s:\tMean value: %.2f' % (key, mean))
        elif method == 'median':
            print('\n%s\tMedian value: %.2f' % (key, median))
        else:
            print('\n%s:\tMean value: %.2f' % (key, mean))
            print('%s:\tMedian value: %.2f' % (key, median))

    return parameters


if __name__ == '__main__':
    args = _parser()
    vizier_query(args.object, params=args.params, method=args.method)
