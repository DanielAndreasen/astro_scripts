#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from . import matplotlibcfg
from astropy.io import fits
from PyAstronomy import pyasl
import argparse
try:
    import lineid_plot
    lineidImport = True
except ImportError:
    lineidImport = False
    print('Install lineid_plot (pip install lineid_plot) for more functionality.')
from .utils import ccf_astro, vac2air, dopplerShift, get_wavelength


def _download_spec(fout):
    """
    Download a spectrum from my personal web page
    """
    import requests
    spec = fout.rpartition('/')[-1]
    url = 'http://www.astro.up.pt/~dandreasen/%s' % spec
    spectrum = requests.get(url)
    with open(fout, 'w') as file:
        file.write(spectrum.content)


class Cursor:
    """Get a crosshair at the cursor's position

    The code is from here:
    http://matplotlib.org/examples/pylab_examples/cursor_demo.html
    """

    def __init__(self, ax):
        self._ax = ax
        self.lx = ax.axhline(color='C0', lw=2, alpha=0.7)
        self.ly = ax.axvline(color='C0', lw=2, alpha=0.7)

    def mouse_move(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        plt.draw()


def _parser():
    """Take care of all the CLI/GUI stuff.
    """
    parser = argparse.ArgumentParser(description='Plot FITS spectra effortless')
    parser.add_argument('fname',
                        action='store',
                        help='Input fits file', metavar='Fits file')
    parser.add_argument('-m', '--model',
                        default=False,
                        help='If not the Sun shoul be used as a model, put'
                        ' the model here (only support BT-Settl for the'
                        ' moment)', metavar='Model atmosphere')
    path_lines = os.path.join(os.path.expanduser('~/.plotfits/'), 'linelist.moog')
    parser.add_argument('--linelist',
                        default=path_lines,
                        help='Linelist with 1 line header and wavelength in 1st col', metavar='Line list')

    parser.add_argument('-s', '--sun',
                        help='Over plot solar spectrum',
                        action='store_true')
    parser.add_argument('-t', '--telluric',
                        help='Over plot telluric spectrum',
                        action='store_true')
    parser.add_argument('-r', '--rv',
                        help='RV shift to observed spectra in km/s',
                        default=False,
                        type=float)
    parser.add_argument('-r1', '--rv1',
                        help='RV shift to model/solar spectrum in km/s',
                        default=False,
                        type=float)
    parser.add_argument('-r2', '--rv2',
                        help='RV shift to telluric spectra in km/s',
                        default=False,
                        type=float)
    parser.add_argument('-l', '--lines',
                        help='Lines to plot on top (multiple lines is an'
                        ' option). If multiple lines needs to be plotted, then'
                        ' separate with a space',
                        default=False, type=float, nargs='+', metavar='Atomic lines')
    parser.add_argument('-c', '--ccf',
                        default='none',
                        choices=['none', 'sun', 'model', 'telluric', 'both'],
                        help='Calculate the CCF for Sun/model or tellurics or both.')
    parser.add_argument('--ftype', help='Select which type the fits file is',
                        choices=['1D', 'CRIRES', 'GIANO', 'UVES'], default='1D',
                        metavar='Instrument')
    parser.add_argument('--fitsext', help='Select fits extention for CRIRES',
                        choices=map(str, range(1, 5)), default='1', metavar='FITS extention')
    parser.add_argument('--order', help='Select which GIANO order to be investigated',
                        choices=map(str, range(32, 81)), default='77', metavar='GIANO order')
    parser.add_argument('--convert', help='Convert wavelength from nm to AA',
                        action='store_true')
    parser.add_argument('--resolution', help='Instrumental resolution, used to broaden model atmosphere.',
                        default=False, type=int)
    parser.add_argument('--nolines', help='Remove lines from the line list',
                        default=False, action='store_true')
    return parser.parse_args()


def main(fname, lines=False, linelist=False,
         model=False, telluric=False, sun=False,
         rv=False, rv1=False, rv2=False, ccf='none', ftype='1D',
         fitsext='0', order='77', convert=False, resolution=False,
         nolines=False):
    """Plot a fits file with extensive options

    :fname: Input spectra
    :lines: Absorption lines
    :linelist: A file with the lines
    :model: Model spectrum
    :telluric: Telluric spectrum
    :sun: Solar spectrum
    :rv: RV of input spectrum
    :rv1: RV of Solar/model spectrum
    :rv2: RV of telluric spectrum
    :ccf: Calculate CCF (sun, model, telluric, both)
    :ftype: Type of fits file (1D, CRIRES, GIANO)
    :fitsext: Slecet fits extention to use (0,1,2,3,4)
    :returns: RV if CCF have been calculated
    """
    print('\n-----------------------------------')
    path = os.path.expanduser('~/.plotfits/')
    pathsun = os.path.join(path, 'solarspectrum_01.fits')
    pathtel = os.path.join(path, 'telluric_NIR.fits')
    pathwave = os.path.join(path, 'WAVE_PHOENIX-ACES-AGSS-COND-2011.fits')
    pathGIANO = os.path.join(path, 'wavelength_GIANO.dat')
    if not os.path.isdir(path):
        os.mkdir(path)
        print('Created: %s' % path)
    if sun and (not os.path.isfile(pathsun)):
        print('Downloading solar spectrum...')
        _download_spec(pathsun)
    if telluric and (not os.path.isfile(pathtel)):
        print('Downloading telluric spectrum...')
        _download_spec(pathtel)
    if model and (not os.path.isfile(pathwave)):
        print('Downloading wavelength vector for model...')
        import urllib
        url = 'ftp://phoenix.astro.physik.uni-goettingen.de/HiResFITS//WAVE_PHOENIX-ACES-AGSS-COND-2011.fits'
        urllib.urlretrieve(url, pathwave)

    fitsext = int(fitsext)
    order = int(order)

    if ftype == '1D':
        I = fits.getdata(fname)
        hdr = fits.getheader(fname)
        w = get_wavelength(hdr, convert=convert)
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
        # d = fits.getdata(fname)
        # I = d['']

    if np.median(I) != 0:
        I /= np.median(I)
    else:
        I /= I.max()
    # Normalization (use first 50 points below 1.2 as constant continuum)
    maxes = I[(I < 1.2)].argsort()[-50:][::-1]
    I /= np.median(I[maxes])
    I[I<0] = 0
    dw = 10  # Some extra coverage for RV shifts

    if rv:
        I, w = dopplerShift(wvl=w, flux=I, v=rv)
    w0, w1 = w[0] - dw, w[-1] + dw

    if sun and not model:
        I_sun = fits.getdata(pathsun)
        hdr = fits.getheader(pathsun)
        w_sun = get_wavelength(hdr)
        i = (w_sun > w0) & (w_sun < w1)
        w_sun = w_sun[i]
        I_sun = I_sun[i]
        if len(w_sun) > 0:
            I_sun /= np.median(I_sun)
            if ccf in ['sun', 'both'] and rv1:
                print('Warning: RV set for Sun. Calculate RV with CCF')
            if rv1 and ccf not in ['sun', 'both']:
                I_sun, w_sun = dopplerShift(wvl=w_sun, flux=I_sun, v=rv1)
        else:
            print('Warning: Solar spectrum not available in wavelength range.')
            sun = False
    elif sun and model:
        print('Warning: Both solar spectrum and a model spectrum are selected. Using model spectrum.')
        sun = False

    if model:
        I_mod = fits.getdata(model)
        hdr = fits.getheader(model)
        if 'WAVE' in hdr.keys():
            w_mod = fits.getdata(pathwave)
        else:
            w_mod = get_wavelength(hdr)
        w_mod = vac2air(w_mod)  # Correction for vacuum to air (ground based)
        i = (w_mod > w0) & (w_mod < w1)
        w_mod = w_mod[i]
        I_mod = I_mod[i]
        if len(w_mod) > 0:
            if resolution:
                I_mod = pyasl.instrBroadGaussFast(w_mod, I_mod, resolution, edgeHandling="firstlast", fullout=False, maxsig=None)
            # https://phoenix.ens-lyon.fr/Grids/FORMAT
            # I_mod = 10 ** (I_mod-8.0)
            I_mod /= np.median(I_mod)
            # Normalization (use first 50 points below 1.2 as continuum)
            maxes = I_mod[(I_mod < 1.2)].argsort()[-50:][::-1]
            I_mod /= np.median(I_mod[maxes])
            if ccf in ['model', 'both'] and rv1:
                print('Warning: RV set for model. Calculate RV with CCF')
            if rv1 and ccf not in ['model', 'both']:
                I_mod, w_mod = dopplerShift(wvl=w_mod, flux=I_mod, v=rv1)
        else:
            print('Warning: Model spectrum not available in wavelength range.')
            model = False

    if telluric:
        I_tel = fits.getdata(pathtel)
        hdr = fits.getheader(pathtel)
        w_tel = get_wavelength(hdr)
        i = (w_tel > w0) & (w_tel < w1)
        w_tel = w_tel[i]
        I_tel = I_tel[i]
        if len(w_tel) > 0:
            I_tel /= np.median(I_tel)
            if ccf in ['telluric', 'both'] and rv2:
                print('Warning: RV set for telluric, Calculate RV with CCF')
            if rv2 and ccf not in ['telluric', 'both']:
                I_tel, w_tel = dopplerShift(wvl=w_tel, flux=I_tel, v=rv2)
        else:
            print('Warning: Telluric spectrum not available in wavelength range.')
            telluric = False

    rvs = {}
    if ccf != 'none':
        if ccf in ['sun', 'both'] and sun:
            # remove tellurics from the Solar spectrum
            if telluric and sun:
                print('Correcting solar spectrum for tellurics...')
            print('Calculating CCF for the Sun...')
            rv1, r_sun, c_sun, x_sun, y_sun = ccf_astro((w, -I + 1), (w_sun, -I_sun + 1))
            if rv1 != 0:
                print('Shifting solar spectrum...')
                I_sun, w_sun = dopplerShift(w_sun, I_sun, v=rv1)
                rvs['sun'] = rv1
                print('DONE\n')

        if ccf in ['model', 'both'] and model:
            print('Calculating CCF for the model...')
            rv1, r_mod, c_mod, x_mod, y_mod = ccf_astro((w, -I + 1), (w_mod, -I_mod + 1))
            if rv1 != 0:
                print('Shifting model spectrum...')
                I_mod, w_mod = dopplerShift(w_mod, I_mod, v=rv1)
                rvs['model'] = rv1
                print('DONE\n')

        if ccf in ['telluric', 'both'] and telluric:
            print('Calculating CCF for the model...')
            rv2, r_tel, c_tel, x_tel, y_tel = ccf_astro((w, -I + 1), (w_tel, -I_tel + 1))
            if rv2 != 0:
                print('Shifting telluric spectrum...')
                I_tel, w_tel = dopplerShift(w_tel, I_tel, v=rv2)
                rvs['telluric'] = rv2
                print('DONE\n')

    if len(rvs) == 0:
        ccf = 'none'

    if ccf != 'none':
        from matplotlib.gridspec import GridSpec
        fig = plt.figure(figsize=(16, 5))
        gs = GridSpec(1, 5)
        if len(rvs) == 1:
            gs.update(wspace=0.25, hspace=0.35, left=0.05, right=0.99)
            ax1 = plt.subplot(gs[:, 0:-1])
            ax2 = plt.subplot(gs[:, -1])
            ax2.set_yticklabels([])
        elif len(rvs) == 2:
            gs.update(wspace=0.25, hspace=0.35, left=0.01, right=0.99)
            ax1 = plt.subplot(gs[:, 1:4])
            ax2 = plt.subplot(gs[:, 0])
            ax3 = plt.subplot(gs[:, -1])
            ax2.set_yticklabels([])
            ax3.set_yticklabels([])
    else:
        fig = plt.figure(figsize=(16, 5))
        ax1 = fig.add_subplot(111)

    # Start in pan mode with these two lines
    # manager = plt.get_current_fig_manager()
    # manager.toolbar.pan()

    # Use nice numbers on x axis (y axis is normalized)...
    x_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
    ax1.xaxis.set_major_formatter(x_formatter)

    if sun and not model:
        ax1.plot(w_sun, I_sun, '-C2', lw=1, alpha=0.6, label='Sun')
    if telluric:
        ax1.plot(w_tel, I_tel, '-C3', lw=1, alpha=0.6, label='Telluric')
    if model:
        ax1.plot(w_mod, I_mod, '-C2', lw=1, alpha=0.6, label='Model')
    ax1.plot(w, I, '-k', lw=1, label='Star')

    # Add crosshair
    xlim = ax1.get_xlim()
    cursor = Cursor(ax1)
    plt.connect('motion_notify_event', cursor.mouse_move)
    ax1.set_xlim(xlim)

    if (linelist or lines) and lineidImport and not nolines:
        try:
            lines, elements = np.loadtxt(linelist, usecols=(0, 1), skiprows=1, unpack=True)
            idx = (lines <= max(w)) & (lines >= min(w))
            lines = lines[idx]
            elements = elements[idx]
            Fe1Lines, Fe2Lines, otherLines = [], [], []
            for line, element in zip(lines, elements):
                if np.allclose(element, 26.0):
                    Fe1Lines.append('FeI: {}'.format(line))
                elif np.allclose(element, 26.1):
                    Fe2Lines.append('FeII: {}'.format(line))
                else:
                    otherLines.append('{}: {}'.format(element, line))

            lines = lines*(1.0 + rv1 / 299792.458) if rv1 else lines*1
            if len(Fe1Lines):
                lineid_plot.plot_line_ids(w, I, lines[elements==26.0], Fe1Lines, ax=ax1, add_label_to_artists=False)
            if len(Fe2Lines):
                pk = lineid_plot.initial_plot_kwargs()
                pk['color'] = 'red'
                lineid_plot.plot_line_ids(w, I, lines[elements==26.1], Fe2Lines, ax=ax1, add_label_to_artists=False, plot_kwargs=pk)
        except IOError:
            pass

    ax1.set_ylim(min(I)-0.05*min(I), 1.05*max(I))
    ax1.set_xlabel('Wavelength')
    ax1.set_ylabel('"Normalized" flux')

    if len(rvs) == 1:
        if 'sun' in rvs.keys():
            ax2.plot(r_sun, c_sun, '-k', alpha=0.9, lw=2)
            ax2.plot(x_sun, y_sun, '--C1', lw=2)
            ax2.set_title('CCF (sun)')
        if 'model' in rvs.keys():
            ax2.plot(r_mod, c_mod, '-k', alpha=0.9, lw=2)
            ax2.plot(x_mod, y_mod, '--C1', lw=2)
            ax2.set_title('CCF (mod)')
        if 'telluric' in rvs.keys():
            ax2.plot(r_tel, c_tel, '-k', alpha=0.9, lw=2)
            ax2.plot(x_tel, y_tel, '--C1', lw=2)
            ax2.set_title('CCF (tel)')
        ax2.set_xlabel('RV [km/s]')

    elif len(rvs) == 2:
        if 'sun' in rvs.keys():
            ax2.plot(r_sun, c_sun, '-k', alpha=0.9, lw=2)
            ax2.plot(x_sun, y_sun, '--C1', lw=2)
            ax2.set_title('CCF (sun)')
        if 'model' in rvs.keys():
            ax2.plot(r_mod, c_mod, '-k', alpha=0.9, lw=2)
            ax2.plot(x_mod, y_mod, '--C1', lw=2)
            ax2.set_title('CCF (mod)')
        ax3.plot(r_tel, c_tel, '-k', alpha=0.9, lw=2)
        ax3.plot(x_tel, y_tel, '--C1', lw=2)
        ax3.set_title('CCF (tel)')

        ax2.set_xlabel('RV [km/s]')
        ax3.set_xlabel('RV [km/s]')

    if rv:
        ax1.set_title('%s\nRV correction: %s km/s' % (fname, int(rv)))
    elif rv1 and rv2:
        ax1.set_title('%s\nSun/model: %s km/s, telluric: %s km/s' % (fname, int(rv1), int(rv2)))
    elif rv1 and not rv2:
        ax1.set_title('%s\nSun/model: %s km/s' % (fname, int(rv1)))
    elif not rv1 and rv2:
        ax1.set_title('%s\nTelluric: %s km/s' % (fname, int(rv2)))
    elif ccf == 'model':
        ax1.set_title('%s\nModel(CCF): %s km/s' % (fname, int(rv1)))
    elif ccf == 'sun':
        ax1.set_title('%s\nSun(CCF): %s km/s' % (fname, int(rv1)))
    elif ccf == 'telluric':
        ax1.set_title('%s\nTelluric(CCF): %s km/s' % (fname, int(rv2)))
    elif ccf == 'both':
        ax1.set_title('%s\nSun/model(CCF): %s km/s, telluric(CCF): %s km/s' % (fname, int(rv1), int(rv2)))
    else:
        ax1.set_title(fname)
    if sun or telluric or model:
        ax1.legend(loc=3, frameon=False)
    plt.show()

    return rvs


def runner():
    args = vars(_parser())
    fname = args.pop('fname')
    opts = {k: args[k] for k in args}

    main(fname, **opts)


if __name__ == '__main__':
    runner()
