"""
DataLoaderCollection gathers all given radars and extracts their data loaders, the collection can then
load data from any file given a compatible data loader is available.
"""

import copy
import logging
from pathlib import Path

import numpy as np

from radardef.components.data_loader_template import DataLoader
from radardef.components.radar_station_template import RadarStation
from radardef.types import TargetFormat


class DataLoaderCollection:
    """
    Collection of all available data loaders from the available radar objects,
    provides a way to gather and provide loaders for many different formats in one place.

    Args:
        radars: List of radars that the collections data loaders will be extracted from.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, radars: list[RadarStation]):
        self.__data_loaders: dict[TargetFormat, DataLoader] = dict()

        for radar in radars:
            for data_loader in radar.get_data_loaders():
                self._register_data_loader(data_loader)

    def load_data(
        self,
        path: Path,
        converted_format: TargetFormat = TargetFormat.UNKNOWN,
    ) -> DataLoader | None:
        """
        Get a dataloader compatible with the file at the path.

        Args:
            path: Path to file that should be loaded
            converted_format (optional): Format of the converted data,
                if not specified the format will be found by the validator.

        Returns:
            A compatible dataloader if available, otherwise None

        """

        if converted_format is TargetFormat.UNKNOWN:
            converted_format = self._get_load_format(path)
        try:
            loader = copy.deepcopy(self.__data_loaders[converted_format])
            loader.load(path)
            return loader
        except KeyError:
            self.__logger.info(
                f"No dataloader available for format: {converted_format}, files affected: {path}"
            )
        return None

    def _get_load_format(self, path: Path) -> TargetFormat:
        """Determine converted format of given file."""

        for converted_format, data_loader in self.__data_loaders.items():
            if data_loader.validate(path):
                return converted_format

        self.__logger.warning("Could not find any matching validator for the given format")
        return TargetFormat.UNKNOWN

    def _register_data_loader(self, data_loader: DataLoader) -> None:
        """Register a data loader to the collection."""
        self.__data_loaders[data_loader.converted_format] = data_loader
