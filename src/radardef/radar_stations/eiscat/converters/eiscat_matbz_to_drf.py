"""
Class and freestanding functions to convert Eiscat mat.bz2 data to DRF format, the converter is based on
the Converter template
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
import scipy.constants
from tqdm import tqdm

import radardef.radar_stations.eiscat.utils.digitalrf_wrapper as drf_wrapper
from radardef.components.converter_template import Converter
from radardef.radar_stations.eiscat.utils.eiscat_utils import (
    eiscat_files,
    eiscat_load_file,
    eiscat_process,
)
from radardef.types import Boundparam, Expparam, Metaparam, SourceFormat, TargetFormat


class EiscatMatbzToDrf(Converter):
    """Converts from Eiscat mat.bz2 format to DRF format"""

    __logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.__compression = 0
        super().__init__(SourceFormat.EISCAT_MATBZ, TargetFormat.DRF)

    def set_compression(self, level: int) -> None:
        """Set compression of the DRF conversion"""
        self.__compression = level

    def convert(self, src: Path, dst: Path) -> list[Path]:
        """Convert file from mat.bz2 to DRF"""
        return [
            convert_eiscat_to_drf(
                src, dst, compression=self.__compression, progress=False, logger=self.__logger
            )
        ]


def convert_eiscat_to_drf(
    src: Path,
    dst: Path,
    name: Optional[str] = None,
    compression: int = 0,
    progress: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Path:
    """
    Converts Eiscat raw data to Hardtarget DRF.

    The output (Hardtarget DRF) folder will be placed within the 'dst'
    directory. By default, the name of the Hardtarget DRF folder is constructed
    from the name of the 'src' directory. The name of the Hardtarget DRF folder
    may be specified using the 'name' option. If 'name' is None, name is derived
    from 'src' (leo_bpark_2.1u_NO@uhf -> leo_bpark_2.1u_NO@uhf_drf).

    Args:

        src : Path to source directory (Eiscat raw data)
        dst : Path to destination directory
        name (optional): Name of output directory
        compression (optional): Compression level for h5 files in output, 0-9.
        progress (optional): Print download progress bar to stdout, default False
        logger (optional): logger object

    Returns:
        The absolute path to the DRF folder or None.

    Raises:
        FileNotFoundError: 'src' does not exist 'dst' does not exist
        FileExistsError: 'dst/name' already exists

    """

    src = Path(src)
    if not (src.is_dir() or src.is_file()):
        raise FileNotFoundError(str(src))

    dst = Path(dst)
    if not dst.is_dir():
        os.makedirs(dst)
        # raise FileNotFoundError(str(dst))

    if name is None:
        name = f"{src.name}_drf"
    hdrf = dst / name
    if hdrf.exists():
        raise FileExistsError(str(hdrf))
    hdrf.mkdir(parents=True, exist_ok=True)

    files = eiscat_files(src)
    n_files = len(files)

    # load experiment info from first matlab file
    meta_first = eiscat_load_file(files[0])[0]

    # create sample writer
    sample_writer = drf_wrapper.DigitalRFWriter(
        hdrf,
        meta_first["exp"]["chnl"],
        meta_first["exp"]["sample_rate"],  # sample rate numerator
        1,  # samplerate denominator
        np.int16,
        meta_first["sample"]["file_start"],
        subdir_cadence_secs=3600,  # one dir per hour
        file_cadence_secs=1,  # one file per second
        is_complex=True,
        compression_level=compression,
        uuid_str=meta_first["exp"]["chnl"],
        ts_align_sec=meta_first["ts"]["file_start"],
    )

    # create pointing writer
    pointing_writer = drf_wrapper.DigitalMetadataWriter(
        hdrf,
        "pointing",
        meta_first["exp"]["sample_rate"],  # sample rate - numerator (int)
        # sample rate - denominator (int)
        meta_first["exp"]["samples_per_file"],
    )

    def pad_data(n_pad: int, file: Path) -> None:
        """Zero pad data with n zeros."""
        try:
            sample_writer.write(np.zeros(n_pad * 2, dtype=np.int16))
        except Exception as e:
            err = f"unable to zero pad samples for {file}"
            if logger:
                logger.error(err)
            raise e
        if logger:
            logger.debug(f"zero padding {n_pad} samples for {file}")

    def write_data(data: Any, file: Path) -> None:
        """Write data to sample writer."""
        try:
            sample_writer.write(data)
        except Exception as e:
            err = f"unable to write samples for {file}"
            if logger:
                logger.error(err)
            raise e

    def drop_data(errors: Any, file: Path) -> None:
        """On data drop log error and dropped file"""
        if logger:
            logger.info(f"dropping : {errors} : {file}")

    def log_progress(idx: int, n_files: int, period: int = 10) -> None:
        """Log the convert process"""
        if logger:
            if idx + 1 == n_files or idx % period == 0:
                logger.debug(f"write progress {idx+1}/{n_files}")

    def write_pointing(sample: int, pointing_data: dict[str, float]) -> None:
        """write pointing data"""
        ts = sample_writer.ts_from_index(sample)
        pointing_idx = int(pointing_writer.index_from_ts(ts))
        pointing_writer.write(pointing_idx, pointing_data)

    if logger:
        logger.info(f"writing DRF from {n_files} input files")

    if progress:
        pbar = tqdm(desc=f"Converting files to digital_rf: {src}", total=n_files)

    # processing loop
    for error in eiscat_process(
        files,
        write_data=write_data,
        pad_data=pad_data,
        drop_data=drop_data,
        write_pointing=write_pointing,
        log_progress=log_progress,
    ):
        if error:
            if logger:
                logger.debug(error)

        if progress:
            pbar.update(1)

    if progress:
        pbar.close()

    if logger:
        logger.info("Done writing DRF files")

    meta = configparser.ConfigParser()

    # Experiment
    meta.add_section(Metaparam.EXPERIMENT)
    exp = meta[Metaparam.EXPERIMENT]

    exp[Expparam.NAME] = str(meta_first["exp"]["name"])
    exp[Expparam.TX_PULSE_LENGTH] = str(meta_first["exp"]["tx_pulse_length"])
    exp[Expparam.T_RX_START_USEC] = str(meta_first["exp"]["rx_start"])
    exp[Expparam.T_RX_END_USEC] = str(meta_first["exp"]["rx_end"])
    exp[Expparam.T_TX_START_USEC] = str(meta_first["exp"]["tx_start"])
    exp[Expparam.T_TX_END_USEC] = str(meta_first["exp"]["tx_end"])
    exp[Expparam.T_CAL_ON_USEC] = str(meta_first["exp"]["cal_on"])
    exp[Expparam.T_CAL_OFF_USEC] = str(meta_first["exp"]["cal_off"])
    exp[Expparam.RADAR_FREQUENCY] = str(meta_first["exp"]["radar_frequency"])
    exp[Expparam.RX_CHANNELS] = str([meta_first["exp"]["chnl"]])
    exp[Expparam.TX_CHANNEL] = meta_first["exp"]["chnl"]
    exp[Expparam.SAMPLE_RATE] = str(meta_first["exp"]["sample_rate"])
    exp[Expparam.T_IPP_USEC] = str(int(meta_first["exp"]["ipp"]))

    # Bounds
    meta.add_section(Metaparam.BOUNDS)
    bounds = meta[Metaparam.BOUNDS]
    meta_last = eiscat_load_file(files[-1])[0]
    bounds[Boundparam.TS_START_USEC] = str(meta_first["ts"]["file_start"])
    bounds[Boundparam.TS_END_USEC] = str(meta_last["ts"]["file_end"])

    # write metadata file
    metafile = hdrf / "metadata.ini"
    with open(metafile, "w") as f:
        meta.write(f)

    return hdrf
