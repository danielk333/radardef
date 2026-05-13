"""Eiscat mat.bz2 validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import SourceFormat


class MatBz2(Validator):
    """Eiscat mat.bz2 validator"""

    def __init__(self) -> None:
        super().__init__(SourceFormat.MATBZ2)

    def validate(self, src: str | Path) -> bool:
        """Validate file is a Eiscat mat.bz2 file"""
        path = Path(src).resolve()
        return path.name.endswith(".mat.bz2")
