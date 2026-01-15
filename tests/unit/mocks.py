from pathlib import Path
from typing import Callable
from unittest.mock import Mock, PropertyMock

import numpy as np

from radardef.components import Converter, DataLoader, RadarStation, Validator
from radardef.types import Metadata, SourceFormat, TargetFormat


def radar_mock(validator: Mock = None, converters: list[Mock] = None, data_loaders: list[Mock] = None):
    mock = Mock(spec=RadarStation)
    if validator is not None:
        type(mock).validator = PropertyMock(return_value=validator)
    if converters is not None:
        mock.get_converters.return_value = converters
    if data_loaders is not None:
        mock.get_data_loaders.return_value = data_loaders
    return mock


def validator_mock(format: SourceFormat, validator_func: Callable[[Path], bool]):
    mock = Mock(spec=Validator)
    type(mock).format = PropertyMock(return_value=format)
    mock.validate = validator_func
    return mock


def converter_mock(
    source_format: SourceFormat, target_format: TargetFormat, convert_func: Callable[[Path, Path], list[Path]]
):
    mock = Mock(spec=Converter)
    type(mock).source_format = PropertyMock(return_value=source_format)
    type(mock).target_format = PropertyMock(return_value=target_format)
    mock.convert = convert_func
    return mock


def data_loader_mock(
    converted_format: TargetFormat,
    meta: Metadata,
    validate_func: Callable[[Path], bool],
    read_func: Callable[[Path], np.ndarray],
):

    mock = Mock(spec=DataLoader)
    type(mock).converted_format = PropertyMock(return_value=converted_format)
    type(mock).meta = PropertyMock(return_value=meta)
    mock.validate = validate_func
    mock.load_data = read_func
    return mock
