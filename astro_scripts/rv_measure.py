#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import os
import numpy as np
from astropy.io import fits
from argparse import ArgumentParser
from .utils import ccf_astro, vac2air, dopplerShift, get_wavelength


def _parser():
    """Take care of all the CLI/GUI stuff.
    """
    parser = ArgumentParser(description='Plot FITS spectra effortless')
    parser.add_argument('fname',
                        action='store',
                        help='Input fits file')
    parser.add_argument('model',
                        default=False,
                        help='If not the Sun shoul be used as a model, put'
                        ' the model here (only support BT-Settl for the'
                        ' moment)')
    parser.add_argument('--ftype', help='Select which type the fits file is',
                        choices=['1D', 'CRIRES', 'GIANO', 'UVES'], default='1D')
    return parser.parse_args()


def main(fname, model, ftype='1D'):
    """Plot a fits file with extensive options

    :fname: Input spectra
    :model: Model spectrum
    :ftype: Type of fits file (1D, CRIRES, GIANO)
    """

    path = os.path.expanduser('~/.plotfits/')
    pathwave = os.path.join(path, 'WAVE_PHOENIX-ACES-AGSS-COND-2011.fits')

    if ftype == '1D':
        I = fits.getdata(fname)
        hdr = fits.getheader(fname)
        w = get_wavelength(hdr)
    elif ftype == 'CRIRES':
        d = fits.getdata(fname, fitsext)
        hdr = fits.getheader(fname, fitsext)
        I = d['Extracted_OPT']
        w = d['Wavelength']*10
    elif ftype == 'GIANO':
        d = fits.getdata(fname)
        I = d[order - 32]  # 32 is the first order
        wd = np.loadtxt(pathGIANO)
        w0, w1 = wd[wd[:, 0] == order][0][1:]
        w = np.linspace(w0, w1, len(I), endpoint=True)
    elif ftype == 'UVES':
        raise NotImplementedError('Please be patient. Not quite there yet')

    if np.median(I) != 0:
        I /= np.median(I)
    else:
        I /= I.max()
    # Normalization (use first 50 points below 1.2 as constant continuum)
    maxes = I[(I < 1.2)].argsort()[-50:][::-1]
    I /= np.median(I[maxes])
    I[I<0] = 0
    dw = 10  # Some extra coverage for RV shifts

    w0, w1 = w[0] - dw, w[-1] + dw

    I_mod = fits.getdata(model)
    hdr = fits.getheader(model)
    if 'WAVE' in hdr.keys():  # Dealing with PHOENIX model
        w_mod = fits.getdata(pathwave)
    else:
        w_mod = get_wavelength(hdr)
    w_mod = vac2air(w_mod)  # Correction for vacuum to air (ground based)
    i = (w_mod > w0) & (w_mod < w1)
    w_mod = w_mod[i]
    I_mod = I_mod[i]
    if len(w_mod) > 0:
        I_mod /= np.median(I_mod)
        # Normalization (use first 50 points below 1.2 as continuum)
        maxes = I_mod[(I_mod < 1.2)].argsort()[-50:][::-1]
        I_mod /= np.median(I_mod[maxes])

    rvs = {}
    print('Calculating the CCF for: %s' % fname)
    rv1, r_mod, c_mod, x_mod, y_mod = ccf_astro((w, -I + 1), (w_mod, -I_mod + 1))
    print('Shifting model spectrum...')
    I_mod, w_mod = dopplerShift(w_mod, I_mod, v=rv1, fill_value=0.95)
    rvs['model'] = rv1
    print('RV for {0} is {1}km/s'.format(fname.replace('.fits', ''), round(rvs['model'], 2)))
    return rv1, r_mod, c_mod, x_mod, y_mod


def runner():
    args = vars(_parser())
    fname = args.pop('fname')
    model = args.pop('model')
    ftype = args.pop('ftype')
    main(fname, model, ftype)


if __name__ == '__main__':
    runner()
