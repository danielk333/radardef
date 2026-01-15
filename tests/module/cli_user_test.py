import argparse
import os
import shutil
import unittest
from pathlib import Path

import radardef.cli.convert_cli as convert_cli

from .download_test_data import download_test_data


class CliUserTest(unittest.TestCase):

    def __del__(self):
        # clear any generated files
        if self.loc_tmp.name == "tmp":
            try:
                shutil.rmtree(self.loc_tmp)
            except FileNotFoundError:
                pass

    def tearDown(self):
        # clear any generated files
        if self.loc_tmp.name == "tmp":
            try:
                shutil.rmtree(self.loc_tmp)
            except FileNotFoundError:
                pass
        return super().tearDown()

    def __init__(self, methodName="runTest"):
        self.loc_test_data = Path.cwd() / os.path.dirname(__file__)
        self.loc_test_data = self.loc_test_data / "test_data"
        self.loc_tmp = Path.cwd() / os.path.dirname(__file__) / "tmp"
        download_test_data(self.loc_test_data)
        super().__init__(methodName)

    def test_convert_with_cli(self):

        src_file = self.loc_test_data / "eiscat/leo_bpark_2.2_SW@32m_small"

        parser = convert_cli.parser_build(argparse.ArgumentParser())
        args = parser.parse_args(["convert", str(src_file), "drf", "-o", str(self.loc_tmp)])
        convert_cli.main(args, None)

        assert len([x for x in self.loc_tmp.iterdir()]) != 0
