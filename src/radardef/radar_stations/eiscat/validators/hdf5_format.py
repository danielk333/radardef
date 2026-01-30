"""Eiscat .hdf5 validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import TargetFormat


class HDF5(Validator):
    """Eiscat hdf5 validator"""

    def __init__(self) -> None:
        super().__init__(TargetFormat.HDF5)

    def validate(self, src: str | Path) -> bool:
        """Validate file is a Eiscat hdf5 file"""
        path = Path(src).resolve()
        return path.name.endswith(".hdf5")
