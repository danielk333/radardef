"""MU radar object"""

from pyant.beam import Beam
from pyant.types import Parameters
from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.pansy.beams import (
    pansy_array_beam,
    pansy_interpolated_array_beam,
)
from radardef.types import StationID


class Pansy(RadarStation):
    """
    Pansy radar definition

    Args:
        interpolated (optional): If beam should be interpolated, by default False.

    """

    def __init__(self, interpolated: bool = False) -> None:

        beam: Beam
        params: Parameters
        if interpolated:
            beam, params = pansy_interpolated_array_beam()
        else:
            beam, params = pansy_array_beam()

        super().__init__(
            StationID.PANSY,
            transmitter=True,
            receiver=True,
            lat=-69.0066066316,
            lon=39.5930902267,
            alt=0.0,
            beam=beam,
            beam_parameters=params,
            power=0.5e6,
            power_per_element=500.0,
            frequency=47e6,
        )
