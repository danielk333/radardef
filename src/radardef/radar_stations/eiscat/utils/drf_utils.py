"""Utility function for accessing DRF."""

import datetime as dt


def ts_from_str(datetime_str: str, as_local: bool = False) -> float:
    """
    Convert from human-readable string (ISO 8601 without a time zone) to a timestamp (seconds since epoch).

    Args:
        datetime_str: datetime as human readable string
        as_local (optional): By default, the string is interpreted as UTC time unless <as_local> is True,
            in which case the string is interpreted as local time.

    Returns:
        Timestamp
    """
    # Parse the string into a naive datetime object
    _datetime = dt.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")

    if as_local:
        # Make it timezone-aware as local time
        _datetime = _datetime.astimezone()
    else:
        # Make it timezone-aware as UTC
        _datetime = _datetime.replace(tzinfo=dt.timezone.utc)

    # Return the timestamp
    return _datetime.timestamp()


def str_from_ts(ts: float, as_local: bool = False) -> str:
    """
    Convert from a timestamp (seconds since epoch) to a human-readable string (ISO 8601 without a time zone).

    Args:
        ts: timestamp
        as_local (optional): If true return local time, default UTC time

    Returns:
        Timestamp as human readable string
    """
    if as_local:
        # Convert to local time (timezone-aware)
        _datetime = dt.datetime.fromtimestamp(ts).astimezone()
    else:
        # Convert to UTC (timezone-aware)
        _datetime = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)

    # Format the datetime as a string
    return _datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")


def ts_from_index(idx: int, sample_rate: float, ts_offset_sec: int = 0) -> float:
    """
    Convert from sample idx to timestamp

    Args:
        idx: Sample index (first sample is index 0)
        sample_rate: Samples per seconds
        ts_offset_sec (optional): Timestamp in seconds since Epoch (1970:01:10T00:00:00)
            ts_offset is the timestamp corresponding to index 0,
            by default this is 0, implying that indexing starts at Epoch (1970:01:10T00:00:00)

    Returns
        Timestamp corresponding to given sample index

    """
    return (idx / sample_rate) + ts_offset_sec


def index_from_ts(ts: float, sample_rate: float, ts_offset_sec: int = 0) -> int:
    """
    Convert from timestamp to sample index

    Args:
    ts: timestamp in seconds from Epoch (1970:01:10T00:00:00)
    sample_rate: samples per seconds
    ts_offset_sec (optional): timestamp in seconds since Epoch (1970:01:10T00:00:00)
        ts_offset is the timestamp corresponding to index 0,
        by default this is 0, implying that indexing starts at Epoch (1970:01:10T00:00:00)

    Returns:
        sample index (first sample is index 0)
    """

    return int((ts - ts_offset_sec) * sample_rate)
