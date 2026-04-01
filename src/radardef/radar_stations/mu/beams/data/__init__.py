"Collect the paths to the available data in a easy to access format"

import importlib.resources
import pathlib

import numpy as np
import numpy.typing as npt

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


def get_yagi_specs() -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:

    assert "mu_yagi_gain.npz" in DATA_PATHS, "gain file missing!"
    _mu_yagi = np.load(DATA_PATHS["mu_yagi_gain.npz"])

    az = _mu_yagi["az_deg"].reshape(-1, 721)
    az -= 180
    el = _mu_yagi["el_deg"].reshape(-1, 721)
    gain_dB = _mu_yagi["gain_dB"].reshape(-1, 721)
    gain_dB = gain_dB - np.max(_mu_yagi["gain_dB"])

    return az, el, gain_dB


def get_antenna_pos() -> npt.NDArray:
    assert "MU_antenna_pos.npy" in DATA_PATHS, "pos file missing!"
    return np.load(DATA_PATHS["MU_antenna_pos.npy"])
