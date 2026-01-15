"""Enums and typed dicts to describe metadata, a standardized dict that each data loader should return"""

from typing import NamedTuple, Optional

import numpy as np
import numpy.typing as npt


# TODO: SI units?
class ExpParams(NamedTuple):
    """
    Experiment parameters
    """

    name: str = "Default"
    radar_frequency: float = 0.0
    t_ipp_usec: float = 0
    ipp_samps: int = 0
    sample_rate: float = 0.0
    t_samp_usec: float = 0
    rx_channels: list[str] | list[int] = []
    t_rx_start_usec: float = 0.0
    t_rx_end_usec: float = 0.0
    t_tx_start_usec: float = 0.0
    t_tx_end_usec: float = 0.0
    wavelength: float = 0.0
    tx_channel: Optional[str | int] = None
    tx_pulse_length: Optional[int] = None
    t_cal_on_usec: Optional[float] = None
    t_cal_off_usec: Optional[float] = None
    data: Optional[np.datetime64] = None
    code: npt.NDArray[np.float64] = np.empty((10,), dtype=np.float64)
    pulse: Optional[int] = None


class BoundParams(NamedTuple):
    """
    Time since epoch (standard unix) bounds
    """

    ts_start_usec: float | int = 0
    ts_end_usec: float | int = 0


class Metadata(NamedTuple):
    """
    Metadata
    """

    experiment: ExpParams
    bounds: BoundParams


class Pointing(NamedTuple):
    """
    Pointing
    """

    data: list[tuple[int, dict[str, float]]]
    sample_rate: float
