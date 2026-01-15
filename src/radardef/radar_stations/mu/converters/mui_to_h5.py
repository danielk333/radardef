"""
This module contains functionality to convert MUI files to h5 for swifter loading and better data overview.
The converter is based on the Converter template

Conventions of the h5-format
-----------------------------

* dates and time are saved in numpy.datetime64[ns]
* the voltage data nd-array is saved in a dataset called "/data"

"""

import logging
import os
import warnings
from io import BufferedReader
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from tqdm import tqdm

import radardef.tools as tools
from radardef.components.converter_template import Converter
from radardef.types import SourceFormat, TargetFormat

logger = logging.getLogger(__name__)


class MuiToH5(Converter):
    """MUI to H5 converter."""

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__(SourceFormat.MUI, TargetFormat.H5)

    def convert(self, src: Path, dst: Path) -> list[Path]:
        """Convert MUI to h5, converted files are saved in dst"""
        output_directories: list[Path] = []
        if src.is_dir():
            for file in tqdm(
                src.iterdir(),
                total=len([f for f in src.iterdir() if f.is_file()]),
                desc=f"Converting files to h5: {src}",
            ):
                output_directories.append(convert_mui_to_h5(file, dst))
        elif src.is_file():
            output_directories.append(convert_mui_to_h5(src, dst))
        return list(set(output_directories))


def convert_mui_to_h5(
    src: Path, dst: Path, experiment_name: str = "mw26x6", skip_existing: bool = False
) -> Path:
    """
    Converts MU raw data to HDF5.

    Args:
        src: Path to source directory (Eiscat raw data)
        dst: Path to destination directory
        experiment_name (optional): Experiment name
        skip_existing (optional): Skip already existing files

    Returns:
        Path to generated HDF5 file directory

    """

    file_outputs_created = []

    try:
        file = open(src, "rb")
    except TypeError:
        logger.debug("File already open or wrong input type.")

    if hasattr(file, "mode"):
        if file.mode != "rb":
            logger.critical("File not open in binary mode.")
            return Path("")

    """
    Constants declared
    """
    SKIP_AMOUNT = 4480

    byte = file.read(1)
    file.seek(-1, 1)
    while byte != b"":
        """
        Initiating variables that will be used later.
        """
        header_data = _get_header_data(file)
        block_amount = header_data["mu_head_1_to_24"][2]
        observation_param_name = header_data["observation_param_name"]
        # I replace ':' with a ., as windows cannot save files with ':' in their name.
        start_time = np.datetime_as_string(header_data["record_start_time"]).replace(":", ".")
        dst_dated = (
            Path(str(dst)).joinpath(
                start_time[0:4],  # Year
                start_time[5:7],  # Month
                start_time[8:10],  # Day
            )
            if bool(dst)
            else Path("")
        )
        """
        Combined it will be something like "dst/20XX/YY/ZZ"
        Using str(dst) to safeguard against dst being None
        """
        output_file_name = Path(dst_dated).joinpath(start_time + ".h5")

        """
        Creates the directories if not yet created.
        """
        if not dst_dated.name == "" and not Path(dst_dated).is_dir():
            logger.debug(f"Creating file directories for location {dst_dated}")
            os.makedirs(dst_dated)

        if bool(dst):
            """
            Checks if dst has been set and if the directory already exists.
            If it does, it will check if the output file already exists. If it does and
            the "skip existing files" flag is set, it will skip those datasets.
            """
            # If the file already exists and you want to skip it
            if Path(output_file_name).is_file() and skip_existing:
                logger.debug(f'Skip existing set and file was found. Skipping file "{output_file_name}".')
                # Skip ahead to the next block
                file.seek(block_amount * SKIP_AMOUNT, 1)
                byte = file.read(1)
                file.seek(-1, 1)
                continue

        if observation_param_name.strip() != experiment_name:
            logger.critical(
                f'Experiment name "{experiment_name}" was not '
                + f'equal to observation parameter name "{observation_param_name}". Exiting.'
            )
            break

        """
        Opening the file properly so it closes if it crashes.
        """
        with h5py.File(output_file_name, "w") as h5file:
            """
            Allocating variables to hold the data.
            mu_data = [channel][ipp][sample]
            """
            ipp_samples = 85
            n_ipp = 512
            channels = 25
            channel_list = []
            mu_data = np.zeros((channels, n_ipp, ipp_samples), dtype="complex")

            for x in range(0, block_amount):
                """
                Block structure:

                    | 8 bit|  8 bit  | 16 bit |   32 bit x 512   |     32 bit x 512      |
                    | beam | channel | sample | 512 real numbers | 512 imaginary numbers |

                    Each block represents the x sample in each ipp for channel x,
                    when all samples for a channel has been read the next channel begins.
                    can be represented like:

                    block: 1    | sample 1 for ipp 1-512 in channel 1|
                    block: 2    | sample 2 for ipp 1-512 in channel 1|
                    .......
                    block: 85   | sample 85 for ipp 1-512 in channel 1|
                    block: 86   | sample 1 for ipp 1-512 in channel 2|


                NOTE: each block ends with 380 blank bytes and should be skipped
                """

                beam = np.fromfile(file, dtype=">i1", count=1)[0]
                channel = np.fromfile(file, dtype=">i1", count=1)[0]  # alt: (x // ipp_samples) % channels
                ipp_sample = np.fromfile(file, dtype=">i2", count=1)[0]  # x % ipp_samples

                real_numbers = np.fromfile(file, dtype=">f4", count=n_ipp)
                complex_numbers = np.fromfile(file, dtype=">f4", count=n_ipp)
                data = real_numbers + 1j * complex_numbers

                mu_data[channel - 1, :, ipp_sample - 1] = data

                if channel not in channel_list:
                    channel_list.append(channel)
                file.seek(380, 1)

            """
            Adding all header data as attributes to the hdf5 file.
            """
            for key, val in header_data.items():
                logger.debug(f"Setting file attribute {key} to {val}")
                if type(val) == np.datetime64:
                    h5file.attrs[key] = str(np.datetime_as_string(val))
                else:
                    h5file.attrs[key] = val
            h5file.attrs["filename"] = src.name
            h5file.attrs["date"] = str(np.datetime_as_string(header_data["record_start_time"]))
            h5file.attrs["path"] = str(src.resolve())

            logger.debug("Creating dataset data, and saving to file")
            h5file.create_dataset("data", data=mu_data)
            h5file.create_dataset("rx_channels", data=channel_list)
            file_outputs_created.append(str(output_file_name))

        byte = file.read(1)
        file.seek(-1, 1)

    logger.debug("Reached EOF, exiting loop and closing file")
    file.close()
    return dst_dated


