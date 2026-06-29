"""
This module contains functionality to load MUI -> h5 converted files in a standardized way. The data loader
is based on the Dataloader template
"""

import datetime as dt
import functools
import logging
import math
from pathlib import Path
from typing import Optional

import h5py
import numpy as np
import numpy.typing as npt

from radardef.components import DataLoader
from radardef.radar_stations.mu.experiments import mu_exp, mu_exp_large
from radardef.radar_stations.mu.validators import H5
from radardef.types import BoundParams, ExpDef, Pointing, TargetFormat


class H5Loader(DataLoader):
    """
    Simplifies the way to load .h5 files converted from MUI

    Args:
        path: Path to file containing the data.
        exp_def: Experiment definition to be able to decode the data.
        cache:  If caching data files should be enabled, will increase RAM usage.
    """

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
        return self.exp_def.rx_channels

    def __init__(
        self,
        path: Path | str,
        exp_def: Optional[ExpDef] = None,
        cache: bool = True,
    ) -> None:

        self._path = Path(path)

        if self.path.is_dir():
            self.files = self._get_all_files_from_dir(self.path)
        else:
            self.files = [self.path]

        if not exp_def:
            exp_def = self.get_experiment(self.files)

        super().__init__(self.path, exp_def, cache)

        if self.path.is_dir():
            self.__epoch_bounds, self.__sample_bounds = self._extract_bounds_from_list(self.files)
        else:
            self.__epoch_bounds, self.__sample_bounds = self._extract_bounds(self.path)

        if len(self.__sample_bounds) != len(self.exp_def.rx_channels):
            raise AttributeError(
                f"Amount of channels in experiment definition: {len(self.exp_def.rx_channels)} \
                is not the same as the amount of channels in the data file: {len(self.__sample_bounds)}"
            )

    def get_experiment(self, files: list[Path]) -> ExpDef:
        if len(files) >= 2:
            n_ipps_start = h5py.File(files[0], "r")["data"].shape[1]
            # Choosing second last since the last file is ok to be shorter than the rest
            n_ipps_end = h5py.File(files[-2], "r")["data"].shape[1]

            if n_ipps_start != n_ipps_end:
                raise Exception("Files in this directory are of different shape, not possible to load")

            elif n_ipps_start == (12 * 512):
                return mu_exp
            elif n_ipps_start == (14 * 512):
                return mu_exp_large
            else:
                self.__logger.info("Samples per file amount is unknown, will create a new experiment")
                return mu_exp.copy(samples_per_file=int(n_ipps_start * mu_exp.ipp_samps))
        else:
            n_ipps = h5py.File(files[0], "r")["data"].shape[1]
            if n_ipps == (12 * 512):
                return mu_exp
            elif n_ipps == (14 * 512):
                return mu_exp_large
            elif n_ipps < (12 * 512):
                # A small file works with any exp defintion
                return mu_exp
            else:
                self.__logger.info("Samples per file amount is unknown, will create a new experiment")
                return mu_exp.copy(samples_per_file=int(n_ipps * mu_exp.ipp_samps))

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
        channel: Optional[str | int | list[int] | list[str]] = None,
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
            Complex data from channel/channels. Shape for single channel: (vector_length,) otherwise: (channels, vector_length)

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

        if self.path.is_dir():
            if start_sample is not None:
                start_file = math.floor(start_sample / self.exp_def.samples_per_file)
                index = start_sample % self.exp_def.samples_per_file
            else:
                start_file = 0
                index = 0
                start_sample = 0

            if vector_length is not None:
                num_files = math.ceil(
                    ((start_sample % self.exp_def.samples_per_file) + vector_length)
                    / self.exp_def.samples_per_file
                )
                samples = vector_length
            else:
                num_files = len(self.files)
                samples = self.bounds(self.exp_def.rx_channels[0])[1]

            files = self.files[start_file : start_file + num_files]
            data = np.empty((0,), dtype=np.complex128)
            if len(files) > 1 or self.cache_state:
                for i, file in enumerate(files):
                    data_block = self.get_data(
                        file, channel if not isinstance(channel, list) else tuple(channel)
                    )

                    if i == 0:
                        data = data_block
                    else:
                        data = np.concatenate((data, data_block), axis=-1)

                if data.ndim >= 2:
                    return data[:, index : index + samples]
                else:
                    return data[index : index + samples]
            else:
                start_ipp = index // self.exp_def.ipp_samps
                end_ipp = (index + samples) // self.exp_def.ipp_samps + 1
                data = self.get_data(
                    files[0], channel if not isinstance(channel, list) else tuple(channel), start_ipp, end_ipp
                )

                index = index % self.exp_def.ipp_samps

                if data.ndim >= 2:
                    return data[:, index : index + samples]
                else:
                    return data[index : index + samples]
        else:
            if self.cache_state:
                data_block = self.get_data(
                    self.path, channel if not isinstance(channel, list) else tuple(channel)
                )

                if start_sample is None and vector_length is None:
                    return data_block
                elif start_sample is not None and vector_length is not None:
                    if data_block.ndim > 1:
                        return data_block[:, start_sample : start_sample + vector_length]
                    else:
                        return data_block[start_sample : start_sample + vector_length]
                elif start_sample is None and vector_length is not None:
                    if data_block.ndim > 1:
                        return data_block[:, 0:vector_length]
                    else:
                        return data_block[0:vector_length]
                else:
                    if data_block.ndim > 1:
                        return data_block[:, start_sample:]
                    else:
                        return data_block[start_sample:]
            else:
                if start_sample is None:
                    start_sample = 0
                if vector_length is None:
                    vector_length = self.bounds(self.exp_def.rx_channels[0])[1]
                start_ipp = start_sample // self.exp_def.ipp_samps
                end_ipp = (start_sample + vector_length) // self.exp_def.ipp_samps + 1
                data_block = self.get_data(
                    self.path,
                    channel if not isinstance(channel, list) else tuple(channel),
                    start_ipp,
                    end_ipp,
                )

                index = start_sample % self.exp_def.ipp_samps
                return data_block[index : index + vector_length]

    def _get_data(
        self,
        path: Path,
        channel: Optional[str | int | tuple[int] | tuple[str]] = None,
        start_ipp: Optional[int] = None,
        end_ipp: Optional[int] = None,
    ) -> npt.NDArray:

        chnl: int | npt.NDArray | None
        if channel:
            if isinstance(channel, str):
                chnl = int(channel)
            if isinstance(channel, tuple):
                chnl = np.array(channel).astype(np.int64)
            else:
                chnl = int(channel)
            if not self._is_channel_present(chnl):
                raise Exception(f"Atleast one of the requested channels {chnl} is missing in {dir}")
        else:
            chnl = None

        with h5py.File(str(path), "r") as h5file:
            if start_ipp is None:
                start_ipp = 0
            if end_ipp is None:
                end_ipp = h5file["data"].shape[1]

            if chnl is not None:
                data = h5file["data"][chnl - 1, start_ipp:end_ipp]
            else:
                data = h5file["data"][:, start_ipp:end_ipp]

        return self._flatten_and_zero_pad(data)

    def pointing(self, sample: int) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        return Pointing(azimuth=0.0, elevation=90.0)

    def _flatten_and_zero_pad(self, data: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
        """
        Zero pads the data to make it match the true signal
        ```
        | 81 zeros | 85 samples rx data | 354 zeros |
        ```
        Args:
            data: data of shape (channels, pulses, rx_samples) or (pulses,rx_samples)

        """
        pulses = data.shape[-2]
        rx_samples = data.shape[-1]
        rx_start_samp = int(self.exp_def.t_rx_start_usec / self.exp_def.t_samp_usec)

        if data.ndim <= 2:
            padded_data = np.zeros((pulses, self.exp_def.ipp_samps), dtype=np.complex128)

            padded_data[:, rx_start_samp : rx_start_samp + rx_samples] = data

            return padded_data.reshape(-1)
        else:
            channels = data.shape[0]
            padded_data = np.zeros((channels, pulses, self.exp_def.ipp_samps), dtype=np.complex128)
            padded_data[:, :, rx_start_samp : rx_start_samp + rx_samples] = data

            return padded_data.reshape(channels, pulses * self.exp_def.ipp_samps)

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

        with h5py.File(str(path), "r") as h5file:
            start_time = dt.datetime.strptime(
                str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
            ).replace(tzinfo=dt.timezone.utc)
            end_time = dt.datetime.strptime(
                str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
            ).replace(tzinfo=dt.timezone.utc)

            # time can be validated by end_time = start_time.timestamp() + (n_ipp * t_ipp_usec) * 1e-6, n_ipp = 512
            # if this is not matching maybe the measurement stopped  early
            epoch_bounds = BoundParams(
                ts_start_usec=int(start_time.timestamp() * 1e6),
                ts_end_usec=int(end_time.timestamp() * 1e6),
            )

            sample_bounds: dict[str | int, tuple[int, int]] = {}
            for j, data in enumerate(h5file["data"]):
                channel = j + 1

                if channel in self.exp_def.rx_channels:
                    pulses = len(data)
                    ipp_length = int(self.exp_def.t_ipp_usec / self.exp_def.t_samp_usec)
                    sample_bounds[channel] = (0, pulses * ipp_length)
                else:
                    self.__logger.debug(
                        f"Channel: {j} is present in measurement file but not in experiment definition"
                    )

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
            with h5py.File(str(f), "r") as h5file:
                # Extract meta data, should be general for all files
                if i == 0:
                    start_time = dt.datetime.strptime(
                        str(h5file.attrs["record_start_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                    ).replace(tzinfo=dt.timezone.utc)
                # Store end point of the directory
                if i == (len(paths) - 1):
                    end_time = dt.datetime.strptime(
                        str(h5file.attrs["record_end_time"])[0:26], "%Y-%m-%dT%H:%M:%S.%f"
                    ).replace(tzinfo=dt.timezone.utc)

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
                ipp_length = int(self.exp_def.t_ipp_usec / self.exp_def.t_samp_usec)
                for j, data in enumerate(h5file["data"]):
                    channel = j + 1
                    if channel in self.exp_def.rx_channels:
                        min_max = (0, len(data) * ipp_length)
                        if channel not in sample_bounds:
                            sample_bounds[channel] = min_max
                        else:
                            sample_bounds[channel] = tuple(np.add(sample_bounds[channel], min_max))
                    else:
                        self.__logger.debug(
                            f"Channel: {j} is present in measurement file but not in experiment definition"
                        )

        epoch_bounds = BoundParams(
            ts_start_usec=int(start_time.timestamp() * 1e6),
            ts_end_usec=int(end_time.timestamp() * 1e6),
        )

        return epoch_bounds, sample_bounds

    def _is_channel_present(self, chnl: str | int | list[str] | list[int] | npt.NDArray[np.int64]) -> bool:
        """is channel present in the data"""

        if isinstance(chnl, list) or isinstance(chnl, np.ndarray):
            return set(chnl).issubset(self.exp_def.rx_channels)
        else:
            return chnl in self.exp_def.rx_channels

    def _setup_cache(self) -> None:
        """Setup cache"""

        if self.cache_state:
            self.get_data = functools.lru_cache(maxsize=2)(self._get_data)
        else:
            if hasattr(self.get_data, "cache_clear"):
                self.get_data.cache_clear()
            self.get_data = self._get_data  # type: ignore[assignment]

    def __getstate__(self) -> dict:
        """
        Prepare object for e.g pickling by removing the decorated functions (not supported by pickle)
        """
        state = self.__dict__.copy()
        if "get_data" in state:
            del state["get_data"]
        return state

    def __setstate__(self, state: dict) -> None:
        """Restore object after unpickling"""
        self.__dict__.update(state)
        self._setup_cache()
