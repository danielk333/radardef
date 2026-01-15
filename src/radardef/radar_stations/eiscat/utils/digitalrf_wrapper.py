"""
This module provides a wrapper around reader and writer objects
from 'digital_rf' - to provide a uniform API and correct some design issues.

NOTE - not sure if digital_rf is thread-safe with respect to concurrent
writes to same file (e.g. adjacent blocks).
Also, it appears that digital_rf is not random access with respect to
writing (even in non-continuous mode) as it maintains and internal index
for next available sample.
"""

from pathlib import Path
from typing import Any, Iterable, Optional

import digital_rf
import numpy as np

from radardef.radar_stations.eiscat.utils.drf_utils import index_from_ts, ts_from_index


class BaseIndexedTimeSequence:
    """

    Time sequence to index and index to time sequence converter

    Args:
        sample_rate: Sample rate for the time sequence
        ts_align_sec (optional): Timestamp associated with a specific index (timestamp in seconds since epoch),
                typically it could be the timestamp of the first sample, default is 0.
                ts_align_sec defines the precise alignment between timestamps and index-domain.
        ts_offset_sec (optional): Timestamp in seconds since epoch,
                                  defines a time offset for the index space, default is 0.
    """

    def __init__(self, sample_rate: float, ts_align_sec: int = 0, ts_offset_sec: int = 0) -> None:

        self.sample_rate = sample_rate
        self.__ts_offset_sec = ts_offset_sec

        self.__ts_align_sec = ts_align_sec
        self.__ts_skew = 0
        __idx_align = index_from_ts(ts_align_sec, self.sample_rate)
        self.__ts_skew = __idx_align - np.floor(__idx_align)

    def ts_from_index(self, idx: int) -> float:
        """convert index to timestamp (seconds since epoch)"""
        ts = ts_from_index(idx, self.sample_rate, ts_offset_sec=self.__ts_offset_sec)
        return ts + self.__ts_skew

    def index_from_ts(self, ts: float) -> int:
        """Convert timestamp(seconds since epoch) to index"""
        ts = ts - self.__ts_skew
        return index_from_ts(ts, self.sample_rate, ts_offset_sec=self.__ts_offset_sec)


class DigitalRFWriter(BaseIndexedTimeSequence):
    """
    Convenience wrapper around digital_rf.DigitalRFWriter

    Args:
        dst: Destination directory.
        chnl: Radar channel.
        sample_rate_numerator: Numerator of sample rate in Hz.
        sample_rate_denominator: Denominator of sample rate in Hz.
        dtype_str: dtype of the data.
        start_global_index: The index of the first sample given in number of samples since the
            epoch.
        subdir_cadence_secs (optional): Number of seconds of data to store in one subdirectory,
            default is 3600 seconds.
        file_cadence_secs (optional): Number of seconds of data to store in each file,
            default is 3600 seconds.
        compression_level (optional): 0 for no compression (default), 1-9 for varying levels of gzip
            compression (1 == least compression, least CPU; 9 == most
            compression, most CPU).
        is_complex (optional): Used when dtype is not complex, if true the data is interpreted as complex.
        checksum (optional): If HDF5 cheksum capability should be used.
        num_subchannels (optional): Number of subchannels to write to simultaniously, default is 1.
        is_continuous (optional): If true data will be written in continuous blocks.
        marching_periods (optional): Write a period to stdout for every file when writing.
        uuid_str (optional): UUID string that will act as a unique identifier for the data. If None, a random
            UUID will be generated.
        ts_align_sec (optional): align sec

    """

    def __init__(
        self,
        dst: str | Path,
        chnl: str,
        sample_rate_numerator: float,
        sample_rate_denominator: float,
        dtype_str: Any,
        start_global_index: int,
        subdir_cadence_secs: int = 3600,  # 1 dir per hour
        file_cadence_secs: int = 3600,  # 1 hour per file
        compression_level: int = 0,
        is_complex: bool = False,
        checksum: bool = False,
        num_subchannels: int = 1,
        is_continuous: bool = True,
        marching_periods: bool = False,
        uuid_str: Optional[str] = None,
        ts_align_sec: int = 0,
    ) -> None:

        # check dst
        dst = Path(dst)
        if not dst.is_dir():
            raise Exception(f"<dst> must be directory path, {dst}")

        # channel directory
        chnldir = dst / chnl
        chnldir.mkdir(parents=True, exist_ok=True)

        # sample rate
        sample_rate = sample_rate_numerator / float(sample_rate_denominator)

        super().__init__(sample_rate, ts_align_sec=ts_align_sec)

        # meta data writer
        self._writer = digital_rf.DigitalRFWriter(
            str(chnldir),
            dtype_str,
            subdir_cadence_secs,
            file_cadence_secs * 1000,  # file_cadence_milliseconds
            start_global_index,  # start global index
            sample_rate_numerator,
            sample_rate_denominator,
            uuid_str=uuid_str,
            compression_level=compression_level,
            checksum=checksum,
            is_complex=is_complex,
            num_subchannels=num_subchannels,
            is_continuous=is_continuous,
            marching_periods=marching_periods,
        )

    def close(self) -> None:
        """Close writer"""
        self._writer.close()

    def write(self, batch: Any) -> None:
        """Write batch"""
        self._writer.rf_write(batch)


class DigitalMetadataWriter(BaseIndexedTimeSequence):
    """
    Convenience wrapper around digital_rf.DigitalMetadataWriter

    Args:
        dst: Destination directory.
        chnl: Radar channel.
        sample_rate_numerator: Numerator of sample rate in Hz.
        sample_rate_denominator: Denominator of sample rate in Hz.
        subdir_cadence_secs (optional): Number of seconds of data to store in one subdirectory,
            default is 3600 seconds.
        file_candence_secs (optional): Number of seconds of data to store in each file,
            default is 3600 seconds.
        prefix: prefix of folder
        ts_align_sec: align sec
    """

    def __init__(
        self,
        dst: str | Path,
        chnl: str,
        sample_rate_numerator: float,
        sample_rate_denominator: float,
        subdir_cadence_secs: int = 3600,  # 1 dir per hour
        file_candence_secs: int = 3600,  # 1 hour per file
        prefix: str = "meta",
        ts_align_sec: int = 0,
    ) -> None:

        # check dst
        path = Path(dst)
        if not path.is_dir():
            raise Exception(f"<dst> must be directory path, {path}")

        # metadir
        metadir = path / chnl
        metadir.mkdir(parents=True, exist_ok=True)

        # sample rate
        sample_rate = sample_rate_numerator / float(sample_rate_denominator)

        super().__init__(sample_rate, ts_align_sec=ts_align_sec)

        # meta data writer
        self._writer = digital_rf.DigitalMetadataWriter(
            str(metadir),
            subdir_cadence_secs,
            file_candence_secs,
            sample_rate_numerator,
            sample_rate_denominator,
            prefix,
        )

    def write(self, idx: int, data: dict[str, Any]) -> None:
        """Write data at sample"""
        self._writer.write(idx, data)

    def close(self) -> None:
        """Close writer"""
        pass
