import functools
import logging
import re
from pathlib import Path
from typing import List, Optional

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

    The data layout is documented trough the link in `Documentation`, e.g. the 2024 release:
    https://doi.org/10.5281/zenodo.15490005

    Args:
        path: Path to file containing the data.
        exp_def: Experiment definition to be able to decode the data.
        cache:  (Not yet supported) If caching data files should be enabled, will increase RAM usage.

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
    PARBLOCK_CALIBRATION_TEMPERATURE = 20  # post-2000 format
    ENDTIME = "EndTime"
    INTEGRATIONTIME = "IntegrationTime"
    # PortalDBReference section
    PORTALDBREFERENCE = "PortalDBReference"
    DATASTREAM = "DataStream"
    EXPERIMENTNAME = "ExperimentName"

    @property
    def epoch_bounds(self) -> BoundParams:
        """Data epoch bounds in microseconds"""
        return self._epoch_bounds

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.exp_def.rx_channels

    def __init__(
        self,
        path: Path | str,
        exp_def: Optional[ExpDef] = None,
        cache: bool = False,
    ) -> None:

        self._path = Path(path)

        if self.path.is_dir():
            self.files = self._get_all_files_from_dir(self.path)
        else:
            self.files = [self.path]

        if not exp_def:
            exp_def = self.get_experiment(self.files)

        super().__init__(path, exp_def, cache)

        self._dumps, self._dumps_per_file, self._samples_per_dump = self._get_data_size(self.files)
        self._epoch_bounds = self._extract_bounds(self.files)
        self._pointing = self._extract_pointing(self.files)

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
            return (0, self._dumps * self._samples_per_dump)
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
            if isinstance(channel, list):
                if len(channel) > len(self.exp_def.rx_channels):
                    raise Exception(
                        f"More channels requested than available, requested: {channel}, available: {self.exp_def.rx_channels}"
                    )
                if len(channel) == 1:
                    channel = channel[0]

            if not isinstance(channel, str):
                channel = str(channel)

            if channel not in self.channels:
                raise Exception(f"channel {channel} missing in {dir}")

        if start_sample is None:
            start_sample = 0
        if vector_length is None:
            vector_length = self._samples_per_dump

        # Index of data we are interested in
        dump_index = start_sample // self._samples_per_dump
        sample_index = start_sample % self._samples_per_dump

        # Dump index relative to the affected files
        dump_windows = -((sample_index + vector_length) // -self._samples_per_dump)
        file_index = dump_index // self._dumps_per_file
        file_dump_index = dump_index % self._dumps_per_file

        # How many files does data need to be retrived from
        n_files = -(dump_windows // -self._dumps_per_file)
        if n_files == 1 and dump_windows + dump_index > self._dumps_per_file:
            n_files += 1

        if n_files == 1:
            if (
                self.cache_state and self._dumps_per_file < 20
            ):  # Files of this size cannot be cached due to limited RAM.
                all_dumps = self.get_data(self.files[file_index])
                dumps = all_dumps[file_dump_index : file_dump_index + dump_windows]
            else:
                dumps = self.get_data(
                    self.files[file_index],
                    start_dump=file_dump_index,
                    end_dump=file_dump_index + dump_windows,
                )
        else:
            files = self.files[file_index : file_index + n_files]
            dumps = np.empty((0,), dtype=np.complex128)
            if self.cache_state and self._dumps_per_file < 20:
                for i, file in enumerate(files):
                    dump_block = self.get_data(self.files[file_index])
                    if i == 0:
                        dumps = dump_block
                    else:
                        dumps = np.concatenate((dumps, dump_block), axis=-1)
                dumps = dumps[file_dump_index : file_dump_index + dump_windows]
            else:
                for i, file in enumerate(files):
                    if i == 0:
                        dump_block = self.get_data(self.files[file_index], start_dump=file_dump_index)
                    elif i == len(files) - 1:
                        first_block_n_dumps = self._dumps_per_file - file_dump_index
                        dump_block = self.get_data(
                            self.files[file_index],
                            end_dump=dump_windows - (first_block_n_dumps + (i - 1) * self._dumps_per_file),
                        )
                    else:
                        dump_block = self.get_data(self.files[file_index])

                    if i == 0:
                        dumps = dump_block
                    else:
                        dumps = np.concatenate((dumps, dump_block), axis=-1)

        # Concatenate the dump windows
        raw_data = np.concatenate(dumps, axis=1)  # TODO: Quite a bottleneck, find a faster alternative

        # extract samples
        data = np.empty(vector_length, dtype=complex)
        data.real = raw_data[self.REAL_IND, sample_index : sample_index + vector_length].flatten()
        data.imag = raw_data[self.IMAG_IND, sample_index : sample_index + vector_length].flatten()

        return data

    def _get_data(
        self, path: Path, start_dump: Optional[int] = None, end_dump: Optional[int] = None
    ) -> npt.NDArray:
        file = self._open_hdf5_file(path)

        if start_dump is None:
            start_dump = 0
        if end_dump is None:
            end_dump = file[self.DATA][self.DATA_LEVEL].shape[0]

        data = file[self.DATA][self.DATA_LEVEL][start_dump:end_dump]
        file.close()

        return data

    # TODO: change to carthesian coordinates
    def pointing(self, sample: int) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""

        block_id = sample // self._samples_per_dump
        return Pointing(azimuth=self._pointing[block_id, 0], elevation=self._pointing[block_id, 1])

    def _extract_pointing(self, path: Path | list[Path]) -> npt.NDArray:
        """Extract pointing data from the parameter block"""

        if isinstance(path, list):
            data = np.zeros((self._dumps, 2))
            for i, sub_path in enumerate(path):
                file = self._open_hdf5_file(sub_path)
                file_dumps = file[self.DATA][self.PARBLOCK][self.PARBLOCK].shape[0]
                for j in range(file_dumps):
                    data[(i * self._dumps_per_file) + j, 0] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][
                        j
                    ][self.PARBLOCK_AZIMUTH]
                    data[(i * self._dumps_per_file) + j, 1] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][
                        j
                    ][self.PARBLOCK_ELEVATION]
                file.close()
        else:
            file = self._open_hdf5_file(path)
            data = np.zeros((self._dumps, 2))
            for i in range(data.shape[0]):
                data[i, 0] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][self.PARBLOCK_AZIMUTH]
                data[i, 1] = file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][self.PARBLOCK_ELEVATION]
            file.close()
        return data

    def _extract_bounds(self, path: Path | list[Path]) -> BoundParams:
        """
        Extract epoch bounds HDF5 file

        """
        start_file = path[0] if isinstance(path, list) else path
        file = self._open_hdf5_file(start_file)
        start_time_sec = (
            ts_from_str(file[self.DATA][self.ENDTIME][0].decode()) - file[self.DATA][self.INTEGRATIONTIME][0]
        )
        file.close()

        end_file = path[-1] if isinstance(path, list) else path
        file = self._open_hdf5_file(end_file)
        end_time_sec = ts_from_str(file[self.DATA][self.ENDTIME][-1].decode())
        file.close()

        return BoundParams(ts_start_usec=int(start_time_sec * 1e6), ts_end_usec=int(end_time_sec * 1e6))

    def _get_data_size(self, path: Path | list[Path]) -> tuple[int, int, int]:
        """Extract amount of dumps and sample per dump from hdf5 file"""

        if isinstance(path, List):
            dumps = 0
            dumps_per_file = -1
            sample_per_dump = -1
            for sub_path in path:
                file = self._open_hdf5_file(sub_path)
                dumps += file[self.DATA][self.DATA_LEVEL].shape[0]
                if dumps_per_file == -1:
                    dumps_per_file = file[self.DATA][self.DATA_LEVEL].shape[0]
                if sample_per_dump == -1:
                    sample_per_dump = file[self.DATA][self.DATA_LEVEL].shape[2]
                file.close()
        else:
            file = self._open_hdf5_file(path)

            dumps, _, sample_per_dump = file[self.DATA][self.DATA_LEVEL].shape
            dumps_per_file = dumps
            file.close()

        return dumps, dumps_per_file, sample_per_dump

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
        return chnl in self.exp_def.rx_channels

    def _get_all_files_from_dir(self, path: Path) -> list[Path]:
        """Get all files available in dir"""
        paths: list[Path] = []
        if not path.is_dir():
            return paths

        paths = [f for f in path.iterdir() if f.is_file() and self.validate(f)]
        paths.sort()

        if len(paths) == 0:
            raise Exception(f"No valid hdf5 files at: {path}")
        return paths

    def get_experiment(self, files: list[Path]) -> ExpDef:

        if len(files) >= 2:
            file = self._open_hdf5_file(self.files[0])
            name = file[self.PORTALDBREFERENCE][self.EXPERIMENTNAME][()][0].decode()
            shape = file[self.DATA][self.DATA_LEVEL].shape
            frequency = file[self.DATA]["ParBlock"]["ParBlock"][0][self.PARBLOCK_FREQUENCY]
            rx_channel = file[self.PORTALDBREFERENCE][self.DATASTREAM][0].decode()
            file.close()

            file = self._open_hdf5_file(self.files[-2])
            end_name = file[self.PORTALDBREFERENCE][self.EXPERIMENTNAME][()][0].decode()
            end_shape = file[self.DATA][self.DATA_LEVEL].shape
            end_frequency = file[self.DATA]["ParBlock"]["ParBlock"][0][self.PARBLOCK_FREQUENCY]
            end_rx_channel = file[self.PORTALDBREFERENCE][self.DATASTREAM][0].decode()
            file.close()

            if name != end_name:
                raise Exception(
                    "Files in the directory has run on different experiments, analyse the file separately"
                )
            if shape != end_shape:
                raise Exception("Files in this directory are of different shape, not possible to load")

            # TODO: Compare last and first frequency and rx channel?

        else:
            file = self._open_hdf5_file(self.files[0])
            name = file[self.PORTALDBREFERENCE][self.EXPERIMENTNAME][()][0].decode()
            shape = file[self.DATA][self.DATA_LEVEL].shape
            frequency = file[self.DATA]["ParBlock"]["ParBlock"][0][self.PARBLOCK_FREQUENCY]
            rx_channel = file[self.PORTALDBREFERENCE][self.DATASTREAM][0].decode()
            file.close

        expname, expvers, owner = self._expinfo_split(name)
        exp_def = get_experiment(group=expname, version=expvers)

        if exp_def.samples_per_file != int(shape[0] * shape[2]):
            self.__logger.info("Samples per file amount is unknown, will create a new experiment")
            exp_def = exp_def.copy(samples_per_file=int(shape[0] * shape[2]))

        if exp_def.radar_frequency != frequency:
            self.__logger.debug(
                f"Radar frequency in experiment does not match with frequency in measurement file.\
                exp def: {exp_def.radar_frequency} measurement file: {frequency}"
            )
            # TODO: Update experiment with correct frequency

        if exp_def.rx_channels[0] != rx_channel:
            raise ValueError("Rx channel does not match with channel in measurement file")

        return exp_def

    def _setup_cache(self) -> None:
        """Setup cache"""

        if self.cache_state:
            self.get_data = functools.lru_cache(maxsize=2)(self._get_data)
        else:
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
