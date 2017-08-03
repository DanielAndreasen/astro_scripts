from __future__ import division, print_function
import numpy as np
import scipy.interpolate as sci


def ccf_astro(spectrum1, spectrum2, rvmin=0, rvmax=150, drv=1):
    """Make a CCF between 2 spectra and find the RV

    :spectrum1: The stellar spectrum
    :spectrum2: The model, sun or telluric
    :dv: The velocity step
    :returns: The RV shift
    """
    # Calculate the cross correlation
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


def _nrefrac(wavelength, density=1.0):
    """
    Refactory index by Elden 1953 from vacuum to air.
    """
    wl = np.array(wavelength)

    s2 = (1e4/wl)**2
    n = 1.0 + 6.4328e-5 + (2.94981e-2/(146.0 - s2)) + (2.554e-4/(41. - s2))
    return density * n


def vac2air(wavelength, density=1.0):
    """
    Refactory index by Elden 1953 from vacuum to air.
    """
    return wavelength/_nrefrac(wavelength, density)


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
