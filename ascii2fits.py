#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import print_function
from astropy.io import fits
import numpy as np
from scipy.interpolate import interp1d
import argparse


def convert2fits(fname, fout=None, dA=0.01, unit='a', read=True):
    """Convert a 2-column ASCII to fits format for splot@IRAF or ARES.

    :fname: File name of ASCII. First column is wavelength and second column is
    intensity.
    :fout: Output name. By default it returns the output is the ASCII name with
    a fits extension.
    :dA: The wavelength step. 0.01 Angstrom by default.
    :read: If True, the data will be read from file, fname. If False, fname
    should contain the wavelength and flux vector
    """

    if not fout:
        fout = fname.rpartition('.')[0] + '.fits'

    if read:
        ll, flux = np.loadtxt(fname, usecols=(0, 1), unpack=True)
    else:
        ll, flux = fname
    if unit == 'nn':  # nano meters
        ll *= 10
    elif unit == 'cm':  # Inverse centimeters
        ll = 10E7/ll
        ll = ll[::-1]
    N = int((ll[-1] - ll[0]) / dA)

    flux_int_func = interp1d(ll, flux, kind='linear')
    ll_int = np.arange(N) * dA + ll[0]
    flux_int = flux_int_func(ll_int)
    prihdr = fits.Header()
    prihdr["NAXIS1"] = N
    prihdr["CDELT1"] = dA
    prihdr["CRVAL1"] = ll[0]

    fits.writeto(fout, flux_int, prihdr, clobber=True)


def _parser():
    parser = argparse.ArgumentParser(description='Convert a 2-column ASCII '
                                     'with wavelength and intensity to a 1D '
                                     'spectra for splot@IRAF or ARES')
    parser.add_argument('input', help='File name of ASCII file')
    parser.add_argument('-o', '--output',
                        help='File name of output. Default'
                        ' is the ASCII name with a .fits'
                        ' extension',
                        default=None)
    parser.add_argument('-d', '--delta',
                        help='Wavelength step (default: 0.01A)',
                        default=0.01,
                        type=float)
    parser.add_argument('-u', '--unit',
                        help='Unit of wavelength vector (default: AA)',
                        default='a', choices=['aa', 'nm', 'cm'])
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = _parser()

    convert2fits(args.input, args.output, args.delta, args.unit)
