#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Licensed under the MIT Licence


import os.path

__all__ = [
    "__title__", "__summary__", "__uri__", "__version__", "__commit__",
    "__author__", "__email__", "__license__", "__copyright__",
]


try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = None


__title__ = "astro_scripts"
__summary__ = "Small scripts for astronomy"
__uri__ = "https://pypi.python.org/pypi/astro-scripts/"

# The version as used in the setup.py and the docs conf.py
__version__ = "0.3.6"

if base_dir is not None and os.path.exists(os.path.join(base_dir, ".commit")):
    with open(os.path.join(base_dir, ".commit")) as fp:
        __commit__ = fp.read().strip()
else:
    __commit__ = None

__author__ = "Daniel T. Andreasen"
__email__ = "daniel.andreasen@astro.up.pt"

__license__ = "MIT Licence"
__copyright__ = "2015 {0!s}".format(__author__)
