"""A collection of functions and information for the NOSTRA system."""

import numpy as np

from pyant.models import FiniteCylindricalParabola, FiniteCylindricalParabolaParams


def generate_nostra() -> tuple[FiniteCylindricalParabola, FiniteCylindricalParabolaParams]:
    """Nostra Finite Cylindrical Parabola beam, note that these values might not be correct"""
    beam = FiniteCylindricalParabola()
    params = FiniteCylindricalParabolaParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=224e6,
        width=120.0,
        height=40.0,
        aperture_width=120.0,  # TODO: Should be optional, can be removed once pyant is updated
    )

    return beam, params
