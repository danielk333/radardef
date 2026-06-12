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


def yagi(cart_coord: CarthesianCoordinates_3xN, polarization: NDArray_2 | NDArray_2xN) -> NDArray_2xN:
    """The Yagi antenna radiation pattern from [^1]

    [^1]: Fukao, S., Sato, T., Tsuda, T., Kato, S., Wakasugi, K., Makihira, T., 1985.
        The MU radar with active phased array system. I - Antenna and power amplifiers. II - In-house equipment.
        Radio Sci. 20, 1155–1176. https://doi.org/10.1029/RS020i006p01155
    """

    yagi_peak_db = 7.24
    interp = scipy.interpolate.RegularGridInterpolator(
        (YAGI_AZ[0, :], YAGI_EL[:, 0]),
        YAGI_GAIN_DB.T + yagi_peak_db,
        bounds_error=False,
    )

    sph = cart_to_sph(cart_coord, degrees=True)
    # this is power gain and not field gain - devide dB by 2 to get field gain
    G = 10 ** (interp(sph[:2, :].T) / 20.0)
    return np.stack([G, G], axis=0)


def mu_array_beam() -> tuple[Array, ArrayParams]:
    """MU array beam [^1]

    [^1]: Fukao, S., Sato, T., Tsuda, T., Kato, S., Wakasugi, K., Makihira, T., 1985.
        The MU radar with active phased array system. I - Antenna and power amplifiers. II - In-house equipment.
        Radio Sci. 20, 1155–1176. https://doi.org/10.1029/RS020i006p01155
    """

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
