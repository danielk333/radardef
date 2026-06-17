import unittest
from pathlib import Path

from radardef.collections import DataLoaderCollection
from radardef.components import DataLoader
from radardef.radar_stations.eiscat.experiments import leo_bpark_2_0, leo_mpark_2_1u
from radardef.radar_stations.mu.experiments import mu_exp
from radardef.types import TargetFormat
from tests.unit import mocks


class DataLoaderCollectionTest(unittest.TestCase):
    def test_load_data_mapping(self):

        class H5MuLoader(DataLoader):
            converted_format = TargetFormat.H5
            validator = mocks.validator_mock(TargetFormat.H5, lambda src: True)

            @property
            def exp_def(self):
                return mu_exp

        class DrfBParkLoader(DataLoader):
            converted_format = TargetFormat.DRF
            validator = mocks.validator_mock(TargetFormat.DRF, lambda src: False)

            @property
            def exp_def(self):
                return leo_bpark_2_0

        class DrfMParkLoader(DataLoader):
            converted_format = TargetFormat.DRF
            validator = mocks.validator_mock(TargetFormat.DRF, lambda src: False)

            @property
            def exp_def(self):
                return leo_mpark_2_1u

        data_loader_mocks = [H5MuLoader, DrfBParkLoader, DrfMParkLoader]

        data_loader_collection = DataLoaderCollection(data_loader_mocks)

        loader = data_loader_collection.load_data(Path(""))

        assert loader is not None

        self.assertEqual(loader.exp_def.name, mu_exp.name)

    def test_get_load_format(self):

        class H5MuLoader(DataLoader):
            converted_format = TargetFormat.H5
            validator = mocks.validator_mock(TargetFormat.H5, lambda src: False)

            @property
            def exp_def(self):
                return mu_exp

        class DrfBParkLoader(DataLoader):
            converted_format = TargetFormat.DRF
            validator = mocks.validator_mock(TargetFormat.DRF, lambda src: False)

            @property
            def exp_def(self):
                return leo_bpark_2_0

        class DrfMParkLoader(DataLoader):
            converted_format = TargetFormat.DRF
            validator = mocks.validator_mock(TargetFormat.DRF, lambda src: True)

            @property
            def exp_def(self):
                return leo_mpark_2_1u

        data_loader_mocks = [H5MuLoader, DrfBParkLoader, DrfMParkLoader]

        data_loader_collection = DataLoaderCollection(data_loader_mocks)

        converted_format = data_loader_collection._get_load_format(Path(""))

        self.assertEqual(converted_format, TargetFormat.DRF)
