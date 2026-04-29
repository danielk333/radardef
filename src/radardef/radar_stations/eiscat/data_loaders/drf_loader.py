"""
Class and freestanding functions to load metadata and data from a file converted from Eiscat mat.bz2
to DRF format. The data loader is based on the DataLoader template.
"""

import configparser
from pathlib import Path
from typing import Optional

import digital_rf
import numpy as np
import numpy.typing as npt

from radardef.components.data_loader_template import DataLoader
from radardef.radar_stations.eiscat.experiments import get_experiment
from radardef.radar_stations.eiscat.validators import DRF
from radardef.types import (
    Boundparam,
    BoundParams,
    ExpDef,
    Expparam,
    Metaparam,
    Pointing,
    TargetFormat,
)


class DrfLoader(DataLoader):
    """Simplifies the way to load DRF files converted from eiscat"""

    converted_format = TargetFormat.DRF
    validator = DRF()

    @property
    def epoch_bounds(self) -> BoundParams:
        """Data epoch bounds in microseconds"""
        return self.__epoch_bounds

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.__channel_reader.get_channels()

    def __init__(
        self,
        path: Path | str,
        exp_def: Optional[ExpDef] = None,
    ) -> None:
        super().__init__(path, exp_def)

        if not self.path.is_dir():
            raise Exception(f"<dir> must be directory path, {self.path}")

        if not self._experiment:
            meta_file = configparser.ConfigParser()
            meta_file.read(self.path / "metadata.ini")
            self._experiment = get_experiment(
                group=meta_file.get(Metaparam.EXPERIMENT, Expparam.NAME),
                version=meta_file.get(Metaparam.EXPERIMENT, Expparam.VERSION),
            )

        self.__channel_reader = digital_rf.DigitalRFReader(str(self.path))

        pointing_dir = self.path / "pointing"
        if not pointing_dir.is_dir():
            raise Exception(f"<dir/pointing> must be directory path, {self.path}")

        self.__meta_reader = digital_rf.DigitalMetadataReader(str(pointing_dir))
        idx_start, idx_end = self.__meta_reader.get_bounds()
        self._pointing_inds = list(self.__meta_reader.read(idx_start, idx_end).keys())
        self.__epoch_bounds = self._extract_bounds(self.path)

    def bounds(self, channel: str | int) -> tuple[int, int]:
        """Sample bounds of the specific channel

        Args:
            channel: channel
        Returns:
            tuple of start and end sample
        Raises:
            Exception: channel is missing
        """

        if not isinstance(channel, str):
            channel = str(channel)

        if channel not in self.__channel_reader.get_channels():
            raise Exception(f"channel {channel} missing in {dir}")

        idx_first, idx_last = self.__channel_reader.get_bounds(channel)
        return idx_first, idx_last + 1

    def read(
        self,
        channel: Optional[str | int | list[str] | list[int]] = None,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """
        Read data from loaded file

        Args:
            channel (optional): Channel to read data from, single channel or list of channels. If not specified all channels will be returned.
            start_sample (optional): Start of range to read, if empty all data will be read
            vector_length (optional): Number of samples (counting from start sample) to read,
                                    if empty all data will be read

        Returns:
            Complex data from channel shape: (vector_length,)

        Raises:
            Exception: channel is missing
        """
        if channel:
            if not isinstance(channel, str):
                channel = str(channel)

            if channel not in self.__channel_reader.get_channels():
                raise Exception(f"channel {channel} missing in {dir}")
        else:
            channel = self.experiment.rx_channels[0]

        if start_sample is None or vector_length is None:
            bound_start, bound_end = self.bounds(channel)
            return self.__channel_reader.read_vector_1d(bound_start, bound_end - 1, channel)
        else:
            return self.__channel_reader.read_vector_1d(start_sample, vector_length, channel)

    def pointing(self, sample: int) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        if self.__meta_reader is None:
            return Pointing(azimuth=0, elevation=0)
        else:
            for p_ind in self._pointing_inds:
                if sample < p_ind:
                    data = self.__meta_reader.read(p_ind)[p_ind]
                    return Pointing(data["azimuth"], data["elevation"])

            data = self.__meta_reader.read(self._pointing_inds[0])[self._pointing_inds[0]]
            return Pointing(data["azimuth"], data["elevation"])

    def _extract_bounds(self, path: Path) -> BoundParams:
        meta_file = configparser.ConfigParser()
        meta_file.read(self.path / "metadata.ini")

        bounds = BoundParams(
            ts_start_usec=meta_file.getfloat(Metaparam.BOUNDS, Boundparam.TS_START_USEC),
            ts_end_usec=meta_file.getfloat(Metaparam.BOUNDS, Boundparam.TS_END_USEC),
        )

        return bounds
