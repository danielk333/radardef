"""
This module contains functionality to load MUI -> h5 converted files in a standardized way. The data loader
is based on the Dataloader template
"""

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import h5py
import numpy as np
import numpy.typing as npt
import scipy.constants

from radardef.components import DataLoader
from radardef.radar_stations.mu.validators import H5
from radardef.types import BoundParams, ExpParams, Metadata, Pointing, TargetFormat


class H5Loader(DataLoader):
    """Simplifies the way to load .h5 files converted from MUI"""

    __logger = logging.getLogger(__name__)

    @property
    def meta(self) -> Metadata:
        """Metadata, containing experiment data and bounds data"""
        return self.__meta

    @property
    def pointing(self) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        return Pointing(data=[(0, {"azimuth": 0.0, "elevation": 90.0})], sample_rate=1)

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.meta.experiment.rx_channels

    def __init__(self) -> None:
        super().__init__(TargetFormat.H5, H5())
        self.__meta = Metadata(ExpParams(), BoundParams())
        self.__sample_bounds: dict[str | int, tuple[int, int]] = {}
        self.__t_ipp_usec = 3120
        self.__t_rx_start_usec = 486
        self.__t_samp_usec = 6
        self.__sample_rate = 1 / (self.__t_samp_usec * 1e-6)
        self.__radar_frequency = 46.5  # TODO: h5file.attrs["tx_frequency"] returns a 0 array
        self._ipp_samps = int(self.__t_ipp_usec / self.__t_samp_usec)
        self.__code = np.kron(
            np.array(
                [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
                dtype=np.float64,
            ),
            np.ones(2),
        ).astype(np.float64)
        self.__samples_per_file = 266240

    def load(self, path: Path | str) -> None:
        """Loads a path to the dataloader, extracting metadata and other important specifications

        Args:
            path: path to data file

        """

        self.__path = Path(path).resolve()
        if self.__path.is_dir():
            files = self._get_all_files_from_dir(self.__path)
            self.__meta, self.__sample_bounds = self._extract_meta_from_list(files)
        else:
            self.__meta, self.__sample_bounds = self._extract_meta(self.__path)

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

        if self.__path.is_dir():
            files = self._get_all_files_from_dir(self.__path)

            if start_sample is not None:
                start_file = math.floor(start_sample / self.__samples_per_file)
                index = start_sample % self.__samples_per_file
            else:
                start_file = 0
                index = 0
                start_sample = 0

            if vector_length is not None:
                num_files = math.ceil(
                    ((start_sample % self.__samples_per_file) + vector_length) / self.__samples_per_file
                )
                samples = vector_length
            else:
                num_files = len(files)
                samples = self.bounds(channel)[1]

            files = files[start_file : start_file + num_files]
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
            h5file = self._open_h5_file(self.__path)
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

    def _flatten_and_zero_pad(self, data: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
        """
        Zero pads the data to make it match the true signal
        ```
        | 81 zeros | 85 samples rx data | 354 zeros |
        ```
        """

        pulses = len(data)
        rx_start_samp = int(self.meta.experiment.t_rx_start_usec / self.meta.experiment.t_samp_usec)

        padded_data = np.zeros((self._ipp_samps * pulses), dtype=np.complex128)

        for ipp_n, rx_batch in enumerate(data):
            offset = int(ipp_n * self._ipp_samps) + rx_start_samp
            padded_data[offset : offset + len(rx_batch)] = rx_batch

        return padded_data

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

    def _extract_meta(self, path: Path) -> tuple[Metadata, dict[str | int, tuple[int, int]]]:
        """Get metadata from h5 file"""

        h5file = self._open_h5_file(path)

        experiment = ExpParams(
            name=h5file.attrs["filename"],
            radar_frequency=self.__radar_frequency,
            t_ipp_usec=self.__t_ipp_usec,
            sample_rate=self.__sample_rate,
            ipp_samps=self._ipp_samps,
            t_samp_usec=self.__t_samp_usec,
            t_rx_start_usec=self.__t_rx_start_usec,
            t_rx_end_usec=self.__t_rx_start_usec + 6 * 85,
            t_tx_start_usec=0,
            t_tx_end_usec=26 * self.__t_samp_usec,  # code length * t_samp
            rx_channels=h5file["rx_channels"][()],
            pulse=2,
            code=self.__code,
            wavelength=scipy.constants.c / (self.__radar_frequency * 1e6),
        )

        start_time = datetime.strptime(str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f")
        end_time = datetime.strptime(str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f")
        # time can be validated by end_time = start_time.timestamp() + (n_ipp * t_ipp_usec) * 1e-6, n_ipp = 512
        # if this is not matching maybe the measurement stopped  early
        bounds = BoundParams(
            ts_start_usec=start_time.timestamp(),
            ts_end_usec=end_time.timestamp(),
        )

        sample_bounds: dict[str | int, tuple[int, int]] = {}
        for channel, data in enumerate(h5file["data"]):
            pulses = len(data)
            ipp_length = int(experiment.t_ipp_usec / experiment.t_samp_usec)
            sample_bounds[channel + 1] = (0, pulses * ipp_length)
        h5file.close()

        return Metadata(experiment, bounds), sample_bounds

    def _extract_meta_from_list(self, paths: list[Path]) -> tuple[Metadata, dict[str | int, tuple[int, int]]]:
        """Concatenate metadata from several h5 file"""

        sample_bounds: dict[str | int, tuple[int, int]] = {}
        experiment = ExpParams()

        # sort accoring to timestamp
        paths.sort()
        for i, f in enumerate(paths):
            h5file = self._open_h5_file(f)

            if i == 0:
                experiment = ExpParams(
                    name=h5file.attrs["filename"],
                    radar_frequency=self.__radar_frequency,
                    t_ipp_usec=self.__t_ipp_usec,
                    sample_rate=self.__sample_rate,
                    ipp_samps=self._ipp_samps,
                    t_samp_usec=self.__t_samp_usec,
                    t_rx_start_usec=self.__t_rx_start_usec,
                    t_rx_end_usec=self.__t_rx_start_usec + 6 * 85,
                    t_tx_start_usec=0,
                    t_tx_end_usec=27 * self.__t_samp_usec,  # (code length + 1) * t_samp,
                    rx_channels=h5file["rx_channels"][()],
                    pulse=2,
                    code=np.kron(
                        np.array(
                            [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
                            dtype=np.float64,
                        ),
                        np.ones(2, dtype=np.float64),
                    ).astype(np.float64),
                    wavelength=scipy.constants.c / (self.__radar_frequency * 1e6),
                )

                start_time = datetime.strptime(
                    str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                )

            elif i == (len(paths) - 1):
                end_time = datetime.strptime(
                    str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                )

            ipp_length = int(experiment.t_ipp_usec / experiment.t_samp_usec)
            for i, data in enumerate(h5file["data"]):
                channel = i + 1
                if channel in experiment.rx_channels:
                    min_max = (0, len(data) * ipp_length)
                    if channel not in sample_bounds:
                        sample_bounds[channel] = min_max
                    else:
                        sample_bounds[channel] = tuple(np.add(sample_bounds[channel], min_max))

            h5file.close()

        bounds = BoundParams(
            ts_start_usec=start_time.timestamp(),
            ts_end_usec=end_time.timestamp(),
        )

        return Metadata(experiment, bounds), sample_bounds

    def _is_channel_present(self, chnl: str | int) -> bool:
        """is channel present in the data"""
        return chnl in self.meta.experiment.rx_channels
