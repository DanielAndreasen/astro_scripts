from __future__ import division
import pytest
import numpy as np
from astro_scripts.utils import _nrefrac, vac2air, dopplerShift

def test_nrefrac():
    wl, density = 10, 1.0
    assert isinstance(_nrefrac(wl, density=density), float)
    assert round(_nrefrac(wl, density=density), 9) == 1.000064298
    assert _nrefrac(wl) == _nrefrac(wl, density=density)
    assert _nrefrac(wl, density=density) < _nrefrac(wl, density=density*2)
    with pytest.raises(ValueError):
        _nrefrac(wl, density=0)
    with pytest.raises(ZeroDivisionError):
        _nrefrac(0, density=density)


def test_vac2air():
    wl, density = 10, 1.0
    assert isinstance(vac2air(wl, density=density), float)
    assert isinstance(vac2air([wl]), np.ndarray)
    assert round(vac2air(wl, density=density), 9) == 9.999357059
    assert vac2air(wl) == vac2air(wl, density=density)
    assert vac2air(wl, density=density) > vac2air(wl, density=density*2)
    with pytest.raises(ValueError):
        vac2air(wl, density=0)
    with pytest.raises(ZeroDivisionError):
        vac2air(0, density=density)


def test_dopplerShift():
    wl = np.array([1, 2, 3])
    fl = np.array([1, 0.8, 1])
    v = 20
    assert isinstance(dopplerShift(wl, fl, v)[0], np.ndarray)
    assert isinstance(dopplerShift(wl, fl, v)[1], np.ndarray)
    assert (dopplerShift(wl, fl, v)[0] == fl).all()
    assert (dopplerShift(wl, fl, v)[1]  > wl).all()
    assert (dopplerShift(wl, fl, -v)[1] < wl).all()
