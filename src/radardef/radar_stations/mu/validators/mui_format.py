"""MUI format validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import SourceFormat


class MUI(Validator):
    """MUI format validator"""

    def __init__(self) -> None:
        super().__init__(SourceFormat.MUI)

    def validate(self, src: str | Path) -> bool:
        """Validate that the path is a h5 file of the correct format"""
        path = Path(src).resolve()

        return self._is_mui_file(path)

    def _is_mui_file(self, path: Path) -> bool:
        """MUI name format"""
        return len(path.name) == 17 and path.name.startswith("MUI")
