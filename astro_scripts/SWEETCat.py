#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import os
import requests
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from . import matplotlibcfg

def _parser():
    parser = argparse.ArgumentParser(description='Plot SWEET-Cat stuff')
    p = ['vmag', 'vmagerr', 'par', 'parerr', 'teff', 'tefferr', 'logg',
         'loggerr', 'logglc', 'logglcerr', 'vt', 'vterr', 'feh', 'feherr',
         'mass', 'masserr', 'lum', 'age']
    parser.add_argument('x', help='Plot this data one first axis', choices=p)
    parser.add_argument('y', help='Plot this data one second axis', choices=p)
    parser.add_argument('-z', help='Color scale', choices=p, default=None)
    parser.add_argument('-p', '--sweetcat', help='Only plot homogeneous parameters', default=False, action='store_true')
    parser.add_argument('-ix', help='Inverse x axis', default=False, action='store_true')
    parser.add_argument('-iy', help='Inverse y axis', default=False, action='store_true')
    parser.add_argument('-iz', help='Inverse z axis', default=False, action='store_true')
    parser.add_argument('-lx', help='Logarithmic x axis', default=False, action='store_true')
    parser.add_argument('-ly', help='Logarithmic y axis', default=False, action='store_true')
    parser.add_argument('-s', help='Place Solar values in the plot', default=False, action='store_true')
    parser.add_argument('-l', help='Fit a linear regression', default=False, action='store_true')
    args = parser.parse_args()
    return args


def _read_sweetcat(fname):
    """
    Read SWEETCat into a pandas DataFrame
    """
    if not isinstance(fname, str):
        raise ValueError('Input name must be a str')

    names = ['star', 'hd', 'ra', 'dec', 'vmag', 'vmagerr', 'par', 'parerr',
             'parsource', 'teff', 'tefferr', 'logg', 'loggerr', 'logglc',
             'logglcerr', 'vt', 'vterr', 'feh', 'feherr', 'mass', 'masserr',
             'author', 'source', 'update', 'comment0', 'comment1', 'comment2']
    df = pd.read_csv(fname, sep='\t', names=names, na_values=['~'])
    df['source'] = df['source'].replace(np.nan, 0).astype(bool)
    df.drop(['comment0', 'comment1', 'comment2'], inplace=True, axis=1)
    # Adding luminosity to the DataFrame
    df['lum'] = (df.teff/5777)**4 * df.mass * (10**(4.44-df.logg))
    df = df[df['teff'] < 10000]
    return df


def _download_sweetcat(fout):
    """
    Download SWEETCAT and write it to file
    """
    url = 'https://www.astro.up.pt/resources/sweet-cat/download.php'
    table = requests.get(url)
    with open(fout, 'w') as file:
        file.write(table.content)


def main():
    args = _parser()
    path = os.path.expanduser('~/.SWEETCat/')
    _sc = os.path.join(path, 'sweetcat.csv')
    if os.path.isdir(path):
        if not os.path.isfile(_sc):
            print('Downloading SWEET-Cat...')
            _download_sweetcat(_sc)
    else:
        os.mkdir(path)
        print('%s Created' % path)
        print('Downloading SWEET-Cat...')
        _download_sweetcat(_sc)

    df = _read_sweetcat(_sc)
    if args.sweetcat:
        df = df[df.source == True]

    df['x'] = df[args.x]
    df['y'] = df[args.y]

    if (args.x == 'age') or (args.y == 'age') or (args.z == 'age'):
        from isochrones.dartmouth import Dartmouth_Isochrone
        dar = Dartmouth_Isochrone()
        age = np.zeros(df.shape[0])
        for i, (mass, feh) in enumerate(df[['mass', 'feh']].values):
            tmp = dar.agerange(mass, feh)
            age[i] = (10**(tmp[0]-9) + 10**(tmp[1]-9))/2
        df['age'] = pd.Series(age)

    if args.z:
        if args.iz:
            z = 1/df[args.z].values
        else:
            z = df[args.z].values
        color = df[args.z].values
        u = z[~np.isnan(z)]
        size = (z-u.min())/(u.max()-u.min())*100
        size[np.argmin(size)] = 10  # Be sure to show the "smallest" point
        plt.scatter(df['x'], df['y'], c=color, s=size)  #, cmap=cm.viridis)
    else:
        plt.scatter(df['x'], df['y'], s=40)


    labels = {'teff':      r'$T_\mathrm{eff}$ [K]',
              'tefferr':   r'$\sigma T_\mathrm{eff}$ [K]',
              'logg':      r'$\log(g)$ [cgs]',
              'loggerr':   r'$\sigma \log(g)$ [cgs]',
              'logglc':    r'$\log(g)$ [cgs]',
              'logglcerr': r'$\sigma \log(g)$ [cgs]',
              'feh':        '[Fe/H]',
              'feherr':    r'$\sigma$ [Fe/H]',
              'vt':        r'$\xi_\mathrm{micro}$ [km/s]',
              'vterr':     r'$\sigma\xi_\mathrm{micro}$ [km/s]',
              'lum':       r'$L_\odot$',
              'mass':      r'$M_\odot$',
              'masserr':   r'$\sigma M_\odot$',
              'radius':    r'$R_\odot$',
              'radiuserr': r'$\sigma R_\odot$',
              'age':       r'Age $[Gyr]$',
              'par':       r'$\pi$ [mas]',
              'parerr':    r'$\sigma \pi$ [mas]',
              'vmag':       'V magnitude',
              'vmagerr':   r'$\sigma$ V magnitude'}

    plt.xlabel(labels[args.x])
    plt.ylabel(labels[args.y])
    if args.z:
        cbar = plt.colorbar()
        cbar.set_label(labels[args.z])
    if args.s:
        sun = {'teff': 5777,
               'tefferr': 1,
               'logg': 4.44,
               'loggerr': 0.01,
               'feh': 0.00,
               'feherr': 0.01,
               'vt': 1.00,
               'vterr': 0.01,
               'lum': 1,
               'mass': 1,
               'masserr': 0.01,
               'radius': 1,
               'radiuserr': 0.01,
               'age': 4.567}
        plt.scatter(sun[args.x], sun[args.y], marker='*', s=200, alpha=0.8)
    if args.ix:
        plt.xlim(plt.xlim()[::-1])
    if args.iy:
        plt.ylim(plt.ylim()[::-1])

    if args.lx:
        plt.xscale('log')
        df['x'] = np.log(df['x'])
    if args.ly:
        y1, y2 = plt.ylim()
        plt.yscale('log')
        plt.ylim(max(y1, 0.01), y2)
        df['y'] = np.log(df['y'])

    if args.l:
        p = np.polyfit(df['x'], df['y'], deg=1)
        print('  y=%.3f*x+%.3f' % (p[0], p[1]))
        x1, x2 = df.x.min(), df.x.max()
        yfit = np.poly1d(p)([x1, x2])
        if args.lx and args.ly:
            plt.plot(np.exp([x1, x2]), np.exp(yfit), '-k')
        elif args.lx and not args.ly:
            plt.plot(np.exp([x1, x2]), yfit, '-k')
        elif not args.lx and args.ly:
            plt.plot([x1, x2], np.exp(yfit), '-k')
        else:
            plt.plot([x1, x2], yfit, '-k')

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
