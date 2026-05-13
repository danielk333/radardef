import importlib.util
from pathlib import Path
from typing import Optional

from radardef.components import DataLoader, Validator
from radardef.types.formats import TargetFormat
from radardef.types.types import ExpDef

from .hdf5_loader import HDF5Loader

if importlib.util.find_spec("digital_rf") is not None:
    from .drf_loader import DrfLoader
else:

    class NotAvailable(Validator):
        def __init__(self) -> None:
            super().__init__(TargetFormat.UNKNOWN)

        def validate(self, src: str | Path) -> bool:
            return False

    class DrfLoader(DataLoader):  # type: ignore[no-redef]
        converted_format = TargetFormat.UNKNOWN
        validator = NotAvailable()

        def __init__(
            self,
            path: Path | str,
            exp_def: Optional[ExpDef] = None,
        ):

            raise ImportError(
                "The optional dependency `digital_rf` for is missing.\n"
                "Install it with `pip install digital_rf`."
            )
