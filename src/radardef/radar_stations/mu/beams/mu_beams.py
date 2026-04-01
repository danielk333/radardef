"""A collection of functions and information for the MU system."""

import pathlib
from pathlib import Path
from typing import Any, Optional

import numpy as np
import scipy.interpolate
from pyant.models import Array, ArrayParams, InterpolatedArray, InterpolatedArrayParams
from spacecoords.spherical import cart_to_sph

from radardef.radar_stations.mu.beams.data import get_antenna_pos, get_yagi_specs
from radardef.tools.types import CarthesianCoordinates_3xN, NDArray_2, NDArray_2xN

YAGI_AZ, YAGI_EL, YAGI_GAIN_DB = get_yagi_specs()
ANTENNA_POS = get_antenna_pos()


def yagi(cart_coord: CarthesianCoordinates_3xN, polarization: NDArray_2) -> NDArray_2xN:

    interp = scipy.interpolate.RegularGridInterpolator(
        (YAGI_AZ[0, :], YAGI_EL[:, 0]),
        YAGI_GAIN_DB.T,
        bounds_error=False,
    )

    sph = cart_to_sph(cart_coord, degrees=True)
    G = 10 ** (interp(sph[:2, :].T) / 10.0)
    return np.stack([G, G], axis=0)


def mu_array_beam() -> tuple[Array, ArrayParams]:
    """A MU array beam"""

    beam = Array(
        antennas=ANTENNA_POS,
        antenna_element=yagi,
    )
    params = ArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=46.5e6,
        polarization=beam.polarization.copy(),
    )
    return beam, params


def mu_interpolated_array_beam(
    path: Optional[Path] = None, **interpolation_kwargs: Any
) -> tuple[InterpolatedArray, InterpolatedArrayParams]:
    """A MU interpolated array beam"""
    beam = InterpolatedArray()
    params = InterpolatedArrayParams(pointing=np.array([0, 0, 1], dtype=np.float64))
    if path is None:
        array, arr_params = mu_array_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        return beam, params

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if path.is_file():
        beam.load(path)
    else:
        array, arr_params = mu_array_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        beam.save(path)
    return beam, params
