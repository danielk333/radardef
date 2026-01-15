"""MUI format validator"""

from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import SourceFormat


class MUI(Validator):
    """MUI format validator"""

    def __init__(self) -> None:
        super().__init__(SourceFormat.MUI)

    def validate(self, src: str | Path) -> bool:
        "File is of format MUI"
        path = Path(src).resolve()
        return len(path.name) == 17 and path.name.startswith("MUI")
