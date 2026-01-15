"""Enums to simplify the usage of the radar objects"""

from enum import IntEnum, StrEnum, auto


class SourceFormat(StrEnum):
    """Radar dataformats"""

    MUI = "mui"
    EISCAT_MATBZ = "eiscat_matbz"
    UNKNOWN = "unknown"


class TargetFormat(StrEnum):
    """Formats possible to convert to"""

    H5 = "h5"
    DRF = "drf"
    UNKNOWN = "unknown"


class StationID(StrEnum):
    """Radar station IDs"""

    MU = auto()
    PANSY = auto()
    TSDR = auto()
    ESR_32M = auto()
    ESR_42M = auto()
    EISCAT_3D = auto()
    EISCAT_UHF_TROMSO = auto()
    EISCAT_UHF_KIRUNA = auto()
    EISCAT_UHF_SODANKYLA = auto()
    EISCAT_VHF = auto()
    EISCAT_3D_SKIBOTN = auto()
    EISCAT_3D_KARESUVANTO = auto()
    EISCAT_3D_KAISENIEMI = auto()
    UNKNOWN = auto()


class EiscatUHFLocation(StrEnum):
    """Eiscat UHF locations"""

    TROMSO = auto()
    KIRUNA = auto()
    SODANKYLA = auto()


class Eiscat3DLocation(StrEnum):
    """Eiscat 3D locations"""

    SKIBOTN = auto()
    KARESUVANTO = auto()
    KAISENIEMI = auto()


class Stage(IntEnum):
    """Eiscat 3D radar stages"""

    SINGLE = 0
    STAGE_1 = 1
    STAGE_2 = 2


class BeamType(StrEnum):
    """Beam types"""

    MEASURED = "measured"
    CASSEGRAIN = "cassegrain"


class DishDiameter(StrEnum):
    """Dish diameter"""

    ESR_32M = "32m"
    ESR_42M = "42m"


class Metaparam(StrEnum):
    """Metadata parameter keys"""

    EXPERIMENT = auto()
    BOUNDS = auto()


class Expparam(StrEnum):
    """Experiment parameter keys"""

    NAME = auto()
    TX_PULSE_LENGTH = auto()
    T_RX_START_USEC = auto()
    T_RX_END_USEC = auto()
    T_TX_START_USEC = auto()
    T_TX_END_USEC = auto()
    T_CAL_ON_USEC = auto()
    T_CAL_OFF_USEC = auto()
    RADAR_FREQUENCY = auto()
    RX_CHANNELS = auto()
    TX_CHANNEL = auto()
    T_IPP_USEC = auto()
    T_SAMP_USEC = auto()
    SAMPLE_RATE = auto()
    DATE = auto()
    CODE = auto()
    PULSE = auto()


class Boundparam(StrEnum):
    """Bound parameter keys"""

    TS_START_USEC = auto()
    START = auto()
    TS_END_USEC = auto()
    END = auto()