def _get_header_data(file: BufferedReader) -> dict:
    """
    Retrieves the meta/headerdata from a MUI file for later conversion and for
    use in parsing information.
    """
    header_data: dict[str, Any] = dict()

    # Copyright Csilla Szasz, Kenneth Kullbrandt, Daniel Kastinen
    """
    %-- Row 1 of the header
    %-- Reading the header of one record
    %-- (Byte position: 1-24) The first 6 numbers are integers,
    %-- four bytes long, each byte consisting of 8 bits -> each
    %-- integer is represented by 4x8=32 bits.
    """
    header_data["mu_head_1_to_24"] = np.fromfile(file, dtype=">i4", count=6)

    """
    %-- (25-32) The data taking program name is 8 bytes
    %-- -> 8x8=64 bits and is written in ASCII.
    """
    header_data["program_name"] = _decode_utf(np.fromfile(file, dtype="S8", count=1))

    """
    %-- (33-56) Parameter file load time: 24 bytes, of characters: dd-mmm-yyyy hh:mm:ss(.ss?)
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        header_data["file_load_time"] = np.datetime64(
            _convert_date(np.fromfile(file, dtype="S24", count=1)).strip() + "Z", "ns"
        )

    """
    %-- (57-60) The data taking program number, 4 bytes -> 4*8=32 bits.
    """
    header_data["program_number"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (61-84) Record start time: DD-MMM-YYYY hh:mm:ss.ss is 24 bytes long, each 8 bits
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        header_data["record_start_time"] = np.datetime64(
            _convert_date(np.fromfile(file, dtype="S24", count=1)).strip() + "Z", "ns"
        )

    """
    %-- (85-96) Record end time: hh:mm:ss.ss is 12 bytes long
    %-- Since "record_end_time" is only given in hh:mm:ss.ss, we want to use the 'dd-mmm-yyy ' part
    %-- of "record_start_time" to be able to convert recend into matlab serial date number.
    %-- To do this we need to convert it to a string and extract the first 10 symbsols and then
    %-- decode the rest from the file. After this we check so an edge case where the day rolled over
    %-- hasn't occured.
    """
    start_date = np.datetime_as_string(header_data["record_start_time"])[0:10]
    end_time = _decode_utf(np.fromfile(file, dtype="S12", count=1))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        temp_end_time = np.datetime64((start_date + " " + end_time).strip() + "Z", "ns")
    header_data["record_end_time"] = _fix_date_edge_case(header_data["record_start_time"], temp_end_time)

    """
    %-- (97-172) The next 19 numbers are 4 byte integers, i.e. 4*8=32 bits long
    """
    header_data["mu_head_25_to_43"] = np.fromfile(file, dtype=">i4", count=19)

    """
    %-- (173-256) The lag number of each ACF point is 21 unsigned longwords represented by 84 bytes,
    %-- i.e. each longword is 84/21=4 bytes of 8 bits each, i.e., the same thing as matlab's int32
    """
    header_data["lag_number_per_ACF"] = np.fromfile(file, dtype=">u4", count=21)

    """
    %-- (257-320) The beam direction number in first 16 beams is represented by 16 unsigned longwords
    %-- of 4 bytes and 4*8=32 bits each
    """
    header_data["beam_direction_number"] = np.fromfile(file, dtype=">u4", count=16)

    """
    %-- (321-336) The next 4 parameters are 4 byte, 4*8=32 bit, integers
    """
    header_data["mu_head_81_to_84"] = np.fromfile(file, dtype=">i4", count=4)

    """
    %-- (337-344) The HP parameter file name is 8 bytes, i.e. 8*8=64 bits
    %-- cannot add characters to the 'head' matrix
    """
    header_data["hp_file_name"] = _decode_utf(np.fromfile(file, dtype="S8", count=1))

    """
    %-- (345-352) The next two parameters are 4 byte, i.e. 4*8=32 bit, integers
    """
    header_data["mu_head_87_to_88"] = np.fromfile(file, dtype=">i4", count=2)

    """
    %-- (353-416) The number of sum (ACF method): 16 unsigned longwords -> 16 * 4 byte (4*8=32 bit) integers
    """
    header_data["number_of_sum_ACF"] = np.fromfile(file, dtype=">u4", count=16)

    """
    %-- (417-420) Number of sample poinst: 4 bytes = 32 bits
    """
    header_data["sample_points"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (421-600) The next 180 bytes are empty, reserved for the future, so we step
    %-- (601-616) Observation parameter name: 16 bytes
    """
    header_data["observation_param_name"] = _decode_utf(np.fromfile(file, dtype="S16", count=1, offset=180))

    """
    %-- (617-640) The next 6 parameters are 4 bytes (4*8=32bits) each
    """
    header_data["mu_head_155_to_160"] = np.fromfile(file, dtype=">i4", count=6)

    """
    %-- (641-896) Transmitted pulse pattern: 32 bits * 64
    """
    header_data["transmitted_pulse_pattern"] = np.fromfile(file, dtype=">i4", count=64)

    """
    %-- (897-904) The next 2 parameters are 4 bytes (4*8=32 bits) each
    """
    header_data["mu_head_224_to_225"] = np.fromfile(file, dtype=">i4", count=2)

    """
    %-- (905-1160) Pulse decoding pattern for all channel: 32 bits * 64
    """
    header_data["pulse_decoding_patterns"] = np.fromfile(file, dtype=">i4", count=64)

    """
    %-- (1161-1164) Beam stearing interval: 4 bytes (4*8=32 bits)
    """
    header_data["beam_stearing_interval"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (1165-1676) Beam direction: 2 bytes (2*8=16 bits) * 256
    %-- Cannot put this into the matrix - 256 numbers into 128 slots
    """
    header_data["beam_directions"] = np.fromfile(file, dtype=">i2", count=256)

    """
    %-- (1677-1696) The next 5 parameters are 4 bytes (2*8=32 bits) each
    """
    header_data["mu_head_420_to_424"] = np.fromfile(file, dtype=">i4", count=5)

    """
    %-- (1697-1716) TX frequency offset of 5 unsigned longwords -> 5 * 4 byte (4*8=32 bit) integers
    """
    header_data["tx_frequency"] = np.fromfile(file, dtype=">u4", count=5)

    """
    %-- (1717-1724) The next 2 parameters are 4 bytes (2*8=32 bits) each
    """
    header_data["mu_head_430_to_431"] = np.fromfile(file, dtype=">i4", count=2)

    """
    %-- (1725-1740) The RX attenuator is 4 unsigned longwords -> 4 * 4 byte (4*8=32 bit) integers
    """
    header_data["rx_attentuator"] = np.fromfile(file, dtype=">u4", count=4)

    """
    %-- (1741-1744) The state of the TX is given by a 4 byte (4*8=32 bit) integer
    """
    header_data["tx_state"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (1745-1760) The state of the RX is given by 4 unsigned longwords -> 4 * 4 byte (4*8=32 bit) integers
    """
    header_data["rx_state"] = np.fromfile(file, dtype=">u4", count=4)

    """
    %-- (1761:1812) The RX module selection is given by 2 bytes * (25+1)
    %-- -> cannot be saved in the head matrix (no room for it)
    """
    header_data["rx_module_selection"] = np.fromfile(file, dtype=">i2", count=26)

    """
    %-- (1813:1820) The next 2 parameters are 4 bytes (2*8=32 bits) each
    """
    header_data["mu_head_454_to_455"] = np.fromfile(file, dtype=">i4", count=2)

    """
    %-- (1821-2844) The sample start time is represented by 256
    %-- unsigned longwords (unit of sub-pulse/4) -> 256 * 4 byte (4*8=32 bit) integer
    """
    header_data["sample_start_time"] = np.fromfile(file, dtype=">u4", count=256)

    """
    %-- (2845-2848) The reception sequence: 4 byte (4*8=32 bit) integer
    """
    header_data["reception_sequence"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (2849-2964) The channel number in digital combine: 29 * 4 bytes (4*4=32 bits)
    """
    header_data["channel_number_digital"] = np.fromfile(file, dtype=">i4", count=29)

    """
    %-- (2965-3080) Number of coherent integrations for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["coherent_integrations"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (3081-3196) Number of FFT points for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["fft_points"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (3197-3312) Number of data points for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["data_points"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (3313-3428) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """
    header_data["lo_hi_bound_fft_0"] = np.fromfile(file, dtype=">i2", count=58)

    """
    %-- (3429-3544) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """
    header_data["lo_hi_bound_fft_1"] = np.fromfile(file, dtype=">i2", count=58)

    """
    %-- (3545-3660) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """
    header_data["lo_hi_bound_fft_2"] = np.fromfile(file, dtype=">i2", count=58)

    """
    %-- The above numbers don't fit into the head matrix (58 numbers but 29 slots)
    %-- They are put into a matrix of their own: IFFT = [IFFT1  IFFT2  IFFT3]
    %-- (3661-3776) RX frequency offset for ach combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["rx_frequency_offset"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (3777-3808) FIR coefficient in RX: 16 * 2 bytes (2*8=16 bits)
    %-- Doesn't fit into the head matrix: 16 numbers into 8 slots...
    """
    header_data["fir_rx_coefficient"] = np.fromfile(file, dtype=">i2", count=16)

    """
    %-- (3809-3924) Gain adjustment of FIR filter in RX for each combined channel:
    %-- 29 * 2 bytes (2*8=16 bits each)
    %-- Cannot fit into the head matrix: 58 number into 29 slots
    """
    header_data["fir_rx_gain"] = np.fromfile(file, dtype=">i2", count=58)

    """
    %-- (3925-3940) The next four parameters are 4 bytes each, i.e. 4*8=32 bits
    """
    header_data["mu_head_982_to_985"] = np.fromfile(file, dtype=">i4", count=4)

    """
    %-- (3941-4056) Number of CIC filter in RX for each cmobined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["cic_rx_filter_amount"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (4057-4172) CIC cropping rate in RX for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """
    header_data["cic_rx_cropping_rate"] = np.fromfile(file, dtype=">u4", count=29)

    """
    %-- (4173-4176) Above sea level:
    """
    header_data["above_sea_level"] = np.fromfile(file, dtype=np.float32, count=1)

    """
    %-- (4177-4180) Header flag: 4 bytes, i.e., 4*8=32 bits
    """
    header_data["header_flag"] = np.fromfile(file, dtype=">i4", count=1)

    """
    %-- (4181-4260) Comment by user: 80 bytes (80*8=640 bits)
    """
    header_data["user_comment"] = _decode_utf(np.fromfile(file, dtype="S80", count=1))

    """
    %-- (4261-4272) The next 3 parameters are 4 bytes (4*8=32 bits) each
    """
    header_data["mu_head_1066_to_1068"] = np.fromfile(file, dtype=">i4", count=3)

    """
    %-- (4273-4480) User header: 4480-4273+1 = 208 bytes
    """
    header_data["user_header"] = _decode_utf(np.fromfile(file, dtype="S208", count=1))
    return header_data


def _decode_utf(ucs_nd: np.ndarray) -> str:
    """
    Converts a UCS-4 numpy ndarray into a UTF-8 python string.
    It first views it as a chararray to access the decode method,
    then squeezes it and converts it from a ndarray into a python string.
    After this, I remove the ' at the beginning and end of the string.
    """
    return np.array2string(ucs_nd.view(np.char.chararray).decode("utf-8").squeeze())[1:-1]


def _convert_date(date_np: np.ndarray) -> str:
    """
    Since the datetimes involved are given in the form "DD-MMM-YYYY hh:mm:ss.ss"
    and numpy expects the form "YYYY-MM-DD hh:mm:ss.ss(...)", we must first convert
    the MU date to numpy standard format. This is accomplished with the help of the
    month dictionary and the _decode_utf function.
    """
    if type(date_np) == np.ndarray:
        date_str = _decode_utf(date_np)
    return date_str[7:11] + "-" + _month[date_str[3:6]] + "-" + date_str[0:2] + date_str[11:]


_month = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}


def _fix_date_edge_case(start_time: np.datetime64, end_time: np.datetime64) -> np.datetime64:
    """
    Checks so the date hasn't rolled over, and if it has it adds a day to the counter.
    """
    if end_time - start_time < 0:
        logger.info("Date rolled over for dataset")
        return end_time + np.timedelta64(1, "D")
    return end_time
