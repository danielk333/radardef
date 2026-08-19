"""Eiscat Svalbard Radar (ESR) object"""

from radardef.radar_station import RadarStation
from radardef.radar_stations.eiscat.beams.esr import (
    esr_32m_cassegrain_beam,
    esr_42m_cassegrain_beam,
)
from radardef.types import DishDiameter, StationID

from .converters import MatBz2ToDrf, MatBz2ToHDF5
from .data_loaders import DrfLoader
from .validators import MatBz2


class ESR(RadarStation):
    """
    Eiscat Svalbard Radar (ESR) definition

    Args:
        dish_diameter: Dish diameter (32m, 42m)

    """

    def __init__(
        self,
        dish_diameter: DishDiameter = DishDiameter.ESR_32M,
    ) -> None:

        if dish_diameter == DishDiameter.ESR_32M:
            beam, params = esr_32m_cassegrain_beam()
            station_id = StationID.ESR_32M
            lon = 16.0758715
            min_elevation = 15.0
        elif dish_diameter == DishDiameter.ESR_42M:
            beam, params = esr_42m_cassegrain_beam()
            station_id = StationID.ESR_42M
            lon = 16.081483
            min_elevation = 81.6  # Fixed to this elevation!

        super().__init__(
            station_id,
            transmitter=True,
            receiver=True,
            lat=78.153145,
            lon=lon,
            alt=185,
            beam=beam,
            beam_parameters=params,
            min_elevation=min_elevation,
            noise_temperature=70,
            power=1e6,
            frequency=500e6,
            converters=[MatBz2ToHDF5(), MatBz2ToDrf()],
            validator=MatBz2(),
            data_loaders=[DrfLoader],
        )
