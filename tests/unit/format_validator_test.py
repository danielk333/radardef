import unittest
from pathlib import Path

from radardef.collections import FormatCollection
from radardef.types import SourceFormat
from tests.unit import mocks


class FormatCollectionTest(unittest.TestCase):
    def test_add_validator(self):

        # Eiscat validator
        validator_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: True)

        # create format validator
        format_collection = FormatCollection([])
        print(f"list: {format_collection.list_formats()}")
        # No validator should be available
        self.assertNotIn(SourceFormat.MATBZ2, format_collection.list_formats())

        # register validator
        format_collection.add_validator(validator_mock)

        # Validator should be available
        self.assertIn(SourceFormat.MATBZ2, format_collection.list_formats())

    def test_simple_validator_mapping(self):

        validator_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: True)

        format_collection = FormatCollection([validator_mock])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.MATBZ2)

    def test_multiple_validators(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: True)

        format_collection = FormatCollection([validator_eiscat_mock, validator_mui_mock])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.MUI)

    def test_no_matching_validator(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)
        format_collection = FormatCollection([validator_eiscat_mock, validator_mui_mock])

        self.assertEqual(format_collection.get_format(Path()), SourceFormat.UNKNOWN)

    def test_list_validators(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: False)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)

        format_collection = FormatCollection([validator_eiscat_mock, validator_mui_mock])

        list_formats = format_collection.list_formats()

        self.assertIn(SourceFormat.MUI, list_formats)
        self.assertIn(SourceFormat.MATBZ2, list_formats)

    def test_is_format(self):

        validator_eiscat_mock = mocks.validator_mock(SourceFormat.MATBZ2, lambda src: True)
        validator_mui_mock = mocks.validator_mock(SourceFormat.MUI, lambda src: False)

        format_collection = FormatCollection([validator_eiscat_mock, validator_mui_mock])

        self.assertFalse(format_collection.is_format(Path(), SourceFormat.MUI))
        self.assertTrue(format_collection.is_format(Path(), SourceFormat.MATBZ2))
