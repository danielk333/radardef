"""A collection of functions and information for the EISCAT UHF Radar system."""

import numpy as np
from pyant.beam import Beam
from pyant.models import (
    Cassegrain,
    CassegrainParams,
    MeasuredAzimuthallySymmetric,
    MeasuredAzimuthallySymmetricParams,
)
from pyant.models.measured import InterpMethods

from .data import DATA_PATHS


def eiscat_uhf_beam(
    interpolation_method: InterpMethods,
) -> tuple[MeasuredAzimuthallySymmetric, MeasuredAzimuthallySymmetricParams]:
    """Eiscat uhf measured azimuthally symmetric beam, values from [^1].

    [^1]: Nygrén, T., 1996. Introduction to incoherent scatter measurements, 1st ed. Invers Oy.
    """

    assert "eiscat_uhf_bp.txt" in DATA_PATHS, "data file missing!"

    with open(DATA_PATHS["eiscat_uhf_bp.txt"], "r") as stream:
        eiscat_beam_data = np.genfromtxt(stream)

    peak_gain = 10**4.81
    order = np.argsort(eiscat_beam_data[:, 0], axis=0)[::-1]
    eiscat_beam_data[:, 0] *= -1
    eiscat_beam_data = eiscat_beam_data[order, :]
    eiscat_beam_data = eiscat_beam_data[eiscat_beam_data[:, 0] >= 0]

    beam = MeasuredAzimuthallySymmetric(
        off_axis_angle=eiscat_beam_data[:, 0],
        gains=10.0 ** (eiscat_beam_data[:, 1] / 10.0) * peak_gain,
        interpolation_method=interpolation_method,
        degrees=True,
    )
    params = MeasuredAzimuthallySymmetricParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
    )
    return beam, params


def eiscat_uhf_cassegrain_beam() -> tuple[Cassegrain, CassegrainParams]:
    """Eiscat uhf cassegrain beam, values from [^1].

    [^1]: Nygrén, T., 1996. Introduction to incoherent scatter measurements, 1st ed. Invers Oy.

    """

    beam = Cassegrain(
        peak_gain=10**4.81,
    )
    params = CassegrainParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=930e6,
        outer_radius=16.0,
        inner_radius=2.29,
    )
    return beam, params
