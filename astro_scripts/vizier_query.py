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
    parser.add_argument('object', help='Object, e.g. HD20010', nargs='+')
    parser.add_argument('-p', '--params', default=True, action='store_true',
                        help='List of parameters (Teff, logg, [Fe/H] be default)')
    parser.add_argument('-m', '--method', choices=['median', 'mean', 'both'], default='both',
                        help='Which method to print values (mean or median). Default is both')
    parser.add_argument('-c', '--coordinate', default=False, action='store_true',
                        help='Return the RA and DEC (format for NOT\'s visibility plot)')
    return parser.parse_args()


def vizier_query(obj, params=True, method='both', coordinate=False):
    """Give mean/median values of some parameters for an object.
    This script use VizieR for looking up the object.

    :obj: The object to query (e.g. HD20010).
    :parama: Extra parameters to look for (default is Teff, logg, __Fe_H_).
    :method: Print median, main or both

    :returns: A dictionary with the parameters
    """

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cat = Vizier.query_object(obj)

    if coordinate:
        for c in cat:
            try:
                ra = c['RAJ2000'][0]
                dec = c['DEJ2000'][0]
            except KeyError:
                ra = 0
            if ra != 0:
                break
        print('\n\n%s %s %s' % (obj, ra, dec))
    else:
        print('\n\nObject: %s' % obj)

    parameters = {'Teff': [], 'logg': [], '__Fe_H_': []}
    if params:
        params=['Teff', 'logg', '__Fe_H_']
        for param in params:
            parameters[param] = []

        for ci in cat:
            for column in parameters.keys():
                try:
                    parameters[column].append(ci[column].quantity)
                except (TypeError, KeyError):
                    pass

        for key in parameters.keys():
            pi = parameters[key]
            parameters[key] = _q2a(pi)
            if len(parameters[key]):
                mean = round(np.nanmean(parameters[key]), 2)
                median = round(np.nanmedian(parameters[key]), 2)
            else:
                mean = 'Not available'
                median = 'Not available'

            if key.startswith('__'):
                key = '[Fe/H]'
            if method == 'mean':
                print('\n%s:\tMean value: %s' % (key, mean))
            elif method == 'median':
                print('\n%s\tMedian value: %s' % (key, median))
            else:
                print('\n%s:\tMean value: %s' % (key, mean))
                print('%s:\tMedian value: %s' % (key, median))

    return parameters, cat


def main():
    args = _parser()
    stars = args.object[0].split(' ')
    if len(stars) == 1:
        stars = args.object[0].split(',')
    for star in stars:
        vizier_query(star, params=args.params, method=args.method, coordinate=args.coordinate)


if __name__ == '__main__':
    main()
