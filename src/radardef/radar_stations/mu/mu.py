"""MU radar object"""

from pyant import Beam
from pyant.types import Parameters
from radardef.components.radar_station_template import RadarStation
from radardef.types import StationID

from .beams import mu_array_beam, mu_interpolated_array_beam
from .converters import MuiToH5
from .data_loaders import H5Loader
from .validators import MUI


class Mu(RadarStation):
    """
    MU radar definition

    Args:
        interpolated (optional): If beam should be interpolated, by default False.

    """

    def __init__(self, interpolated: bool = False) -> None:

        beam: Beam
        params: Parameters
        if interpolated:
            beam, params = mu_interpolated_array_beam()
        else:
            beam, params = mu_array_beam()

        super().__init__(
            StationID.MU,
            transmitter=True,
            receiver=True,
            lat=34.85402777777778,
            lon=136.10562222222222,
            alt=372.0,
            beam=beam,
            beam_parameters=params,
            min_elevation=30,
            power=1e6,
            power_per_element=2105.2631578947367,
            frequency=46.5e6,
            converters=[MuiToH5()],
            validator=MUI(),
            data_loaders=[H5Loader()],
        )
