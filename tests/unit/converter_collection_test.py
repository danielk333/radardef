import unittest
from pathlib import Path

from tests.unit import mocks

from radardef.collections import ConverterCollection
from radardef.types import SourceFormat, TargetFormat


class ConverterCollectionTest(unittest.TestCase):

    def test_converters_available(self):

        converter_mui_h5_mock = mocks.converter_mock(
            SourceFormat.MUI, TargetFormat.H5, lambda src, dst: [Path("/converted_file/1")]
        )
        converter_eiscat_drf_mock = mocks.converter_mock(
            SourceFormat.EISCAT_MATBZ, TargetFormat.DRF, lambda src, dst: [Path("/converted_file/2")]
        )

        converter_mocks = [converter_mui_h5_mock, converter_eiscat_drf_mock]

        radar_mock = mocks.radar_mock(converters=converter_mocks)

        converter_collection = ConverterCollection([radar_mock])

        # Get available converters
        collection = converter_collection.list_collection()

        for converter in converter_mocks:
            self.assertIn(
                f"{converter.source_format}:\n├Target format> {converter.target_format}",
                collection,
            )

    def test_simple_conversion_mapping(self):

        converter_mui_h5_mock = mocks.converter_mock(
            SourceFormat.MUI, TargetFormat.H5, lambda src, dst: [Path("/converted_file/1")]
        )
        converter_eiscat_drf_mock = mocks.converter_mock(
            SourceFormat.EISCAT_MATBZ, TargetFormat.DRF, lambda src, dst: [Path("/converted_file/2")]
        )

        converter_mocks = [converter_mui_h5_mock, converter_eiscat_drf_mock]

        radar_mock = mocks.radar_mock(converters=converter_mocks)

        converter_collection = ConverterCollection([radar_mock])

        output = converter_collection.convert(Path(""), SourceFormat.MUI, TargetFormat.H5, Path(""))

        self.assertEqual(output[0], Path("/converted_file/1"))

    def test_multiple_conversion_mapping(self):

        converter_mui_h5_mock = mocks.converter_mock(
            SourceFormat.MUI, TargetFormat.H5, lambda src, dst: [Path("/converted_file/1")]
        )
        converter_eiscat_h5_mock = mocks.converter_mock(
            SourceFormat.EISCAT_MATBZ, TargetFormat.H5, lambda src, dst: [Path("/converted_file/2")]
        )

        converter_mocks = [converter_mui_h5_mock, converter_eiscat_h5_mock]

        radar_mock = mocks.radar_mock(converters=converter_mocks)

        converter_collection = ConverterCollection([radar_mock])

        output = converter_collection.convert(
            [Path("some_mui_file"), Path("some_eiscat_file")],
            [SourceFormat.MUI, SourceFormat.EISCAT_MATBZ],
            TargetFormat.H5,
            Path(""),
        )

        self.assertEqual(output[0][0], Path("/converted_file/1"))
        self.assertEqual(output[1][0], Path("/converted_file/2"))

    def test_get_converter(self):

        converter_mui_h5_mock = mocks.converter_mock(
            SourceFormat.MUI, TargetFormat.H5, lambda src, dst: [Path("/converted_file/1")]
        )
        converter_eiscat_drf_mock = mocks.converter_mock(
            SourceFormat.EISCAT_MATBZ, TargetFormat.DRF, lambda src, dst: [Path("/converted_file/2")]
        )

        converter_mocks = [converter_mui_h5_mock, converter_eiscat_drf_mock]

        radar_mock = mocks.radar_mock(converters=converter_mocks)

        converter_collection = ConverterCollection([radar_mock])

        for converter in converter_mocks:
            self.assertEqual(
                converter_collection.get_converter(converter.source_format, converter.target_format),
                converter,
            )
