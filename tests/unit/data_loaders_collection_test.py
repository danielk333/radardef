import unittest
from pathlib import Path

import numpy as np
from tests.unit import mocks

from radardef.collections import DataLoaderCollection
from radardef.types import BoundParams, ExpParams, Metadata, SourceFormat, TargetFormat


class DataLoaderCollectionTest(unittest.TestCase):

    def test_load_data_mapping(self):

        mui_h5_metadata = Metadata(
            ExpParams(name="mui_h5"),
            BoundParams(),
        )
        data_loader_mui_h5_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.H5,
            meta=mui_h5_metadata,
            validate_func=lambda src: True,
            read_func=lambda src: np.empty(3),
        )
        mui_drf_metadata = Metadata(
            ExpParams(name="mui_drf"),
            BoundParams(),
        )
        data_loader_mui_drf_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.DRF,
            meta=mui_drf_metadata,
            validate_func=lambda src: False,
            read_func=lambda src: np.empty(3),
        )
        mui_eiscat_metadata = Metadata(
            ExpParams(name="eiscat_drf"),
            BoundParams(),
        )
        data_loader_eiscat_drf_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.DRF,
            meta=mui_eiscat_metadata,
            validate_func=lambda src: False,
            read_func=lambda src: np.empty(3),
        )

        data_loader_mocks = [data_loader_mui_h5_mock, data_loader_mui_drf_mock, data_loader_eiscat_drf_mock]

        radar_mock = mocks.radar_mock(data_loaders=data_loader_mocks)

        data_loader_collection = DataLoaderCollection([radar_mock])

        loader = data_loader_collection.load_data(Path(""))

        assert loader is not None

        metadata = loader.meta

        self.assertEqual(metadata.experiment.name, "mui_h5")

    def test_get_load_format(self):

        mui_h5_metadata = Metadata(
            ExpParams(name="mui_h5"),
            BoundParams(),
        )
        data_loader_mui_h5_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.H5,
            meta=mui_h5_metadata,
            validate_func=lambda src: False,
            read_func=lambda src: np.empty(3),
        )
        mui_drf_metadata = Metadata(
            ExpParams(name="mui_drf"),
            BoundParams(),
        )
        data_loader_mui_drf_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.DRF,
            meta=mui_drf_metadata,
            validate_func=lambda src: False,
            read_func=lambda src: np.empty(3),
        )
        mui_eiscat_metadata = Metadata(
            ExpParams(name="eiscat_drf"),
            BoundParams(),
        )
        data_loader_eiscat_drf_mock = mocks.data_loader_mock(
            converted_format=TargetFormat.DRF,
            meta=mui_eiscat_metadata,
            validate_func=lambda src: True,
            read_func=lambda src: np.empty(3),
        )

        data_loader_mocks = [data_loader_mui_h5_mock, data_loader_mui_drf_mock, data_loader_eiscat_drf_mock]

        radar_mock = mocks.radar_mock(data_loaders=data_loader_mocks)

        data_loader_collection = DataLoaderCollection([radar_mock])

        converted_format = data_loader_collection._get_load_format(Path(""))

        self.assertEqual(converted_format, TargetFormat.DRF)
