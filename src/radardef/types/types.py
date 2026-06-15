"""General types"""

from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import NamedTuple, Optional, TypeVar

import numpy as np
import numpy.typing as npt
import scipy.constants

P = TypeVar("P", bound="ExpDef")


class BoundParams(NamedTuple):
    """
    Time since epoch (standard unix) bounds
    """

    ts_start_usec: float | int = 0
    ts_end_usec: float | int = 0


class Pointing(NamedTuple):
    """
    Pointing
    """

    azimuth: float
    elevation: float


@dataclass(frozen=True)
class ExpDef:
    """
    Experiment defintion
    """

    name: str
    radar_frequency: float
    t_ipp_usec: int
    t_samp_usec: int
    t_rx_start_usec: int
    t_rx_end_usec: int
    t_tx_start_usec: int
    t_tx_end_usec: int
    baud_length_usec: int
    samples_per_file: int
    code: npt.NDArray[np.float64]
    rx_channels: list[str] | list[int]
    tx_channel: Optional[str | int] = None
    t_cal_on_usec: Optional[float] = None
    t_cal_off_usec: Optional[float] = None
    ipp_samps: int = field(init=False)
    sample_rate: float = field(init=False)
    wavelength: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_rate", 1 / (self.t_samp_usec * 1e-6))
        object.__setattr__(self, "wavelength", scipy.constants.c / (self.radar_frequency * 1e6))
        object.__setattr__(self, "ipp_samps", int(self.t_ipp_usec / self.t_samp_usec))

    def copy(self: P, **modifications) -> P:
        kwargs = {key.name: deepcopy(getattr(self, key.name)) for key in fields(self) if key.init}
        kwargs.update(modifications)
        return self.__class__(**kwargs)
