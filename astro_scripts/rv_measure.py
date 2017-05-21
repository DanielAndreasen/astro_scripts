#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import os
import numpy as np
from astropy.io import fits
import scipy.interpolate as sci
from argparse import ArgumentParser


def ccf_astro(spectrum1, spectrum2, rvmin=0, rvmax=150, drv=1):
    """Make a CCF between 2 spectra and find the RV

    :spectrum1: The stellar spectrum
    :spectrum2: The model, sun or telluric
    :dv: The velocity step
    :returns: The RV shift
    """
    # Calculate the cross correlation
    s = False
    w, f = spectrum1
    tw, tf = spectrum2
    if not len(w) or not len(tw):
        return 0, 0, 0, 0, 0
    c = 299792.458
    drvs = np.arange(rvmin, rvmax, drv)
    cc = np.zeros(len(drvs))
    for i, rv in enumerate(drvs):
        fi = sci.interp1d(tw * (1.0 + rv / c), tf)
        # Shifted template evaluated at location of spectrum
        try:
            fiw = fi(w)
            cc[i] = np.sum(f * fiw)
        except ValueError:
            s = True
            fiw = 0
            cc[i] = 0

    if not np.any(cc):
        return 0, 0, 0, 0, 0

    # Fit the CCF with a gaussian
    cc[cc == 0] = np.mean(cc)
    cc = (cc-min(cc))/(max(cc)-min(cc))
    RV, g = _fit_ccf(drvs, cc)
    return RV, drvs, cc, drvs, g(drvs)


def _fit_ccf(rv, ccf):
    """Fit the CCF with a 1D gaussian
    :rv: The RV vector
    :ccf: The CCF values
    :returns: The RV, and best fit gaussian
    """
    from astropy.modeling import models, fitting
    ampl = 1
    mean = rv[ccf == ampl]
    I = np.where(ccf == ampl)[0][0]

    g_init = models.Gaussian1D(amplitude=ampl, mean=mean, stddev=5)
    fit_g = fitting.LevMarLSQFitter()

    try:
        g = fit_g(g_init, rv[I - 10:I + 10], ccf[I - 10:I + 10])
    except TypeError:
        print('Warning: Not able to fit a gaussian to the CCF')
        return mean, g_init
    RV = g.mean.value
    return RV, g


def nrefrac(wavelength, density=1.0):
    """
    Refactory index by Elden 1953 from vacuum to air.
    """
    wl = np.array(wavelength)

    s2 = (1e4/wl)**2
    n = 1.0 + 6.4328e-5 + (2.94981e-2/(146.0 - s2)) + (2.554e-4/(41. - s2))
    return density * n


def dopplerShift(wvl, flux, v, edgeHandling='firstlast', fill_value=None):
    """Doppler shift a given spectrum.
    Does not interpolate to a new wavelength vector, but does shift it.
    """

    # Shifted wavelength axis
    wlprime = wvl * (1.0 + v / 299792.458)
    return flux, wlprime


def get_wavelength(hdr, convert=False):
    """Return the wavelength vector calculated from the header of a FITS
    file.

    Input
    -----
    hdr : FITS header
      Header from a FITS ('CRVAL1', 'CDELT1', and 'NAXIS1' is required as keywords)
    convert : bool
      If True, multiple the wavelength vector with 10 (nm -> AA)

    Output
    ------
    w : ndarray
      Equidistant wavelength vector
    """
    w0, dw, n = hdr['CRVAL1'], hdr['CDELT1'], hdr['NAXIS1']
    w1 = w0 + dw * n
    w = np.linspace(w0, w1, n, endpoint=False)
    if convert:
        w *= 10
    return w


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
    nre = nrefrac(w_mod)  # Correction for vacuum to air (ground based)
    w_mod = w_mod/nre
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
