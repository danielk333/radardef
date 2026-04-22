"""
This module contains functionality to load MUI -> h5 converted files in a standardized way. The data loader
is based on the Dataloader template
"""

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import h5py
import numpy as np
import numpy.typing as npt

from radardef.components import DataLoader
from radardef.radar_stations.mu.experiments import mu_exp
from radardef.radar_stations.mu.validators import H5
from radardef.types import BoundParams, ExpDef, Pointing, TargetFormat


class H5Loader(DataLoader):
    """Simplifies the way to load .h5 files converted from MUI"""

    __logger = logging.getLogger(__name__)

    converted_format = TargetFormat.H5
    validator = H5()

    @property
    def epoch_bounds(self) -> BoundParams:
        """Data epoch bounds in microseconds"""
        return self.__epoch_bounds

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.experiment.rx_channels

    def __init__(
        self,
        path: Path | str,
        exp_def: Optional[ExpDef] = None,
    ) -> None:
        """Loads a path to the dataloader, extracting metadata and other important specifications

        Args:
            path: path to data file

        """

        if not exp_def:
            exp_def = mu_exp

        super().__init__(path, exp_def)

        if self.path.is_dir():
            self.files = self._get_all_files_from_dir(self.path)
            self.__epoch_bounds, self.__sample_bounds = self._extract_bounds_from_list(self.files)
        else:
            self.files = [self.path]
            self.__epoch_bounds, self.__sample_bounds = self._extract_bounds(self.path)

        if len(self.__sample_bounds) != len(self.experiment.rx_channels):
            raise AttributeError(
                f"Amount of channels in experiment definition: {len(self.experiment.rx_channels)} \
                is not the same as the amount of channels in the data file: {len(self.__sample_bounds)}"
            )

    def bounds(self, channel: str | int) -> tuple[int, int]:
        """Sample bounds of the specific channel

        Args:
            channel: channel
        Returns:
            tuple of start and end sample
        Raises:
            Exception: channel is missing
        """

        if not isinstance(channel, int):
            channel = int(channel)

        if self._is_channel_present(channel):
            return self.__sample_bounds[channel]
        else:
            raise Exception(f"channel {channel} is missing in {dir}")

    def read(
        self,
        channel: str | int,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """
        Read data from loaded file

        Args:
            channel (optional): Channel to read data from
            start_sample (optional): Start of range to read, if empty all data will be read
            vector_length (optional): Number of samples (counting from start sample) to read,
                                    if empty all data will be read

        Returns:
            Complex data of length vector_length from give channel

        Raises:
            Exception: channel is missing

        NOTE:
            Ipp structure:

            ```
            0                   26       81                 166                520
            |    26 samples     |         |    85 samples    |
            |tx_start-----tx_end|_________|rx_start----rx_end|__________________|
            |---------------------------------ipp-------------------------------|
            ```

            included in raw data:
            ```
                |rx_start-----rx_end|
            ```
            padded data:
            ```
                | 81 zeros | 85 samples rx data | 354 zeros |
            ```
        """

        if not isinstance(channel, int):
            channel = int(channel)

        if not self._is_channel_present(channel):
            raise Exception(f"channel {channel} is missing in {dir}")

        if self.path.is_dir():
            if start_sample is not None:
                start_file = math.floor(start_sample / self.experiment.samples_per_file)
                index = start_sample % self.experiment.samples_per_file
            else:
                start_file = 0
                index = 0
                start_sample = 0

            if vector_length is not None:
                num_files = math.ceil(
                    ((start_sample % self.experiment.samples_per_file) + vector_length)
                    / self.experiment.samples_per_file
                )
                samples = vector_length
            else:
                num_files = len(self.files)
                samples = self.bounds(channel)[1]

            files = self.files[start_file : start_file + num_files]
            padded_data = np.empty((0,), dtype=np.complex128)
            for i, file in enumerate(files):
                h5file = self._open_h5_file(file)
                data = h5file["data"][channel - 1]
                h5file.close()
                if i == 0:
                    padded_data = self._flatten_and_zero_pad(data)
                else:
                    padded_data = np.concatenate((padded_data, self._flatten_and_zero_pad(data)), axis=0)

            return padded_data[index : index + samples]
        else:
            h5file = self._open_h5_file(self.path)
            data = h5file["data"][channel - 1]
            h5file.close()

            # flatten and fill with zeroes
            padded_data = self._flatten_and_zero_pad(data)

            if start_sample is None and vector_length is None:
                return padded_data
            elif start_sample is not None and vector_length is not None:
                return padded_data[start_sample : start_sample + vector_length]
            elif start_sample is None and vector_length is not None:
                return padded_data[0:vector_length]
            else:
                return padded_data[start_sample:]

    def pointing(self, sample: int) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        return Pointing(azimuth=0.0, elevation=90.0)

    def _flatten_and_zero_pad(self, data: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
        """
        Zero pads the data to make it match the true signal
        ```
        | 81 zeros | 85 samples rx data | 354 zeros |
        ```
        """

        pulses = data.shape[0]
        rx_start_samp = int(self.experiment.t_rx_start_usec / self.experiment.t_samp_usec)

        padded_data = np.zeros((pulses, self.experiment.ipp_samps), dtype=np.complex128)

        padded_data[:, rx_start_samp : rx_start_samp + data.shape[1]] = data

        return padded_data.reshape(-1)

    def _open_h5_file(self, path: Path) -> h5py.File:
        """Open h5 file and return reader"""

        try:
            h5file = h5py.File(str(path), "r")
        except FileNotFoundError:
            self.__logger.exception(f"Could not open file: {path}. File does not exist.")
            raise
        except OSError:
            self.__logger.exception(f"File {path} was not a h5 file, and was probably in binary format.")
            raise
        except UnicodeDecodeError:
            self.__logger.exception(f"File {path} was not a h5 file.")
            raise

        return h5file

    def _get_all_files_from_dir(self, path: Path) -> list[Path]:
        """Get all files available in dir"""
        paths: list[Path] = []
        if not path.is_dir():
            return paths

        paths = [f for f in path.iterdir() if f.is_file() and self.validate(f)]
        paths.sort()

        if len(paths) == 0:
            raise Exception(f"No valid h5 files at: {path}")
        return paths

    def _extract_bounds(self, path: Path) -> tuple[BoundParams, dict[str | int, tuple[int, int]]]:
        """Get bounds from h5 file"""

        h5file = self._open_h5_file(path)
        start_time = datetime.strptime(str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f")
        end_time = datetime.strptime(str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f")
        # time can be validated by end_time = start_time.timestamp() + (n_ipp * t_ipp_usec) * 1e-6, n_ipp = 512
        # if this is not matching maybe the measurement stopped  early
        epoch_bounds = BoundParams(
            ts_start_usec=int(start_time.timestamp() * 1e6),
            ts_end_usec=int(end_time.timestamp() * 1e6),
        )

        sample_bounds: dict[str | int, tuple[int, int]] = {}
        for j, data in enumerate(h5file["data"]):
            channel = j + 1

            if channel in self.experiment.rx_channels:
                pulses = len(data)
                ipp_length = int(self.experiment.t_ipp_usec / self.experiment.t_samp_usec)
                sample_bounds[channel] = (0, pulses * ipp_length)
            else:
                self.__logger.debug(
                    f"Channel: {j} is present in measurement file but not in experiment definition"
                )

        h5file.close()

        return epoch_bounds, sample_bounds

    def _extract_bounds_from_list(
        self, paths: list[Path]
    ) -> tuple[BoundParams, dict[str | int, tuple[int, int]]]:
        """Concatenate metadata from several h5 file"""

        sample_bounds: dict[str | int, tuple[int, int]] = {}

        # sort accoring to timestamp
        paths.sort()

        previous_end_point = "unknwn"

        for i, f in enumerate(paths):
            h5file = self._open_h5_file(f)

            # Extract meta data, should be general for all files
            if i == 0:
                start_time = datetime.strptime(
                    str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                )
            # Store end point of the directory
            if i == (len(paths) - 1):
                end_time = datetime.strptime(
                    str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                )

            # Validate that the data is sequential
            if i != 0:
                current_start_point = str(h5file.attrs["record_start_time"])[0:26]
                if previous_end_point != current_start_point:
                    self.__logger.warning(
                        f"The data is not sequential, there is a time gap before file {f.name}."
                        f"The end point of previous file was: {previous_end_point} and the start point of current file is: {current_start_point}"
                    )
            previous_end_point = str(h5file.attrs["record_end_time"])[0:26]

            # Calculate channel sample bounds
            ipp_length = int(self.experiment.t_ipp_usec / self.experiment.t_samp_usec)
            for j, data in enumerate(h5file["data"]):
                channel = j + 1
                if channel in self.experiment.rx_channels:
                    min_max = (0, len(data) * ipp_length)
                    if channel not in sample_bounds:
                        sample_bounds[channel] = min_max
                    else:
                        sample_bounds[channel] = tuple(np.add(sample_bounds[channel], min_max))
                else:
                    self.__logger.debug(
                        f"Channel: {j} is present in measurement file but not in experiment definition"
                    )
            h5file.close()

        epoch_bounds = BoundParams(
            ts_start_usec=int(start_time.timestamp() * 1e6),
            ts_end_usec=int(end_time.timestamp() * 1e6),
        )

        return epoch_bounds, sample_bounds

    def _is_channel_present(self, chnl: str | int) -> bool:
        """is channel present in the data"""
        return chnl in self.experiment.rx_channels
