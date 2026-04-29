import logging
import re
from pathlib import Path
from typing import Optional

import h5py
import numpy as np
import numpy.typing as npt

from radardef.components import DataLoader
from radardef.radar_stations.eiscat.experiments import get_experiment
from radardef.radar_stations.eiscat.utils.drf_utils import ts_from_str
from radardef.radar_stations.eiscat.validators import HDF5
from radardef.types import (
    BoundParams,
    ExpDef,
    Pointing,
    TargetFormat,
)


class HDF5Loader(DataLoader):
    """
    HDF5 layout:
    ```
        DATA <Actual data>
          ├─EndTime
          ├─IntegrationTime
          ├─L1
          ├─L2
          └─ParBlock
                └─ParBlock
        MetaData <Data specs>
          ├─EndTime
          ├─IntegrationTime
          ├─L1
          ├─L2
          └─ParBlock
                └─ParBlockLayout
        PortalDBR <Portal specs>
          ├─AccumulatedSeconds
          ├─DataStream
          ├─Documentation
          ├─ExperimentName
          ├─InfoId
          ├─RequestID
          └─ResourceID
    ```

    """

    __logger = logging.getLogger(__name__)

    converted_format = TargetFormat.HDF5
    validator = HDF5()

    # Data section
    DATA = "Data"
    DATA_LEVEL = "L1"
    REAL_IND = 0
    IMAG_IND = 1
    PARBLOCK = "ParBlock"
    PARBLOCK_ELEVATION = 8
    PARBLOCK_AZIMUTH = 9
    PARBLOCK_FREQUENCY = 54  # Not stated in docs
    ENDTIME = "EndTime"
    INTEGRATIONTIME = "IntegrationTime"
    # PortalDBReference section
    PORTALDBREFERENCE = "PortalDBReference"
    DATASTREAM = "DataStream"
    EXPERIMENTNAME = "ExperimentName"

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
        super().__init__(path, exp_def)
        if not self._experiment:
            file = self._open_hdf5_file(self.path)
            name = file[self.PORTALDBREFERENCE][self.EXPERIMENTNAME][()][0].decode()
            file.close

            expname, expvers, owner = self._expinfo_split(name)
            self._experiment = get_experiment(group=expname, version=expvers)

        self.__dumps, self.__samples_per_dump = self._get_data_size(self.path)
        self.__epoch_bounds = self._extract_bounds(self.path)
        self.__pointing = self._extract_pointing(self.path)

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

        if self._is_channel_present(channel):
            return (0, self.__dumps * self.__samples_per_dump)
        else:
            raise Exception(f"channel {channel} is missing in {dir}")

    def read(
        self,
        channel: Optional[str | int | list[str] | list[int]] = None,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """

        HDF5 data format:
        ```
            [dump, [real, imag], samples]
        ```

        Args:
            channel (optional): Channel to read data from, single channel or list of channels. If not specified all channels will be returned.
            start_sample (optional): sample to start reading from, if not given bounds start will be used.
            vector_length (optional): Amount of samples to read from start_sample,
                                      if not given one batch will be read.

        Returns:
            Complex data from channel shape: (vector_length,)
        """
        if channel:
            if not isinstance(channel, str):
                channel = str(channel)

            if channel not in self.channels:
                raise Exception(f"channel {channel} missing in {dir}")

        if start_sample is None:
            start_sample = 0
        if vector_length is None:
            vector_length = self.__samples_per_dump

        dump_index = start_sample // self.__samples_per_dump
        sample_index = start_sample % self.__samples_per_dump
        windows = -((sample_index + vector_length) // -self.__samples_per_dump)

        file = self._open_hdf5_file(self.path)

        # Concatenate the dump windows
        raw_data = file[self.DATA][self.DATA_LEVEL][dump_index : dump_index + windows].reshape(2, -1)

        file.close()

        # extract samples
        data = np.empty(vector_length, dtype=complex)
        data.real = raw_data[self.REAL_IND, sample_index : sample_index + vector_length].flatten()
        data.imag = raw_data[self.IMAG_IND, sample_index : sample_index + vector_length].flatten()

        return data

    # TODO: change to carthesian coordinates

    def pointing(self, sample: int) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""

        block_id = sample // self.__samples_per_dump
        return Pointing(azimuth=self.__pointing[block_id, 0], elevation=self.__pointing[block_id, 1])

    def _extract_pointing(self, path: Path) -> npt.NDArray:
        """Extract pointing data from the parameter block"""

        file = self._open_hdf5_file(path)
        data = np.zeros((file[self.DATA][self.PARBLOCK][self.PARBLOCK].shape[0], 2))
        for i in range(data.shape[0]):
            data[i, 0] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][self.PARBLOCK_AZIMUTH]
            data[i, 1] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][self.PARBLOCK_ELEVATION]
        file.close()
        return data

    def _extract_bounds(self, path: Path) -> BoundParams:
        """
        Extract meta data from HDF5 file and experiment config files

        """
        file = self._open_hdf5_file(path)

        if (
            self.experiment.radar_frequency
            != file[self.DATA]["ParBlock"]["ParBlock"][0][self.PARBLOCK_FREQUENCY]
        ):
            self.__logger.debug(
                f"Radar frequency in experiment does not match with frequency in measurement file.\
                exp def: {self.experiment.radar_frequency} \
                measurement file: {file[self.DATA]['ParBlock']['ParBlock'][0][self.PARBLOCK_FREQUENCY]}"
            )
        if self.experiment.rx_channels[0] != file[self.PORTALDBREFERENCE][self.DATASTREAM][0].decode():
            raise ValueError("Rx channel does not match with channel in measurement file")

        start_time_sec = (
            ts_from_str(file[self.DATA][self.ENDTIME][0].decode()) - file[self.DATA][self.INTEGRATIONTIME][0]
        )
        end_time_sec = ts_from_str(file[self.DATA][self.ENDTIME][-1].decode())
        bounds = BoundParams(ts_start_usec=int(start_time_sec * 1e6), ts_end_usec=int(end_time_sec * 1e6))
        file.close()
        return bounds

    def _get_data_size(self, path: Path) -> tuple[int, int]:
        """Extract amount of dumps and sample per dump from hdf5 file"""
        file = self._open_hdf5_file(path)

        dumps, _, sample_per_dump = file[self.DATA][self.DATA_LEVEL].shape

        return dumps, sample_per_dump

    def _open_hdf5_file(self, path: Path) -> h5py.File:
        """Open hdf5 file and return reader"""

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

    def _expinfo_split(self, xpinf: str) -> tuple[str, ...]:
        """
        Move from hard coded constants to loading config based on exp name/version
        'leo_bpark_2.1u_NO' -> (leo_bpark', '2.1u', 'NO')
        """
        try:
            match = re.match(r"(\w+)_(\d+(?:\.\d+)?[a-z]*)_(\w+)", xpinf)
            if match is not None:
                return match.groups()
            else:
                return "", "", ""
        except Exception as e:
            raise ValueError(f"d_ExpInfo: {xpinf} not understood: {e}")

    def _get_channel_from_file_name(self, file_name: str) -> str:
        """Extract channel from file name
        'leo_mpark_2.1u_EI@uhf_2024' -> 'uhf'
        """
        match = re.findall(r"(?<=@)[^_]+(?=_)", file_name)
        return match[0]

    def _is_channel_present(self, chnl: str | int) -> bool:
        """is channel present in the data"""
        return chnl in self.experiment.rx_channels
