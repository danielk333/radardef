"""
Class and functions to convert Eiscat mat.bz2 data to HDF5 format, the converter is based on
the Converter template
"""

import logging
from pathlib import Path
from typing import Optional

import h5py
import numpy as np

from radardef.components import Converter
from radardef.radar_stations.eiscat.utils.eiscat_utils import eiscat_files, eiscat_load_file
from radardef.radar_stations.eiscat.validators import MatBz2
from radardef.types.formats import TargetFormat

PARBLOCK_ELEVATION = 8
PARBLOCK_AZIMUTH = 9
PARBLOCK_FREQUENCY = 54  # Not stated in docs
PARBLOCK_INTEGRATIONTIME = 6
PARBLOCK_DUMPSEQUENCENUMBER = 11
PARBLOCK_CALIBRATION_TEMPERATURE = 20  # post-2000 format
PARBLOCK_ANTENNAID = 40


class MatBz2ToHDF5(Converter):
    """
    Converts a MatBz file to the EISCAT HDF5 format.

    The EISCAT HDF5 structure is as follows:
    ```
    Data/ Group
        EndTime: Dataset (array of end timepoint in format "2024-07-04T10:00:19.203")
        IntegrationTime: Dataset (amount of time covered at that array index)
        L1 : The data we are insterested in, in chunks of data covering the the time in integrationTime
             (n_dumps, 2 (real,imag), samples_per_dump)
        ParBlock/ Group
            ParBlock: Dataset, one set per "index or group"
            [b'Dump end year' b'Dump end month' b'Dump end days' b'Dump end hours' b'Dump end minutes'
             b'Dump end seconds' b'Integration time (s)' b'Combined output power (W)' b'Elevation (degrees)'
             b'Azimuth (degrees)' b'Dump end time (s since 1970)' b'Dump sequence number' b'NA' b'NA' b'NA' b'NA' b'NA'
             b'NA' b'NA' b'NA' b'Noise injection calibration (K)' b'Pre-integration factor (Always 1 on mainland)'
             b'NA' b'NA' b'NA' b'NA' b'NA' b'NA' b'NA' b'NA' b'Rx frequency, channel 1 (MHz)'
             b'Rx frequency, channel 2 (MHz)' b'Rx frequency, channel 3 (MHz)' b'Rx frequency, channel 4 (MHz)'
             b'Rx frequency, channel 5 (MHz)' b'Rx frequency, channel 6 (MHz)' b'Rx frequency, channel 7 (MHz)'
             b'Rx frequency, channel 8 (MHz)' b'Rx frequency, channel 9 (MHz)' b'd_parbl version number'
             b'Antenna ID (1: 32m, 2: 42m, 3: VHF, 4: UHF, 5: Kir, 6: Sod, 8: 32p)'
             b'Remote antenna intersection range (m)' b'User parameter' b'User parameter' b'User parameter'
             b'User parameter' b'User parameter' b'User parameter' b'User parameter' b'User parameter'
             b'User parameter' b'User parameter' b'User parameter' b'User parameter' b'User parameter'
             b'User parameter' b'User parameter' b'User parameter' b'User parameter' b'User parameter'
             b'User parameter' b'User parameter' b'High voltage reading (V)' b'Loop counter'
             b'Peak power read from wave guide (W)' b'RF duty cycle read from wave guide'
             b'Power status on Troms\xc3\xb8 systems (bitmap)']
    MetaData/ Group
        (Not needed right now)

    PortalDBReference/ Group
        DataStream: Dataset (channel)
        ExperimentName: Dataset (e.g leo_mpark_2.1u)
    ```
    """

    __logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.__compression = 0
        super().__init__(MatBz2(), TargetFormat.HDF5)

    def convert_single_object(self, src: Path, dst: Path) -> list[Path]:
        """
        Abstract method, convert from source format to target format

        Args:
            src: Path to source directory
            dst: Path to destination directory

        Returns:
            output: List of the generated files directories
        """
        return [convert_matbz2_to_hdf5(src, dst, progress=False, logger=self.__logger)]


