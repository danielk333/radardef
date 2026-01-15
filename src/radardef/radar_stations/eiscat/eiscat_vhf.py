"""Eiscat VHF radar object"""

from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.eiscat.beams.vhf import eiscat_vhf_beam
from radardef.types import StationID

from .converters import EiscatMatbzToDrf
from .data_loaders import DrfLoader
from .validators import EiscatMatlab


class EiscatVHF(RadarStation):
    """Eiscat VHF radar definition"""

    def __init__(self) -> None:
        beam, params = eiscat_vhf_beam()
        super().__init__(
            StationID.EISCAT_VHF,
            transmitter=True,
            receiver=True,
            lat=69.5866115,
            lon=19.221555,
            alt=85.0,
            beam=beam,
            beam_parameters=params,
            noise_temperature=100,
            power=1.6e6,
            frequency=224e6,
            converters=[EiscatMatbzToDrf()],
            validator=EiscatMatlab(),
            data_loaders=[DrfLoader()],
        )
