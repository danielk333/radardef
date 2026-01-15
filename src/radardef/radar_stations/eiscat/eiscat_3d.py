"""Eiscat 3D radar object"""

from pyant.beam import Beam
from pyant.types import Parameters
from radardef.components.radar_station_template import RadarStation
from radardef.radar_stations.eiscat.beams.e3d import (
    eiscat_3d_single_subarray_beam,
    eiscat_3d_stage1_beam,
    eiscat_3d_stage1_interp_beam,
    eiscat_3d_stage2_beam,
    eiscat_3d_stage2_interp_beam,
)
from radardef.types import Eiscat3DLocation, Stage, StationID


class Eiscat3D(RadarStation):
    """
    Eiscat 3D radar definition

    Args:
        location: Eiscat 3d radar location (skibotn, karesuvanto, kaiseniemi)
        stage (optional): Stage of the radar (single, stage_1, stage_2), default single
        interpolation (optional): Should interpolation be used, default False

    """

    def __init__(
        self,
        location: Eiscat3DLocation = Eiscat3DLocation.KAISENIEMI,
        stage: Stage = Stage.SINGLE,
        interpolation: bool = False,
    ):

        beam: Beam
        params: Parameters
        if interpolation:
            if stage is Stage.SINGLE:
                self.__logger.warning("There is no interpolation beam available for a single subarray")
            elif stage is Stage.STAGE_1:
                beam, params = eiscat_3d_stage1_interp_beam()
            elif stage is Stage.STAGE_2:
                beam, params = eiscat_3d_stage2_interp_beam()
            else:
                self.__logger.warning("No available beam for the given stage")
        else:
            if stage is Stage.SINGLE:
                beam, params = eiscat_3d_single_subarray_beam()
            elif stage is Stage.STAGE_1:
                beam, params = eiscat_3d_stage1_beam()
            elif stage is Stage.STAGE_2:
                beam, params = eiscat_3d_stage2_beam()
            else:
                self.__logger.warning("No available beam for the given stage")

        match location:
            case Eiscat3DLocation.SKIBOTN:
                super().__init__(
                    station_id=StationID.EISCAT_3D_SKIBOTN,
                    transmitter=True,
                    receiver=True,
                    lat=69.34023844,
                    lon=20.313166,
                    alt=0.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=150,
                    power=3.276e6,
                    power_per_element=1e3,
                    frequency=233e6,
                )
            case Eiscat3DLocation.KARESUVANTO:
                super().__init__(
                    station_id=StationID.EISCAT_3D_KARESUVANTO,
                    transmitter=False,
                    receiver=True,
                    lat=68.463862,
                    lon=22.458859,
                    alt=0.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=150,
                    frequency=233e6,
                )
            case Eiscat3DLocation.KAISENIEMI:
                super().__init__(
                    station_id=StationID.EISCAT_3D_KAISENIEMI,
                    transmitter=False,
                    receiver=True,
                    lat=68.148205,
                    lon=19.769894,
                    alt=0.0,
                    beam=beam,
                    beam_parameters=params,
                    min_elevation=30,
                    noise_temperature=150,
                    frequency=233e6,
                )
            case _:
                super().__init__(
                    station_id=StationID.UNKNOWN,
                    transmitter=False,
                    receiver=False,
                    lat=0.0,
                    lon=0.0,
                    alt=0.0,
                    beam=None,
                    beam_parameters=None,
                    min_elevation=0,
                    noise_temperature=0,
                    frequency=0,
                )
