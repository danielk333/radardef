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
import scipy.constants

from radardef.components.data_loader_template import DataLoader
from radardef.radar_stations.eiscat.utils import load_radar_code
from radardef.radar_stations.eiscat.validators import DRF
from radardef.types import (
    Boundparam,
    BoundParams,
    Expparam,
    ExpParams,
    Metadata,
    Metaparam,
    Pointing,
    TargetFormat,
)


class DrfLoader(DataLoader):
    """Simplifies the way to load DRF files converted from eiscat"""

    @property
    def meta(self) -> Metadata:
        """Metadata, containing experiment data and bounds data"""

        # metadata file
        meta_file = configparser.ConfigParser()
        meta_file.read(self.__path / "metadata.ini")
        sample_rate = meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.SAMPLE_RATE)
        t_samp_usec = int((1 / sample_rate) * 1e6)
        t_ipp_usec = meta_file.getint(Metaparam.EXPERIMENT, Expparam.T_IPP_USEC)
        ipp_samps = int(t_ipp_usec * 1e-6 * sample_rate)
        code = load_radar_code("leo_bpark")  # TODO: Base this on some experiment param in the future

        experiment = ExpParams(
            name=meta_file.get(Metaparam.EXPERIMENT, Expparam.NAME).strip("'").strip('"'),
            radar_frequency=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.RADAR_FREQUENCY),
            t_ipp_usec=t_ipp_usec,
            sample_rate=sample_rate,
            ipp_samps=ipp_samps,
            t_samp_usec=t_samp_usec,
            rx_channels=eval(meta_file.get(Metaparam.EXPERIMENT, Expparam.RX_CHANNELS).strip("'").strip('"')),
            tx_channel=meta_file.get(Metaparam.EXPERIMENT, Expparam.TX_CHANNEL).strip("'").strip('"'),
            tx_pulse_length=int((meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.TX_PULSE_LENGTH) + 1)),
            t_rx_start_usec=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_RX_START_USEC),
            t_rx_end_usec=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_RX_END_USEC),
            t_tx_start_usec=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_TX_START_USEC),
            t_tx_end_usec=(meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_TX_END_USEC) + t_samp_usec),
            t_cal_on_usec=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_CAL_ON_USEC),
            t_cal_off_usec=meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.T_CAL_OFF_USEC),
            wavelength=scipy.constants.c
            / (meta_file.getfloat(Metaparam.EXPERIMENT, Expparam.RADAR_FREQUENCY) * 1e6),
            code=code,
        )

        bounds = BoundParams(
            ts_start_usec=meta_file.getfloat(Metaparam.BOUNDS, Boundparam.TS_START_USEC),
            ts_end_usec=meta_file.getfloat(Metaparam.BOUNDS, Boundparam.TS_END_USEC),
        )

        return Metadata(experiment, bounds)

    @property
    def pointing(self) -> Pointing:
        """Pointing data, data describing the radar pointing direction in spherical coordinates"""
        if self.__meta_reader is None:
            return Pointing(data=[(0, {"azimuth": 0, "elevation": 0})], sample_rate=0)
        else:
            idx_start, idx_end = self.__meta_reader.get_bounds()
            # load pointing data as vector
            return Pointing(
                data=list(self.__meta_reader.read(idx_start, idx_end).items()),
                sample_rate=float(self.__meta_reader.get_samples_per_second()),
            )

    @property
    def channels(self) -> list[int] | list[str]:
        """All available channels"""
        return self.__channel_reader.get_channels()

    def __init__(self) -> None:
        super().__init__(TargetFormat.DRF, DRF())

    def load(self, path: Path | str) -> None:
        """Loads a path to the dataloader, extracting metadata and other important specifications

        Args:
            path: path to data file

        Raises:
            Exception: path is not a directory
            Exception: pointing dir must be a directory
        """

        self.__path = Path(path).resolve()

        if not self.__path.is_dir():
            raise Exception(f"<dir> must be directory path, {self.__path}")

        self.__channel_reader = digital_rf.DigitalRFReader(str(self.__path))

        pointing_dir = self.__path / "pointing"
        if not pointing_dir.is_dir():
            raise Exception(f"<dir/pointing> must be directory path, {self.__path}")

        self.__meta_reader = digital_rf.DigitalMetadataReader(str(pointing_dir))

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
        """

        if not isinstance(channel, str):
            channel = str(channel)

        if channel not in self.__channel_reader.get_channels():
            raise Exception(f"channel {channel} missing in {dir}")

        if start_sample is None or vector_length is None:
            bound_start, bound_end = self.bounds(channel)
            return self.__channel_reader.read_vector_1d(bound_start, bound_end - 1, channel)
        else:
            return self.__channel_reader.read_vector_1d(start_sample, vector_length, channel)
