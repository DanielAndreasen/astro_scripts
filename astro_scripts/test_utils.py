from __future__ import division
from astro_scripts import utils


def test_nrefrac():
    assert isinstance(utils.nrefrac(10, 10), float)
