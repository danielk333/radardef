import configparser
import importlib.resources
import logging
import pathlib

import numpy as np
from numpy.typing import NDArray

from radardef.radar_stations.eiscat.experiments.constants import ExpGroup, ExpVer
from radardef.types import ExpDef

logger = logging.getLogger(__name__)

EISCAT_EXPERIMENTS: dict[ExpGroup, dict[ExpVer, ExpDef]] = {group: {} for group in ExpGroup}
EXP_FILES: dict[str, pathlib.Path] = {}

# To be compatible with 3.7-8
# as resources.files was introduced in 3.9
if hasattr(importlib.resources, "files"):
    _data_files = importlib.resources.files("radardef.radar_stations.eiscat.experiments")
    for file in _data_files.iterdir():
        if isinstance(file, pathlib.Path):
            if not file.is_file():
                continue
            if file.name.endswith(".py"):
                continue

            EXP_FILES[file.name] = file.resolve()

else:
    _data_content = importlib.resources.contents("radardef.radar_stations.eiscat.experiments")
    for fname in _data_content:
        with importlib.resources.path("radardef.radar_stations.eiscat.experiments", fname) as file:
            if not file.is_file():
                continue
            if file.name.endswith(".py"):
                continue

            EXP_FILES[file.name] = pathlib.Path(str(file)).resolve()


def load_radar_code(xpname: ExpGroup | str) -> NDArray[np.float64]:
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


try:
    from radardef.radar_stations.eiscat.experiments.leo_bpark import (
        leo_bpark_2_0,
        leo_bpark_2_0u,
        leo_bpark_2_1u,
        leo_bpark_2_2,
        leo_bpark_2_3v,
        leo_bpark_2_4u,
        leo_bpark_2_5u,
    )

    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_0] = leo_bpark_2_0
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_0u] = leo_bpark_2_0u
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_1u] = leo_bpark_2_1u
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_2] = leo_bpark_2_2
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_3v] = leo_bpark_2_3v
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_4u] = leo_bpark_2_4u
    EISCAT_EXPERIMENTS[ExpGroup.leo_bpark][ExpVer.v2_5u] = leo_bpark_2_5u
except ImportError:
    logger.warning("Could not import leo_bpark experiments")

try:
    from radardef.radar_stations.eiscat.experiments.leo_mpark import leo_mpark_2_1u

    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_1u] = leo_mpark_2_1u
except ImportError:
    logger.warning("Could not import leo_mpark experiments")

try:
    from radardef.radar_stations.eiscat.experiments.leo_pwait import (
        leo_pwait_2_3r,
        leo_pwait_2_3u,
        leo_pwait_2_3v,
        leo_pwait_2_4u,
        leo_pwait_2_5u,
    )

    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_3r] = leo_pwait_2_3r
    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_3u] = leo_pwait_2_3u
    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_3v] = leo_pwait_2_3v
    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_4u] = leo_pwait_2_4u
    EISCAT_EXPERIMENTS[ExpGroup.leo_mpark][ExpVer.v2_5u] = leo_pwait_2_5u

except ImportError:
    logger.warning("Could not import leo_pwait experiments")

try:
    from radardef.radar_stations.eiscat.experiments.leo_sat import leo_sat_1_0l, leo_sat_1_0u

    EISCAT_EXPERIMENTS[ExpGroup.leo_sat][ExpVer.v1_0l] = leo_sat_1_0l
    EISCAT_EXPERIMENTS[ExpGroup.leo_sat][ExpVer.v1_0u] = leo_sat_1_0u

except ImportError:
    logger.warning("Could not import leo_sat experiments")


def get_experiment(group: ExpGroup | str, version: ExpVer | str) -> ExpDef:
    try:
        return EISCAT_EXPERIMENTS[ExpGroup(group)][ExpVer(version)]
    except KeyError:
        raise ValueError(f"No experiment with name: {group} and version: {version} available")
