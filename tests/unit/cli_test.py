import argparse
import unittest
from pathlib import Path

import pytest
from tests.unit import mocks

import radardef.cli.commands_cli as commands_cli
import radardef.cli.convert_cli as convert_cli
import radardef.cli.format_cli as format_cli
from radardef.types import SourceFormat, TargetFormat


class CliTest(unittest.TestCase):

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        return super().setUp()

    @pytest.fixture(autouse=True)
    def _pass_fixtures(self, capsys):
        self.capsys = capsys

    def test_convert_cli_list(self):

        parser = convert_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["-l", "."])

        convert_cli.main(args, None)

        mui_to_h5 = f"{SourceFormat.MUI}:\n├Target format> {TargetFormat.H5}\n"
        matbz_to_drf = f"{SourceFormat.EISCAT_MATBZ}:\n├Target format> {TargetFormat.DRF}\n"

        out, _ = self.capsys.readouterr()
        self.assertIn(mui_to_h5, out)
        self.assertIn(matbz_to_drf, out)

    def test_convert_cli_convert_bad_target(self):

        parser = convert_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["some/imaginary/path", "txt"])

        convert_cli.main(args, None)

        expected_output = "No conversion to target format is present, use -l to list available formats\n"
        out, _ = self.capsys.readouterr()
        self.assertEqual(expected_output, out)

    def test_convert_cli_convert_bad_path(self):

        parser = convert_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["some/imaginary/path", "drf"])
        with self.assertLogs("radardef.radar_def", level="ERROR") as logger:
            convert_cli.main(args, None)
            self.assertEqual(
                logger.output, ["ERROR:radardef.radar_def:Input path/paths is not a valid file/directory"]
            )
            expected_output = "Path/paths was not valid\n"
            out, _ = self.capsys.readouterr()
            self.assertEqual(expected_output, out)

    def test_convert_cli_convert_no_path(self):

        parser = convert_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["h5"])

        convert_cli.main(args, None)

        expected_output = "No input paths!\n"
        out, _ = self.capsys.readouterr()
        self.assertEqual(expected_output, out)

    def test_format_cli_list(self):

        parser = format_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["-l"])

        format_cli.main(args, None)

        expected_output = f">{SourceFormat.MUI}\n>{SourceFormat.EISCAT_MATBZ}\n\n"
        out, err = self.capsys.readouterr()
        self.assertEqual(expected_output, out)

    def test_format_cli_format(self):

        parser = format_cli.parser_build(argparse.ArgumentParser())

        args = parser.parse_args(["tmp/fake_path/MUI.191106.011550"])

        format_cli.main(args, None)

        expected_output = f"Source format is: {SourceFormat.MUI}\n"
        out, err = self.capsys.readouterr()
        self.assertEqual(expected_output, out)
