#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import numpy as np
from astropy.io import fits
import argparse
from gooey import Gooey, GooeyParser


@Gooey(program_name='CRIRES spectrum to an 1D spectrum', default_size=(610, 500))
def _parser():
    '''The argparse stuff'''

    parser = GooeyParser(description='CRIRES spectrum to an 1D spectrum')
    parser.add_argument('fname', action='store', widget='FileChooser', help='Input fits file')
    parser.add_argument('--output', default=False,
                        help='Output to this name. If nothing is given, output will be: "wmin-wmax.fits"')
    parser.add_argument('-u', '--unit', default='angstrom',
                        choices=['angstrom', 'nm'],
                        help='The unit of the output wavelength')
    parser.add_argument('-c', '--clobber', default=True, action='store_false',
                        help='Do not overwrite existing files.')
    args = parser.parse_args()
    return args


def _get_wavelength(fname, unit=1):
    '''Get the wavelength from a CRIRES pipeline reduced spectrum.

    Input:
        fname: File name
        unit: 1=Aangstrom, 2=nm
    Output:
        w: Output wavelength
    '''
    d = fits.getdata(fname)
    hdr = fits.getheader(fname)
    I = d['Extracted_OPT']
    wmin, wmax = hdr['ESO INS WLEN MIN'], hdr['ESO INS WLEN MAX']
    if unit == 1:
        return np.linspace(wmin, wmax, len(I), endpoint=True) * 10
    elif unit == 2:
        return np.linspace(wmin, wmax, len(I), endpoint=True)


def main(fname, output=False, unit=1, clobber=True):
    '''Convert the CRIRES spectrum to a 1D spectrum

    Input:
        fname: Fits file of CRIRES spectrum
        output: Name of output file. Default is: "wmin-wmax.fits"
        unit: Unit of wavelength vector (Angstrom is default.)
        clobber: Overwrite existing files
    '''
    I = fits.getdata(fname)
    w = _get_wavelength(fname, unit=unit)
    if not output:
        output = '%i-%i.fits' % (w.min(), w.max())
    else:
        if not output.lower().endswith('.fits'):
            output += '.fits'

    N = len(w)
    hdr = fits.Header()
    hdr["NAXIS1"] = N
    hdr["CDELT1"] = (w[-1]-w[0])/N
    hdr["CRVAL1"] = w[0]

    fits.writeto(output, I['Extracted_OPT'], header=hdr, clobber=clobber)
    print('File writed to: %s' % output)


if __name__ == '__main__':
    args = _parser()
    if args.unit == 'angstrom':
        args.unit = 1
    elif args.unit == 'nm':
        args.unit = 2
    main(args.fname, output=args.output, unit=args.unit, clobber=args.clobber)