def convert_matbz2_to_hdf5(
    src: Path, dst: Path, progress: bool = False, logger: Optional[logging.Logger] = None
) -> Path:
    """
    Converts eiscat MatBz2 to HDF5
    """

    src = Path(src)
    if not (src.is_dir() or src.is_file()):
        raise FileNotFoundError(str(src))

    dst = Path(dst)

    # Sort files by timepoint
    files = eiscat_files(src)
    sample_write = None

    # Get data from first file
    meta_first = eiscat_load_file(files[0])[0]
    measurement_date = str(meta_first["date"]["file_start"])[0:10]
    measurement_time = str(meta_first["date"]["file_start"])[11:19]
    measurement_ms = str(meta_first["date"]["file_start"])[20:]

    name = (
        "EISCAT_"
        + meta_first["exp"]["name"]
        + "_"
        + meta_first["exp"]["version"]
        + "_"
        + meta_first["exp"]["owner"]
        + "@"
        + meta_first["exp"]["chnl"]
        + "_"
        + measurement_date.replace("-", "")
        + "_"
        + measurement_time.replace(":", "")
        + "_"
        + measurement_ms
        + ".hdf5"
    )

    file_path = (
        dst / measurement_date / (measurement_time[0:2].replace(":", "") + "-00-00") / "converted_data" / name
    )

    if not file_path.parent.is_dir():
        file_path.parent.mkdir(parents=True)

    if file_path.is_file():
        if logger:
            logger.info(f"File already exists: {file_path}")

        return file_path.parent

    with h5py.File(str(file_path), "w") as hdf5_file:
        n_data_points = len(files)

        # Create structure
        # Data
        data_group = hdf5_file.create_group("Data")
        data_group.create_dataset("EndTime", (n_data_points,), dtype=h5py.string_dtype())
        data_group.create_dataset("IntegrationTime", (n_data_points,), dtype="f8")
        data_group.create_dataset("L1", (n_data_points, 2, meta_first["exp"]["samples_per_file"]), dtype="f8")
        par_block_group = data_group.create_group("ParBlock")
        par_block_group.create_dataset("ParBlock", (n_data_points, 67), dtype="f8")

        # PortalDBReference
        port_ref_group = hdf5_file.create_group("PortalDBReference")
        port_ref_group.create_dataset(
            "ExperimentName",
            data=[
                meta_first["exp"]["name"]
                + "_"
                + meta_first["exp"]["version"]
                + "_"
                + meta_first["exp"]["owner"]
            ],
        )
        port_ref_group.create_dataset("DataStream", data=[meta_first["exp"]["chnl"]])

        # Convert each file to a common file
        for i, file in enumerate(files):
            meta, data, pointing_data, errors = eiscat_load_file(file)

            sample_file_start = meta["sample"]["file_start"]
            if sample_write is None:
                sample_write = meta["sample"]["file_start"]

            if not errors:
                # check that we are not writing old data
                if sample_file_start < sample_write:
                    errors.append("attempt to overwrite data")
                # check if zero padding is needed
                n_pad = (sample_file_start - sample_write) % meta_first["exp"]["samples_per_file"]
                if n_pad > 0:
                    data = np.concatenate(np.zeros((2, n_pad)), data)

                # Fill data sections
                data_group["EndTime"][i] = meta["date"]["file_end"]
                data_group["IntegrationTime"][i] = meta_first["exp"]["file_secs"]
                data_group["L1"][i] = data.T

            else:
                # Fill data sections
                data_group["EndTime"][i] = meta["date"]["file_end"]
                data_group["IntegrationTime"][i] = meta_first["exp"]["file_secs"]
                data_group["L1"][i] = np.zeros((2, meta_first["exp"]["samples_per_file"]))

            for error in errors:
                if logger:
                    logger.warning("error")

            # Parameter block
            par_block = np.zeros((67,), dtype="f4")
            par_block[PARBLOCK_ELEVATION] = pointing_data["elevation"]
            par_block[PARBLOCK_AZIMUTH] = pointing_data["azimuth"]
            par_block[PARBLOCK_FREQUENCY] = meta["exp"]["radar_frequency"]
            par_block[PARBLOCK_INTEGRATIONTIME] = meta_first["exp"]["file_secs"]
            par_block[PARBLOCK_DUMPSEQUENCENUMBER] = i
            par_block[PARBLOCK_ANTENNAID] = AntennaID(meta_first["exp"]["chnl"])

            par_block_group["ParBlock"][i] = par_block
            # increment sample_write
            sample_write = sample_file_start + meta["exp"]["samples_per_file"]

    return file_path.parent


def AntennaID(id: str) -> int:
    """Convert eiscat antenna id to its corresponding integer"""

    if id.lower() == "32m":
        return 1
    elif id.lower() == "42m":
        return 2
    elif id.lower() == "vhf":
        return 3
    elif id.lower() == "uhf":
        return 4
    elif id.lower() == "kir":
        return 5
    elif id.lower() == "sod":
        return 6
    elif id.lower() == "32p":
        return 8
    else:
        return 0
