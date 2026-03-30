from enum import auto

# Python StrEnum has default lowercase for auto() but is only available from py 3.11
try:
    from enum import StrEnum
except ImportError:
    from strenum import (  # type: ignore[assignment, no-redef, unused-ignore, import-not-found]
        LowercaseStrEnum as StrEnum,  # type: ignore[import-not-found,no-redef, unused-ignore]
    )


class ExpGroup(StrEnum):
    leo_bpark = auto()
    leo_mpark = auto()
    leo_pwait = auto()
    leo_sat = auto()


class ExpVer(StrEnum):
    v1_0l = "1.0l"
    v1_0u = "1.0u"
    v2_0 = "2.0"
    v2_0u = "2.0u"
    v2_1u = "2.1u"
    v2_2 = "2.2"
    v2_3u = "2.3u"
    v2_3v = "2.3v"
    v2_3r = "2.3r"
    v2_4u = "2.4u"
    v2_5u = "2.5u"
