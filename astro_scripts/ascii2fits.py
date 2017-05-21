#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import print_function
from astropy.io import fits
import numpy as np
from scipy.interpolate import interp1d
import argparse


def vac2air(wavelength, density=1.0):
    """
    Refactory index by Elden 1953 from vacuum to air.
    """
    wl = np.array(wavelength)

    s2 = (1e4/wl)**2
    n = 1.0 + 6.4328e-5 + (2.94981e-2/(146.0 - s2)) + (2.554e-4/(41. - s2))
    return wavelength/(density * n)


def convert2fits(fname, fout=None, dA=0.01, unit='a', read=True, vac=None):
    """Convert a 2-column ASCII to fits format for splot@IRAF or ARES.

    Inputs
    ------
    fname : str
      File name of ASCII. First column is wavelength and second column is
      intensity.
    fout : str (default: None)
      Output name. By default it returns the output is the ASCII name with
      a fits extension.
    dA : float (default: 0.01)
      The wavelength step in Angstrom.
    unit : str (default: a)
      The unit to convert from to Angstrom.
    read : bool (default: True)
      If True, the data will be read from file, fname. If False, fname
      should contain the wavelength and flux vector
    vac : bool (default: None)
      If True convert the wavelength vector from vacuum to air

    Output
    ------
    fout : fits
      Spectrum saved to fout in 1D format.
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
        flux = flux[::-1]
    elif unit == 'mm':  # micro meters
        ll *= 10000

    if vac:
        ll = vac2air(ll)

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
                        default='a', choices=['aa', 'nm', 'cm', 'mm'])
    parser.add_argument('-v', '--vacuum', action='store_true', default=False,
                        help='If input spectrum is in vacuum, convert to air wavelengths')
    args = parser.parse_args()
    return args


def main():
    args = _parser()

    convert2fits(args.input, fout=args.output, dA=args.delta,
                 unit=args.unit, vac=args.vacuum)


if __name__ == '__main__':
    main()
