"""Eiscat UHF radar object"""

from pyant.beam import Beam
from pyant.models.measured import InterpMethods
from pyant.types import Parameters
from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.eiscat.beams.uhf import (
    eiscat_uhf_beam,
    eiscat_uhf_cassegrain_beam,
)
from radardef.types import BeamType, EiscatUHFLocation, StationID

from .converters import EiscatMatbzToDrf
from .data_loaders import DrfLoader
from .validators import EiscatMatlab


class EiscatUHF(RadarStation):
    """
    Eiscat UHF radar definition

    Args:
        location: Eiscat uhf radar location (tromso, kiruna, sodankyla)
        beam_type (optional): Beam type (measured, cassegrain)
        interpolation_method: What interpolation method to use

    """

    def __init__(
        self,
        location: EiscatUHFLocation = EiscatUHFLocation.KIRUNA,
        beam_type: BeamType = BeamType.MEASURED,
        interpolation_method: InterpMethods = "linear",
    ) -> None:

        beam: Beam
        params: Parameters
        if beam_type == BeamType.MEASURED:
            beam, params = eiscat_uhf_beam(interpolation_method)
        elif beam_type == BeamType.CASSEGRAIN:
            beam, params = eiscat_uhf_cassegrain_beam()

        match location:
            case EiscatUHFLocation.KIRUNA:
                super().__init__(
                    StationID.EISCAT_UHF_KIRUNA,
                    transmitter=False,
                    receiver=True,
                    lat=67.86055555555555,
                    lon=20.435277777777777,
                    alt=418.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=100,
                    frequency=930.0e6,
                    converters=[EiscatMatbzToDrf()],
                    validator=EiscatMatlab(),
                    data_loaders=[DrfLoader()],
                )
            case EiscatUHFLocation.SODANKYLA:
                super().__init__(
                    StationID.EISCAT_UHF_SODANKYLA,
                    transmitter=False,
                    receiver=True,
                    lat=67.36361111111111,
                    lon=26.626944444444444,
                    alt=197.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=100,
                    frequency=930.0e6,
                    converters=[EiscatMatbzToDrf()],
                    validator=EiscatMatlab(),
                    data_loaders=[DrfLoader()],
                )
            case EiscatUHFLocation.TROMSO:
                super().__init__(
                    StationID.EISCAT_UHF_TROMSO,
                    transmitter=True,
                    receiver=True,
                    lat=69.58638888888889,
                    lon=19.227222222222224,
                    alt=86.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=100,
                    power=1.6e6,
                    frequency=930.0e6,
                    converters=[EiscatMatbzToDrf()],
                    validator=EiscatMatlab(),
                    data_loaders=[DrfLoader()],
                )
