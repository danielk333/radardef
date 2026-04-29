"""Template class for all data loaders to inherit from"""

from abc import abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt

from radardef.components import Validator
from radardef.types import BoundParams, ExpDef, Pointing, TargetFormat


class DataLoader:
    """
    Data loader template, should be inherited by all data loaders

    Args:
        experiment: Experiment definition to be able to decode the data


    """

    converted_format: TargetFormat
    validator: Validator[TargetFormat]

    @property
    def experiment(self) -> ExpDef:
        """Experiment specifications"""
        if not self._experiment:
            raise ValueError("Experiment needs to be defined to be able to load data")
        return self._experiment

    @property
    def path(self) -> Path:
        """Data path"""
        return self._path

    @property
    @abstractmethod
    def epoch_bounds(self) -> BoundParams:
        """Data epoch bounds in microseconds"""
        pass

    @property
    @abstractmethod
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        pass

    def __init__(
        self,
        path: Path | str,
        exp_def: Optional[ExpDef] = None,
    ):
        self._experiment = exp_def
        self._path = Path(path)

    @classmethod
    def validate(cls, path: Path) -> bool:
        """Validate that the file format compatible with the loader"""
        return cls.validator.validate(path)

    @abstractmethod
    def bounds(self, channel: str | int) -> tuple[int, int]:
        """Sample bounds of the specific channel"""
        pass

    @abstractmethod
    def read(
        self,
        channel: Optional[str | int | list[str] | list[int]] = None,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """

        Args:
            channel (optional): Channel to read data from, single channel or list of channels. If not specified all channels will be returned.
            start_sample (optional): sample to start reading from, if not given bounds start will be used
            vector_length (optional): Amount of samples to read from start_sample,
                if not given all samples will be read

        Returns:
            Complex data from channel/channels. Shape for single channel: (vector_length,) otherwise: (channels, vector_length)
        """
        pass

    # TODO: change to carthesian coordinates
    @abstractmethod
    def pointing(self, sample: int) -> Pointing:
        """
        Pointing data, data describing the radar pointing direction in spherical coordinates

        """
        pass
