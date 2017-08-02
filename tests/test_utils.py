from __future__ import division
import os
import pytest
import numpy as np
import pandas as pd
from astro_scripts.utils import nrefrac


def test_nrefrac():
    assert isinstance(nrefrac(10, 10), float)
