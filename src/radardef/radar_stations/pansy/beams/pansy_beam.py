"""A collection of functions and information for the PANSY Radar system."""

import pathlib
from pathlib import Path
from typing import Any, Optional

import numpy as np
import numpy.typing as npt
import scipy.interpolate

from pyant.models import Array, ArrayParams, InterpolatedArray, InterpolatedArrayParams
from radardef.tools.types import CarthesianCoordinates_3xN, NDArray_2, NDArray_2xN
from spacecoords.spherical import cart_to_sph

from .data import DATA_PATHS


def load_pos_and_gain_from_data() -> tuple[npt.NDArray, npt.NDArray]:
    """Load position and gain data from the measurement files"""

    assert "antpos.csv-20160121" in DATA_PATHS, "pos file missing!"
    # SerialNo. , GrpName, ModuleID, Ready , X(m), Y(m), Z(m)
    _pansy_antennas = np.genfromtxt(
        fname=DATA_PATHS["antpos.csv-20160121"],
        skip_header=1,
        delimiter=",",
        dtype="i4, U3, U3, i4, f8, f8, f8",
    )

    assert "mu_yagi_gain.npz" in DATA_PATHS, "gain file missing!"
    _mu_yagi = np.load(DATA_PATHS["mu_yagi_gain.npz"])

    return _pansy_antennas, _mu_yagi


def pansy_array_beam() -> tuple[Array, ArrayParams]:
    """A pansy array beam"""

    _pansy_antennas, _mu_yagi = load_pos_and_gain_from_data()

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

    groups_f1 = np.unique(_pansy_antennas["f1"])
    grp_remove = ["DIV", "Z1", "Z2"]
    groups = [grp for grp in groups_f1 if grp not in grp_remove]

    antennas = []
    for ind, grp in enumerate(groups):
        select = np.logical_and(
            _pansy_antennas["f1"] == grp,
            _pansy_antennas["f3"] == 1,
        )
        subgroup = np.empty((3, np.sum(select)), dtype=np.float64)
        subgroup[0, :] = _pansy_antennas["f4"][select]
        subgroup[1, :] = _pansy_antennas["f5"][select]
        subgroup[2, :] = _pansy_antennas["f6"][select]
        antennas.append(subgroup)

    beam = Array(
        antennas=antennas,  # type: ignore[arg-type]
        antenna_element=yagi,
    )
    params = ArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=47e6,
        polarization=beam.polarization.copy(),
    )
    return beam, params


def pansy_interpolated_array_beam(
    path: Optional[Path] = None, **interpolation_kwargs: Any
) -> tuple[InterpolatedArray, InterpolatedArrayParams]:
    """
    A pansy interpolated array beam

    Beam can be loaded from a file if a path is given.
    """

    beam = InterpolatedArray()
    params = InterpolatedArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
    )
    if path is None:
        array, arr_params = pansy_array_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        return beam, params

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if path.is_file():
        beam.load(path)
    else:
        array, arr_params = pansy_array_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        beam.save(path)
    return beam, params
