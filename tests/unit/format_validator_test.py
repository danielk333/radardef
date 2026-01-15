import unittest
from pathlib import Path

from tests.unit import mocks

from radardef.collections import FormatCollection
from radardef.types import SourceFormat


class FormatCollectionTest(unittest.TestCase):

    def test_register_validator(self):

        # Eiscat validator
        validator_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: True)

        # create format validator
        format_collection = FormatCollection([])
        print(f"list: {format_collection.list_formats()}")
        # No validator should be available
        self.assertNotIn(SourceFormat.EISCAT_MATBZ, format_collection.list_formats())

        # register validator
        format_collection._register_validator(validator_mock.format, validator_mock.validate)

        # Validator should be available
        self.assertIn(SourceFormat.EISCAT_MATBZ, format_collection.list_formats())

    def test_simple_validator_mapping(self):

        validator_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: True)
        radar_mock = mocks.radar_mock(validator=validator_mock)

        format_collection = FormatCollection([radar_mock])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.EISCAT_MATBZ)

    def test_multiple_validators(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: True)
        radar_mock = mocks.radar_mock(validator=validator_eiscat_mock)
        radar_mock_2 = mocks.radar_mock(validator=validator_mui_mock)

        format_collection = FormatCollection([radar_mock, radar_mock_2])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.MUI)

    def test_no_matching_validator(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)
        radar_mock = mocks.radar_mock(validator=validator_eiscat_mock)
        radar_mock_2 = mocks.radar_mock(validator=validator_mui_mock)

        format_collection = FormatCollection([radar_mock, radar_mock_2])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.UNKNOWN)

    def test_list_validators(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)
        radar_mock = mocks.radar_mock(validator=validator_eiscat_mock)
        radar_mock_2 = mocks.radar_mock(validator=validator_mui_mock)

        format_collection = FormatCollection([radar_mock, radar_mock_2])

        list_formats = format_collection.list_formats()

        self.assertIn(SourceFormat.MUI, list_formats)
        self.assertIn(SourceFormat.EISCAT_MATBZ, list_formats)

    def test_is_format(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.EISCAT_MATBZ, lambda src: True)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)
        radar_mock = mocks.radar_mock(validator=validator_eiscat_mock)
        radar_mock_2 = mocks.radar_mock(validator=validator_mui_mock)

        format_collection = FormatCollection([radar_mock, radar_mock_2])

        self.assertFalse(format_collection.is_format(Path(), SourceFormat.MUI))
        self.assertTrue(format_collection.is_format(Path(), SourceFormat.EISCAT_MATBZ))
