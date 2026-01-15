import configparser
import importlib.resources
import pathlib

import numpy as np
from numpy.typing import NDArray

EXP_FILES: dict[str, pathlib.Path] = {}

# To be compatible with 3.7-8
# as resources.files was introduced in 3.9
if hasattr(importlib.resources, "files"):
    _data_files = importlib.resources.files("radardef.radar_stations.eiscat.utils")
    for file in _data_files.iterdir():
        if isinstance(file, pathlib.Path):
            if not file.is_file():
                continue
            if file.name.endswith(".py"):
                continue

            EXP_FILES[file.name] = file.resolve()

else:
    _data_content = importlib.resources.contents("radardef.radar_stations.eiscat.utils")
    for fname in _data_content:
        with importlib.resources.path("radardef.radar_stations.eiscat.utils", fname) as file:
            if not file.is_file():
                continue
            if file.name.endswith(".py"):
                continue

            EXP_FILES[file.name] = pathlib.Path(str(file)).resolve()


def load_radar_code(xpname: str) -> NDArray[np.float64]:
    """Load radar code, xpname + _code.txt."""

    code_name = xpname + "_code.txt"
    assert code_name in EXP_FILES, f"radar code '{code_name}' not found in pre-defined configurations"
    code_file = EXP_FILES[code_name]
    try:
        with open(code_file, "r") as fh:
            code = []
            for line in fh:
                code.append([1 if ch == "+" else -1 for ch in line.strip()])
        return np.array(code, dtype=np.float64)
    except Exception as e:
        raise ValueError(f"Couldn't open code file for {xpname}:" + str(e))


def load_expconfig(xpname: str) -> configparser.ConfigParser:
    """load expconfig, any .ini file"""
    cfg_name = xpname + ".ini"
    assert cfg_name in EXP_FILES, f'experiment "{cfg_name}" not found in pre-defined configurations'
    cfg_file = EXP_FILES[cfg_name]
    try:
        cfg = configparser.ConfigParser()
        cfg.read_file(open(cfg_file, "r"))
        return cfg
    except Exception as e:
        raise ValueError(f"Couldn't open config file for {xpname}:" + str(e))
