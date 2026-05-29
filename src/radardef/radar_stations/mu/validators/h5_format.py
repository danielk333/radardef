"""H5 validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import TargetFormat


class H5(Validator):
    """H5 validator"""

    def __init__(self) -> None:
        super().__init__(TargetFormat.H5)

    def validate(self, src: str | Path) -> bool:
        """Validate that the path is a h5 file of the correct format"""
        path = Path(src).resolve()

        return self._is_h5_file(path)

    def _is_h5_file(self, src: Path) -> bool:
        """H5 name format"""
        if len(src.name) < 11:
            return False
        return (src.name[10] == "T") and (src.suffix == ".h5")
