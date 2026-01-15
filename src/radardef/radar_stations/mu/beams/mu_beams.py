"""A collection of functions and information for the MU system."""

import pathlib
from pathlib import Path
from typing import Any, Optional

import numpy as np
import scipy.interpolate

from pyant.models import Array, ArrayParams, InterpolatedArray, InterpolatedArrayParams
from radardef.radar_stations.mu.beams.data import DATA_PATHS
from radardef.tools.types import CarthesianCoordinates_3xN, NDArray_2, NDArray_2xN
from spacecoords.spherical import cart_to_sph


def mu_array_beam() -> tuple[Array, ArrayParams]:
    """A MU array beam"""

    assert "MU_antenna_pos.npy" in DATA_PATHS, "pos file missing!"
    _mu_antennas = np.load(DATA_PATHS["MU_antenna_pos.npy"])

    assert "mu_yagi_gain.npz" in DATA_PATHS, "gain file missing!"
    _mu_yagi = np.load(DATA_PATHS["mu_yagi_gain.npz"])

    az = _mu_yagi["az_deg"].reshape(-1, 721)
    az -= 180
    el = _mu_yagi["el_deg"].reshape(-1, 721)
    gain_dB = _mu_yagi["gain_dB"].reshape(-1, 721)
    gain_dB = gain_dB - np.max(_mu_yagi["gain_dB"])

    interp = scipy.interpolate.RegularGridInterpolator(
        (az[0, :], el[:, 0]),
        gain_dB.T,
        bounds_error=False,
    )

    def yagi(cart_coord: CarthesianCoordinates_3xN, polarization: NDArray_2) -> NDArray_2xN:
        sph = cart_to_sph(cart_coord, degrees=True)
        G = 10 ** (interp(sph[:2, :].T) / 10.0)
        return np.stack([G, G], axis=0)

    beam = Array(
        antennas=_mu_antennas,
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
