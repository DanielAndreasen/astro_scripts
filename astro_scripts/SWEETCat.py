#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import os
import requests
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
try:
    import seaborn as sns
    sns.set_context('talk')
except ImportError:
    print('For better looking plots, try install seaborn (pip install seaborn)')
    pass


def _read_sweetcat(fname):
    """
    Read SWEETCat into a pandas DataFrame
    """
    if not isinstance(fname, str):
        raise ValueError('Input name must be a str')

    names = ['star', 'hd', 'ra', 'dec', 'vmag', 'ervmag', 'par', 'erpar',
             'parsource', 'teff', 'erteff', 'logg', 'erlogg', 'logglc',
             'erlogglc', 'vt', 'ervt', 'metal', 'ermetal', 'mass', 'ermass',
             'author', 'link', 'source', 'update', 'comment1', 'comment2']
    df = pd.read_csv(fname, sep='\t', names=names, na_values=['~'])
    # Adding luminosity to the DataFrame
    df['lum'] = (df.teff/5777)**4 * df.mass
    return df


def _download_sweetcat(fout):
    """
    Download SWEETCAT and write it to file
    """
    url = 'https://www.astro.up.pt/resources/sweet-cat/download.php'
    table = requests.get(url)
    with open(fout, 'w') as file:
        file.write(table.content)


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
