from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt
import scipy.constants
import logging
import h5py
import re
from radardef.components.data_loader_template import DataLoader
from radardef.radar_stations.eiscat.utils import load_radar_code, load_expconfig
from radardef.radar_stations.eiscat.utils.drf_utils import ts_from_str
from radardef.radar_stations.eiscat.validators import HDF5
from radardef.types import (
    BoundParams,
    ExpParams,
    Metadata,
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
    def meta(self) -> Metadata:
        """Metadata, containing experiment data and bounds data"""
        return self.__meta

    # TODO: change to carthesian coordinates
    @property
    def pointing(self) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        return self.__pointing

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.meta.experiment.rx_channels

    def __init__(self) -> None:
        super().__init__(TargetFormat.HDF5, HDF5())
        self.__meta = Metadata(ExpParams(), BoundParams())

    def load(self, path: Path | str) -> None:
        """
        Loads a path to the dataloader, extracting metadata and other important specifications

        Args:
            path: path to data file
        """

        self.__path = Path(path).resolve()
        self.__dumps, self.__samples_per_dump = self._get_data_size(self.__path)
        self.__meta = self._extract_meta(self.__path)
        self.__pointing = self._extract_pointing(self.__path)

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
        channel: str | int,
        start_sample: Optional[int] = None,
        vector_length: Optional[int] = None,
    ) -> npt.NDArray[np.complex128]:
        """

        HDF5 data format:
        ```
            [dump, [real, imag], samples]
        ```

        Args:
            channel: channel to read data from
            start_sample (optional): sample to start reading from, if not given bounds start will be used.
            vector_length (optional): Amount of samples to read from start_sample,
                                      if not given one batch will be read.

        Returns:
            Complex data of given channel
        """
        if not isinstance(channel, str):
            channel = str(channel)

        if channel not in self.channels:
            raise Exception(f"channel {channel} missing in {dir}")

        if start_sample is None:
            start_sample = 0
        if vector_length is None:
            vector_length = self.__samples_per_dump

        dump_index = start_sample // self.__samples_per_dump
        windows = -(vector_length // -self.__samples_per_dump)
        sample_index = start_sample % self.__samples_per_dump

        file = self._open_hdf5_file(self.__path)

        raw_data = file[self.DATA][self.DATA_LEVEL][
            dump_index : dump_index + windows,
            self.REAL_IND : self.IMAG_IND + 1,
            sample_index : sample_index + vector_length,
        ]

        file.close()

        data = np.empty(vector_length, dtype=complex)
        data.real = raw_data[:, self.REAL_IND]
        data.imag = raw_data[:, self.IMAG_IND]

        return data

    def _extract_pointing(self, path: Path) -> Pointing:
        """Extract pointing data from the parameter block"""

        file = self._open_hdf5_file(path)
        data = []
        for i in range(file[self.DATA][self.PARBLOCK][self.PARBLOCK].shape[0]):

            data.append(
                (
                    i * self.__samples_per_dump,
                    {
                        "azimuth": file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][self.PARBLOCK_AZIMUTH],
                        "elevation": file[self.DATA][self.PARBLOCK][self.PARBLOCK][i][
                            self.PARBLOCK_ELEVATION
                        ],
                    },
                )
            )
        file.close()
        return Pointing(data=data, sample_rate=1)

    def _extract_meta(self, path: Path) -> Metadata:
        """
        Extract meta data from HDF5 file and experiment config files

        """
        file = self._open_hdf5_file(path)
        name = file[self.PORTALDBREFERENCE][self.EXPERIMENTNAME][()][0].decode()

        expname, expvers, owner = self._expinfo_split(name)
        cfg = load_expconfig(expname)
        cfv = cfg[expvers]

        items = [
            "sample_rate",
            "ipp",
            "tx_pulse_length",
            "rx_start",
            "rx_end",
            "tx_start",
            "tx_end",
            "cal_on",
            "cal_off",
        ]

        exp_params = {}
        for item in items:
            data = cfv.get(item)
            exp_params[item] = float(data) if data is not None else 0

        t_samp_usec = int((1 / exp_params["sample_rate"]) * 1e6)
        radar_frequency = file[self.DATA]["ParBlock"]["ParBlock"][0][self.PARBLOCK_FREQUENCY]
        ipp_samps = exp_params["ipp"] / t_samp_usec
        channel = file[self.PORTALDBREFERENCE][self.DATASTREAM][0].decode()

        experiment = ExpParams(
            name=name,
            radar_frequency=radar_frequency,
            t_ipp_usec=exp_params["ipp"],
            sample_rate=exp_params["sample_rate"],
            ipp_samps=int(ipp_samps),
            t_samp_usec=t_samp_usec,
            rx_channels=[channel],
            tx_channel=channel,
            tx_pulse_length=int(exp_params["tx_pulse_length"]) + 1,
            t_rx_start_usec=exp_params["rx_start"],
            t_rx_end_usec=exp_params["rx_end"],
            t_tx_start_usec=exp_params["tx_start"],
            t_tx_end_usec=exp_params["tx_end"] + t_samp_usec,
            t_cal_on_usec=exp_params["cal_on"],
            t_cal_off_usec=exp_params["cal_off"],
            wavelength=scipy.constants.c / radar_frequency * 1e6,
            # code=load_radar_code(expname), #TODO: Fix code for leo_mpark
        )

        start_time_sec = (
            ts_from_str(file[self.DATA][self.ENDTIME][0].decode()) - file[self.DATA][self.INTEGRATIONTIME][0]
        )
        end_time_sec = ts_from_str(file[self.DATA][self.ENDTIME][-1].decode())
        bounds = BoundParams(ts_start_usec=int(start_time_sec * 1e6), ts_end_usec=int(end_time_sec * 1e6))
        file.close()
        return Metadata(experiment=experiment, bounds=bounds)

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
        return chnl in self.meta.experiment.rx_channels
