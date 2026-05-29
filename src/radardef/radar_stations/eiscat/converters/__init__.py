import importlib.util
from pathlib import Path

from radardef.components import Converter, Validator
from radardef.types.formats import SourceFormat, TargetFormat

from .matbz2_to_hdf5 import MatBz2ToHDF5

if importlib.util.find_spec("digital_rf") is not None:
    from .matbz2_to_drf import MatBz2ToDrf
else:

    class Unavailable(Validator):
        def __init__(self) -> None:
            super().__init__(SourceFormat.UNKNOWN)

        def validate(self, src: str | Path) -> bool:
            return False

    class MatBz2ToDrf(Converter):  # type: ignore[no-redef]
        def convert_single_object(self, src: Path, dst: Path) -> list[Path]:
            raise ImportError(
                "The optional dependency `digital_rf` for is missing.\n"
                "Install it with `pip install digital_rf`."
            )

        def __init__(self) -> None:
            super().__init__(Unavailable(), TargetFormat.UNKNOWN)
