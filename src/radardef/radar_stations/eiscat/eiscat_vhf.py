"""Eiscat VHF radar object"""

from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.eiscat.beams.vhf import eiscat_vhf_beam
from radardef.types import StationID

from .converters import MatBz2ToDrf, MatBz2ToHDF5
from .data_loaders import DrfLoader, HDF5Loader
from .validators import MatBz2


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
            converters=[MatBz2ToHDF5(), MatBz2ToDrf()],
            validator=MatBz2(),
            data_loaders=[DrfLoader, HDF5Loader],
        )
