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

        if path.is_file():
            return self._is_h5_file(path)
        else:
            files = [f for f in path.iterdir() if self._is_h5_file(f)]
            return len(files) > 0

    def _is_h5_file(self, src: Path) -> bool:
        """Compatible h5 file"""
        return (len(src.name) == 32) and (src.name[10] == "T") and (src.suffix == ".h5")
