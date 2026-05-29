"""
DataLoaderCollection gathers all given radars and extracts their data loaders, the collection can then
load data from any file given a compatible data loader is available.
"""

import logging
from pathlib import Path
from typing import Optional

from radardef.components.data_loader_template import DataLoader
from radardef.types import ExpDef, TargetFormat


class DataLoaderCollection:
    """
    Collection of all available data loaders from the available radar objects,
    provides a way to gather and provide loaders for many different formats in one place.

    Args:
        data_loaders: List of data loaders that the collection will be based upon.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, data_loaders: list[type[DataLoader]]):
        self.__data_loaders: dict[TargetFormat, type[DataLoader]] = dict()
        self.add_data_loaders(data_loaders)

    def load_data(
        self,
        path: Path,
        converted_format: Optional[TargetFormat] = None,
        experiment: Optional[ExpDef] = None,
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
        if not converted_format or converted_format == TargetFormat.UNKNOWN:
            converted_format = self._get_load_format(path)
        try:
            return self.__data_loaders[converted_format](path, experiment)
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

    def add_data_loaders(self, data_loaders: list[type[DataLoader]]) -> None:
        """Register data loaders to the collection."""
        for data_loader in data_loaders:
            self.__data_loaders[data_loader.converted_format] = data_loader

    def get_data_loaders(self) -> list[type[DataLoader]]:
        return list(self.__data_loaders.values())
