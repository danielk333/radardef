"""A collection of functions and information for the EISCAT VHF Radar system."""

import numpy as np

from pyant.models import FiniteCylindricalParabola, FiniteCylindricalParabolaParams


def eiscat_vhf_beam() -> tuple[FiniteCylindricalParabola, FiniteCylindricalParabolaParams]:
    """
    Eiscat VHF with all panels moving as a whole [1]_.

    NOTE:
        Has an extra method called :code:`calibrate` that numerically calculates
        the integral of the gain and scales the gain pattern according.

    """
    beam = FiniteCylindricalParabola()
    params = FiniteCylindricalParabolaParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=224e6,
        width=120.0,
        height=40.0,
        aperture_width=120.0,  # TODO: Should be optional, can be removed once pyant is updated
    )
    return beam, params
