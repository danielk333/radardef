"""
ConverterCollection gathers all given radars and extracts their converters, the collection can then convert
between any given source format to a target format given that atleast one radar contained such a converter.
"""

import logging
from pathlib import Path
from typing import Iterator

from radardef.components.converter_template import Converter
from radardef.tools.mpi_tools import CommBar
from radardef.types import SourceFormat, TargetFormat


class ConverterCollection:
    """
    Collection of all available converters from the available radar objects,
    provides a way to gather and provide converters for many different formats in one place.

    Args:
        converters: List of converters that the collections will be based upon.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, converters: list[Converter]):
        self._converters: dict[SourceFormat, dict] = dict()
        self.add_converters(converters)

    def __iter__(self) -> Iterator:
        """Iterate over all available converters."""
        return iter(self._converters)

    def add_converters(self, converters: list[Converter]) -> None:
        """Register several converters to the collection."""
        for converter in converters:
            self.__logger.debug(f"Registering {converter}")
            if converter.source_format in self._converters:
                self._converters[converter.source_format][converter.target_format] = converter
            else:
                self._converters[converter.source_format] = {converter.target_format: converter}

    def convert(
        self,
        path: Path,
        source_format: SourceFormat,
        target_format: TargetFormat,
        output_dir: Path,
        progress: bool | CommBar = False,
    ) -> list[Path] | None:
        """
        Converts the file/directory at the given path from a source format to a target format,
        """

        try:
            return self._converters[source_format][target_format].convert(path, output_dir, progress=progress)
        except KeyError:
            self.__logger.info(
                f'No converter from source format: "{source_format} \
                to target format: {target_format}, files affected: {path}'
            )

        return None

    def list_collection(self) -> str:
        """Lists available converters as a string."""

        st = ""
        for source_format in self._converters:
            st += f"{source_format}:\n"
            for target_format in self._converters[source_format]:
                st += f"├Target format> {target_format}\n"
        return st

    def available_target_formats(self, source_format: SourceFormat) -> list[TargetFormat]:
        """
        Get all target formats that is supported by the available converters for a specific source format
        """
        try:
            return list(self._converters[source_format].keys())
        except KeyError:
            return []

    def get_converter(self, source_format: SourceFormat, target_format: TargetFormat) -> Converter:
        return self._converters[source_format][target_format]

    def get_converters(self) -> list[Converter]:
        converters = []
        for source_format in self._converters:
            converters += list(self._converters[source_format].values())

        return converters
