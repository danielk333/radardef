"""A collection of functions and information for the EISCAT 3D Radar system.

Notes
-----
Configuration are taken from [1]_.


.. [1] (Technical report) Vierinen, J., Kastinen, D., Kero, J.,
    Grydeland, T., McKay, D., Roynestad, E., Hesselbach, S., Kebschull, C., &
    Krag, H. (2019). EISCAT 3D Performance Analysis

"""

import pathlib
from pathlib import Path
from typing import Any, Optional

import numpy as np
import numpy.typing as npt
import scipy.constants

from pyant.models import Array, ArrayParams, InterpolatedArray, InterpolatedArrayParams
from radardef.tools.types import NDArray_2xN, NDArray_N

from .data import DATA_PATHS

e3d_frequency = 233e6
e3d_antenna_gain = 10.0**0.3  # 3 dB peak antenna gain?


def e3d_subarray(frequency: float) -> tuple[NDArray_N, NDArray_N, NDArray_N]:
    """Generate cartesian positions `x,y,z` in meters of antenna elements in
    one standard EISCAT 3D subarray.
    """
    l0 = scipy.constants.c / frequency

    dx = 1.0 / np.sqrt(3)
    dy = 0.5

    xall = []
    yall = []

    x0_p1 = np.arange(-2.5, -5.5, -0.5).tolist()
    x0_p2 = np.arange(-4.5, -2.0, 0.5).tolist()
    x0 = np.array([x0_p1 + x0_p2])[0] * dx
    y0 = np.arange(-5, 6, 1) * dy

    for iy in range(11):
        nx = 11 - np.abs(iy - 5)
        x_now = x0[iy] + np.array(range(nx)) * dx
        y_now = y0[iy] + np.array([0.0] * (nx))
        xall += x_now.tolist()
        yall += y_now.tolist()

    x = l0 * np.array(xall)
    y = l0 * np.array(yall)
    z = x * 0.0

    return x, y, z


# TODO:Better type hint
def e3d_array(frequency: float, fname: Optional[str] = None, configuration: str = "full") -> npt.NDArray:
    """Generate the antenna positions for a EISCAT 3D Site based on submodule
    positions of a file.
    """

    def _read_e3d_submodule_pos(string_data: str) -> NDArray_2xN:
        """read e3d submodule position and create a 2xN numpy float array"""
        dat = []
        file = string_data.split("\n")
        for line in file:
            if len(line) == 0:
                continue
            dat.append(list(map(lambda x: float(x), line.split())))
        return np.array(dat)

    assert "e3d_subgroup_positions.txt" in DATA_PATHS, "data file missing!"
    path = fname if fname is not None else DATA_PATHS["e3d_subgroup_positions.txt"]

    with open(path, "r") as stream:
        _ant_data = stream.read()

    dat = _read_e3d_submodule_pos(_ant_data)

    sx, sy, sz = e3d_subarray(frequency)

    if configuration == "full":
        pass
    elif configuration == "dense":
        dat = dat[(np.sum(dat**2.0, axis=1) < 27.0**2.0), :]
    elif configuration == "sparse":
        dat = dat[
            np.logical_or(
                np.logical_or(
                    np.logical_and(np.sum(dat**2, axis=1) < 10**2, np.sum(dat**2, axis=1) > 7**2),
                    np.logical_and(np.sum(dat**2, axis=1) < 22**2, np.sum(dat**2, axis=1) > 17**2),
                ),
                np.logical_and(
                    np.sum(dat**2, axis=1) < 36**2,
                    np.sum(dat**2, axis=1) > 30**2,
                ),
            ),
            :,
        ]
    elif configuration == "module":
        dat = np.zeros((1, 2))

    antennas = np.zeros((3, len(sx), dat.shape[0]), dtype=dat.dtype)
    for i in range(dat.shape[0]):
        for j in range(len(sx)):
            antennas[0, j, i] = sx[j] + dat[i, 0]
            antennas[1, j, i] = sy[j] + dat[i, 1]
            antennas[2, j, i] = sz[j]
    return antennas


def eiscat_3d_single_subarray_beam() -> tuple[Array, ArrayParams]:
    """EISCAT 3D Gain pattern for single antenna sub-array."""
    beam = Array(
        antennas=e3d_array(
            e3d_frequency,
            configuration="module",
        ),
    )
    params = ArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=e3d_frequency,
        polarization=beam.polarization.copy(),
    )
    return beam, params


def eiscat_3d_stage1_beam(configuration: str = "dense") -> tuple[Array, ArrayParams]:
    """EISCAT 3D Gain pattern for a dense core of active sub-arrays,
    i.e stage 1 of development.

    Args:
        configuration (optional): Chooses how the stage1 antennas are distributed in the full array,
            alt {'dense', 'sparse'}

    """
    beam = Array(
        antennas=e3d_array(
            e3d_frequency,
            configuration=configuration,
        ),
    )
    params = ArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=e3d_frequency,
        polarization=beam.polarization.copy(),
    )
    return beam, params


# TODO: Clarify Any
def eiscat_3d_stage1_interp_beam(
    path: Optional[str | Path] = None, configuration: str = "dense", **interpolation_kwargs: Any
) -> tuple[InterpolatedArray, InterpolatedArrayParams]:
    """EISCAT 3D Gain pattern for a dense core of active sub-arrays,
    i.e stage 1 of development.

    Args:
        configuration (optional): Chooses how the stage1 antennas are distributed in the full array,
            alt {'dense', 'sparse'}
    """
    beam = InterpolatedArray()
    params = InterpolatedArrayParams(pointing=np.array([0, 0, 1], dtype=np.float64))
    if path is None:
        array, arr_params = eiscat_3d_stage1_beam(configuration=configuration)
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        return beam, params

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if path.is_file():
        beam.load(path)
    else:
        array, arr_params = eiscat_3d_stage1_beam(configuration=configuration)
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        beam.save(path)
    return beam, params


def eiscat_3d_stage2_beam() -> tuple[Array, ArrayParams]:
    """EISCAT 3D Gain pattern for a full site of active sub-arrays,
    i.e stage 2 of development.

    """
    beam = Array(
        antennas=e3d_array(
            e3d_frequency,
            configuration="full",
        ),
    )
    params = ArrayParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=e3d_frequency,
        polarization=beam.polarization.copy(),
    )
    return beam, params


# TODO: Clarify Any
def eiscat_3d_stage2_interp_beam(
    path: Optional[str | Path] = None, **interpolation_kwargs: Any
) -> tuple[InterpolatedArray, InterpolatedArrayParams]:
    """EISCAT 3D Gain pattern for a full set of active sub-arrays,
    i.e stage 2 of development.
    """
    beam = InterpolatedArray()
    params = InterpolatedArrayParams(pointing=np.array([0, 0, 1], dtype=np.float64))
    if path is None:
        array, arr_params = eiscat_3d_stage2_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        return beam, params

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if path.is_file():
        beam.load(path)
    else:
        array, arr_params = eiscat_3d_stage2_beam()
        beam.generate_interpolation(array, arr_params, **interpolation_kwargs)
        beam.save(path)
    return beam, params
