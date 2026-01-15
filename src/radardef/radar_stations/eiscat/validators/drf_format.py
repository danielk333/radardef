"""DRF validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import TargetFormat


class DRF(Validator):
    """Drf validator"""

    def __init__(self) -> None:
        super().__init__(TargetFormat.DRF)

    def validate(self, src: str | Path) -> bool:
        """Validate path is a directory and of drf format"""
        path = Path(src).resolve()
        return path.is_dir() and path.name.endswith("drf")
