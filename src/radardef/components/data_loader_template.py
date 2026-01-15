"""Template class for all data loaders to inherit from"""

from abc import abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt

from radardef.components import Validator
from radardef.types import Metadata, Pointing, TargetFormat


class DataLoader:
    """
    Data loader template, should be inherited by all data loaders

    Args:
        converted_format: Format of the converted data
        validator: validator for the converted format to see that a file is compatible

    """

    @property
    def converted_format(self) -> TargetFormat:
        """Converted format of the data compatible with the data loader"""
        return self.__converted_format

    @property
    @abstractmethod
    def meta(self) -> Metadata:
        """Metadata, containing experiment data and bounds data"""
        pass

    # TODO: change to carthesian coordinates
    @property
    @abstractmethod
    def pointing(self) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        pass

    @property
    @abstractmethod
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        pass

    def __init__(self, converted_format: TargetFormat, validator: Validator[TargetFormat]):
        self.__converted_format = converted_format
        self.__validator = validator

    @abstractmethod
    def load(self, path: Path | str) -> None:
        """Loads a path to the dataloader, extracting metadata and other important specifications"""
        pass

    def validate(self, path: Path) -> bool:
        """Validate that the file format compatible with the loader"""
        return self.__validator.validate(path)

    @abstractmethod
    def bounds(self, channel: str | int) -> tuple[int, int]:
        """Sample bounds of the specific channel"""
        pass

    @abstractmethod
    def read(
        self,
        channel: str | int,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """

        Args:
            channel: channel to read data from
            start_sample (optional): sample to start reading from, if not given bounds start will be used
            vector_length (optional): Amount of samples to read from start_sample,
                if not given all samples will be read

        Returns:
            Complex data of given channel
        """
        pass
