"""Tromso Space Debris Radar (TSDR) object"""

from pyant.beam import Beam
from pyant.types import Parameters
from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.eiscat.beams.tsdr import tsdr_beam, tsdr_phased_beam
from radardef.types import StationID

from .converters import EiscatMatbzToDrf
from .data_loaders import DrfLoader
from .validators import EiscatMatlab


class TSDR(RadarStation):
    """
    Tromso Space Debris Radar (TSDR) definition

    Args:
        phased: If the beam should be phased
    """

    def __init__(self, phased: bool = False) -> None:
        beam: Beam
        params: Parameters
        if phased:
            beam, params = tsdr_phased_beam()
        else:
            beam, params = tsdr_beam()

        super().__init__(
            StationID.TSDR,
            transmitter=True,
            receiver=True,
            lat=69.5866115,
            lon=19.221555,
            alt=85.0,
            beam=beam,
            beam_parameters=params,
            noise_temperature=100,
            power=0.5e6,
            frequency=1.8e9,
            converters=[EiscatMatbzToDrf()],
            validator=EiscatMatlab(),
            data_loaders=[DrfLoader()],
        )
