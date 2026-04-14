"""Template of a Radar station"""

import logging
from pathlib import Path
from typing import Optional

from numpy.typing import NDArray
from pyant import Beam
from pyant.types import Parameters
from spacecoords import celestial, frames, spherical

from radardef.components.converter_template import Converter
from radardef.components.data_loader_template import DataLoader
from radardef.components.validator_template import Validator
from radardef.types import ExpDef, TargetFormat


class RadarStation:
    """
    Definition of a radar station.

    Args:
        station_id: A unique string that identifies a radar station.
        transmitter: If the radar station has a transmitter.
        receiver: If the radar station has a receiver.
        lat: Geographical latitude of radar station in decimal degrees  (North+).
        lon: Geographical longitude of radar station in decimal degrees (East+).
        alt: Geographical altitude above geoid surface of radar station in meter.
        beam: The radar beam model for this station.
        beam_parameters: The parameters for the radar beam model for this station.
        min_elevation (optional): The minimum elevation the radar can measure at.
        noise_temperature (optional): The noise temperature in Kelvins intrinsic to the radar receiver.
        power (optional): The maximum power in Watts the radar transmitter can deliver.
        power_per_element (optional): power_per_element
        frequency (optional): The frequency the radar operates at.
        validator (optional): Validator to validate the correct data format from the station
        converters (optional):  List of converters that can converte from the source format to other formats
        data_loaders (optional):  Data loader object compatible with the converted files

    """

    __logger = logging.getLogger(__name__)

    @property
    def station_id(self) -> str:
        """A unique string that identifies a radar station."""
        return self.__station_id

    @property
    def transmitter(self) -> bool:
        """If the radar station has a transmitter."""
        return self.__transmitter

    @property
    def receiver(self) -> bool:
        """If the radar station has a receiver."""
        return self.__receiver

    @property
    def lat(self) -> float:
        """Geographical latitude of radar station in decimal degrees  (North+)."""
        return self.__lat

    @property
    def lon(self) -> float:
        """Geographical longitude of radar station in decimal degrees (East+)."""
        return self.__lon

    @property
    def alt(self) -> float:
        """Geographical altitude above geoid surface of radar station in meter."""
        return self.__alt

    @property
    def beam(self) -> Beam:
        """The radar beam for this station."""
        return self.__beam

    @property
    def beam_parameters(self) -> Parameters:
        """The parameters for the radar beam model for this station."""
        return self.__beam_parameters

    @property
    def ecef(self) -> NDArray:
        """The ITRS coordinates of the radar station."""
        return self.__ecef

    @property
    def ecef_lat(self) -> float:
        """The latitude of the ITRS coordinates of the radar station."""
        return self.__ecef_lat

    @property
    def ecef_lon(self) -> float:
        """The longitude of the ITRS coordinates of the radar station."""
        return self.__ecef_lon

    @property
    def ecef_alt(self) -> float:
        """The altitude of the ITRS coordinates of the radar station."""
        return self.__ecef_alt

    @property
    def min_elevation(self) -> float | None:
        """The minimum elevation the radar can measure at."""
        return self.__min_elevation

    @property
    def noise_temperature(self) -> float | None:
        """The noise temperature in Kelvins intrinsic to the radar receiver."""
        return self.__noise_temperature

    @property
    def power(self) -> float | None:
        """The maximum power in Watts the radar transmitter can deliver."""
        return self.__power

    @property
    def power_per_element(self) -> float | None:
        """Power per element."""
        return self.__power_per_element

    @property
    def frequency(self) -> float | None:
        """The frequency the radar operates at."""
        return self.__frequency

    @property
    def validator(self) -> Validator | None:
        """Validator to confirm that the"""
        return self.__validator

    def enu(self, ecefs: NDArray) -> NDArray:
        """Converts a set of ECEF states to local ENU coordinates using geocentric zenith."""

        rel_ = ecefs.copy()
        rel_[:3, :] = rel_[:3, :] - self.ecef[:, None]
        rel_[:3, :] = frames.ecef_to_enu(
            self.ecef_lat,
            self.ecef_lon,
            rel_[:3, :],
            degrees=True,
        )
        if ecefs.shape[0] > 3:
            rel_[3:, :] = frames.ecef_to_enu(
                self.ecef_lat,
                self.ecef_lon,
                rel_[3:, :],
                degrees=True,
            )

        return rel_

    def __init__(
        self,
        station_id: str,
        transmitter: bool,
        receiver: bool,
        lat: float,
        lon: float,
        alt: float,
        beam: Beam,
        beam_parameters: Parameters,
        min_elevation: Optional[float] = None,
        noise_temperature: Optional[float] = None,
        power: Optional[float] = None,
        power_per_element: Optional[float] = None,
        frequency: Optional[float] = None,
        converters: Optional[list[Converter]] = None,
        validator: Optional[Validator] = None,
        data_loaders: Optional[list[type[DataLoader]]] = None,
    ) -> None:

        self.__station_id = station_id
        self.__transmitter = transmitter
        self.__receiver = receiver
        self.__lat = lat
        self.__lon = lon
        self.__alt = alt
        self.__beam = beam
        self.__beam_parameters = beam_parameters
        self.__ecef = celestial.geodetic_to_ITRS(lat, lon, alt, degrees=True)
        ecef_lla = spherical.cart_to_sph(self.ecef, degrees=True)
        self.__ecef_lat = ecef_lla[1]
        self.__ecef_lon = 90 - ecef_lla[0]
        self.__ecef_alt = ecef_lla[2]
        self.__min_elevation = min_elevation
        self.__noise_temperature = noise_temperature
        self.__power = power
        self.__power_per_element = power_per_element
        self.__frequency = frequency
        self.__validator = validator
        self.__converters: dict[TargetFormat, Converter] = dict()
        self.__data_loaders: dict[TargetFormat, type[DataLoader]] = dict()

        if converters is not None:
            for converter in converters:
                self.add_converter(converter)

        if data_loaders is not None:
            for data_loader in data_loaders:
                self.add_data_loader(data_loader)

    def get_converters(self) -> list[Converter]:
        """Get all converters connected to this radar"""
        return list(self.__converters.values())

    def get_data_loaders(self) -> list[type[DataLoader]]:
        """Get all data loaders connected to this radar"""
        return list(self.__data_loaders.values())

    def add_converter(self, converter: Converter) -> None:
        """Add a converter to this radar"""
        self.__converters[converter.target_format] = converter

    def add_data_loader(self, data_loader: type[DataLoader]) -> None:
        """Add a data loader to this radar"""
        self.__data_loaders[data_loader.converted_format] = data_loader

    def convert(self, path: Path, target_format: TargetFormat, dst: Path) -> list[Path] | None:
        """Convert data from this radar to a specific format"""

        if self.__validator is not None:
            if not self.__validator.validate(path):
                self.__logger.error("Source format not supported")
                return None
        else:
            self.__logger.error("No source validator available, will try to convert anyways")

        try:
            return self.__converters[target_format].convert(path, dst)
        except KeyError:
            self.__logger.error("Not possible to convert to the wanted format, no converter available")

        return None

    def load_data(
        self, path: Path, converted_format: Optional[TargetFormat] = None, experiment: Optional[ExpDef] = None
    ) -> DataLoader | None:
        """Load converted data from this radar"""
        if converted_format is None:
            for data_loader in self.__data_loaders.values():
                if data_loader.validate(path):
                    return data_loader(path, experiment)
            self.__logger.error("Source format not supported")
        else:
            try:
                if self.__data_loaders[converted_format].validate(path):
                    return self.__data_loaders[converted_format](path, experiment)
                else:
                    self.__logger.error("Source format not supported")
            except KeyError:
                self.__logger.error("Not possible to load the wanted format, no loader available")

        return None
