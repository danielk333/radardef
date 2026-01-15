"""
ConverterCollection gathers all given radars and extracts their converters, the collection can then convert
between any given source format to a target format given that atleast one radar contained such a converter.
"""

import logging
from pathlib import Path
from typing import Iterator

import radardef.tools as tools
from radardef.components.converter_template import Converter
from radardef.components.radar_station_template import RadarStation
from radardef.types import SourceFormat, TargetFormat

try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:

    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()  # type: ignore[assignment]


class ConverterCollection:
    """
    Collection of all available converters from the available radar objects,
    provides a way to gather and provide converters for many different formats in one place.

    Args:
        radars: List of radars that the collections converters will be extracted from.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, radars: list[RadarStation]):
        self.__converters: dict[SourceFormat, dict] = dict()

        for radar in radars:
            self._register_converters(radar.get_converters())

    def __iter__(self) -> Iterator:
        """Iterate over all available converters."""
        return iter(self.__converters)

    def _register_converters(self, converters: list[Converter]) -> None:
        """Register several converters to the collection."""
        for converter in converters:
            self.__logger.info(f"Registering {converter}")

            if converter.source_format in self.__converters:
                self.__converters[converter.source_format][converter.target_format] = converter
            else:
                self.__converters[converter.source_format] = {converter.target_format: converter}

    @tools.MPI_target_args(range(1, 3), loading_bar=True, MPI=comm.size > 1)
    def convert(
        self, path: Path, source_format: SourceFormat, target_format: TargetFormat, output_dir: Path
    ) -> list[Path] | None:
        """
        Converts the file/directory at the given path from a source format to a target format,
        parrellized with MPI if needed.
        For parallelization path list and source_format list has to be of the same size.
        """

        try:
            return self.__converters[source_format][target_format].convert(path, output_dir)
        except KeyError:
            self.__logger.info(
                f'No converter from source format: "{source_format} \
                to target format: {target_format}, files affected: {path}'
            )
        return None

    def list_collection(self) -> str:
        """Lists available converters as a string."""

        st = ""
        for source_format in self.__converters:
            st += f"{source_format}:\n"
            for target_format in self.__converters[source_format]:
                st += f"├Target format> {target_format}\n"
        return st

    def get_converter(self, source_format: SourceFormat, target_format: TargetFormat) -> Converter:
        return self.__converters[source_format][target_format]
