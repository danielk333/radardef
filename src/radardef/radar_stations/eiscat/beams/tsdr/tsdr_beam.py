"""A collection of functions and information for the Tromso Space Debris Radar (TSDR) system.

Notes:
    Configurations taken from [1]_.

    .. [1] (White paper) McKay, D., Grydeland, T., Vierinen, J.,
        Kastinen, D., Kero, J., Krag, H. (2019) Conversion of the EISCAT VHF
        antenna into the Tromso Space Debris Radar

"""

import numpy as np

from pyant.models import (
    FiniteCylindricalParabola,
    FiniteCylindricalParabolaParams,
    PhasedFiniteCylindricalParabola,
    PhasedFiniteCylindricalParabolaParams,
)


def tsdr_beam() -> tuple[FiniteCylindricalParabola, FiniteCylindricalParabolaParams]:
    """
    Tromso Space Debris Radar system with all panels moving as a whole [1]_.

    NOTE:
        Has an extra method called :code:`calibrate` that numerically calculates
        the integral of the gain and scales the gain pattern according.



    """
    beam = FiniteCylindricalParabola()
    params = FiniteCylindricalParabolaParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        frequency=1.8e9,
        width=120.0,
        height=40.0,
        aperture_width=120.0,  # TODO: Should be optional, can be removed once pyant is updated
    )
    return beam, params


def tsdr_phased_beam() -> tuple[PhasedFiniteCylindricalParabola, PhasedFiniteCylindricalParabolaParams]:
    """
    Tromso Space Debris Radar system with panels moving independently.

    NOTE:
        This model is a list of the 4 panels. This applies heave approximations on
        the behavior of the gain pattern as the panels move. Considering a linefeed
        of a single panel, it will receive more reflection area if one of the
        adjacent panels move in into the same pointing direction therefor
        distorting the side-lobe as support structures pass but also narrowing the
        resulting beam.None of these effects are considered here and this
        approximation is reasonably valid when all panels are pointing in
        sufficiently different directions.

    """
    beam = PhasedFiniteCylindricalParabola()
    params = PhasedFiniteCylindricalParabolaParams(
        pointing=np.array([0, 0, 1], dtype=np.float64),
        phase_steering=0.0,
        depth=18.0,
        frequency=1.8e9,
        width=120.0,
        height=40.0,
        aperture_width=120.0,  # TODO: Should be optional so can be removed when pyant is updated
    )
    return beam, params
