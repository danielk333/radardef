"""A collection of functions and information for the Eiscat Svalbard Radar (ESR) system."""

import numpy as np

from spacecoords.spherical import sph_to_cart
from pyant.models import Cassegrain, CassegrainParams


def esr_32m_cassegrain_beam() -> tuple[Cassegrain, CassegrainParams]:
    """ESR 32 meter antenna diameter"""
    beam = Cassegrain(
        peak_gain=10 ** (42.5 / 10),
    )
    params = CassegrainParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=500e6,
        outer_radius=16.0,
        inner_radius=1.73,
    )
    return beam, params


def esr_42m_cassegrain_beam() -> tuple[Cassegrain, CassegrainParams]:
    """ESR 42 meter antenna diameter"""
    beam = Cassegrain(
        peak_gain=10 ** (45.0 / 10),  # Linear gain (42.5 dB)
    )
    params = CassegrainParams(
        # azimut=185.5, elevation=82.1  (since 2019)
        pointing=sph_to_cart(np.array([185.5, 82.1, 1], dtype=np.float64), degrees=True),
        frequency=500e6,
        outer_radius=21.0,  # radius main reflector
        inner_radius=3.3,  # radius subreflector (eyeballed from photo)
    )
    return beam, params
