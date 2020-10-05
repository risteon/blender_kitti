#!/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import numpy as np


def add_height_map(
    *,
    zvalues: np.ndarray,
    colors: np.ndarray = None,
    config: np.ndarray = None,
    name_prefix: str = "height_map",
    scene,
):
    return None, {"zvalues": zvalues, "colors": colors, "config": config}
