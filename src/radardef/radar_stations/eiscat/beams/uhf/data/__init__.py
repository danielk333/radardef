"Collect the paths to the available data in a easy to access format"

import importlib.resources
import pathlib

DATA_PATHS = {}

# To be compatible with 3.7-8
# as resources.files was introduced in 3.9
if hasattr(importlib.resources, "files"):
    _data_files = importlib.resources.files(__name__)
    for file in _data_files.iterdir():
        if not file.is_file():
            continue
        if file.name.endswith(".py"):
            continue

        DATA_PATHS[file.name] = pathlib.Path(str(file))

else:
    _data_folder = importlib.resources.contents(__name__)
    for fname in _data_folder:
        with importlib.resources.path(__name__, fname) as file:
            if not file.is_file():
                continue
            if file.name.endswith(".py"):
                continue

            DATA_PATHS[file.name] = pathlib.Path(str(file))
