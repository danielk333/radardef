"""
Format validator gathers all given radars and extracts their source validators, the collection can then solve
what format any given file is, given that the format is the source format of atleast one radar.
"""

import logging
from collections.abc import Callable
from pathlib import Path

from radardef.components.radar_station_template import RadarStation
from radardef.types import SourceFormat


class FormatCollection:
    """
    Collection of all available validators from the available radar objects,
    provides a way to gather and provide source validators for many different formats in one place and make
    it possible to solve the source format of a given file.

    Args:
        radars: List of radars that the collections validators will be extracted from.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, radars: list[RadarStation]) -> None:

        self.__formats: dict[SourceFormat, Callable[[Path], bool]] = dict()

        for radar in radars:
            if radar.validator is not None:
                self.__logger.info(f"registering  {radar.validator}")
                self._register_validator(radar.validator.format, radar.validator.validate)

    def _register_validator(self, source_format: SourceFormat, validator: Callable) -> None:
        """Register a validator related to a source format to collection."""
        self.__formats[source_format] = validator

    def get_format(self, path: Path) -> SourceFormat:
        """Returns the source format of the file."""

        for source_format, validator in self.__formats.items():
            if validator(path):
                return source_format
        return SourceFormat.UNKNOWN

    def is_format(self, path: Path, source_format: SourceFormat) -> bool:
        """Validates that the file is of the expected format"""
        try:
            return self.__formats[source_format](path)
        except KeyError:
            self.__logger.debug(f"No validator available for {source_format} format")
            return False

    def list_formats(self) -> str:
        """Lists formats with a validator as a string"""

        st = ""
        if self.__formats is not None:
            for source_format, _ in self.__formats.items():
                st += f">{source_format}\n"
        return st
