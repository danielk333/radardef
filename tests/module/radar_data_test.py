import os
import shutil
import unittest
from pathlib import Path

import numpy.testing

from radardef import RadarDef

from .download_test_data import download_test_data


class RadarDataTest(unittest.TestCase):

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

    def test_mu_h5_convert(self):

        radar_def = RadarDef()
        src_file = self.loc_test_data / "mu/MUI.191106.042339"
        output_dir = self.loc_tmp
        out = radar_def.convert(src_file, "h5", output_dir)

        for list_dir in out:
            for dir in list_dir:
                self.assertEqual(dir.parents[2], Path(output_dir))
                assert dir.is_dir()

                amount_of_files = len([x for x in dir.iterdir() if x.is_file()])

                self.assertGreater(amount_of_files, 1)

    def test_eiscat_drf_convert(self):

        radar_def = RadarDef()
        src_file = self.loc_test_data / "eiscat/leo_bpark_2.2_SW@32m_small"
        output_dir = self.loc_tmp
        out = radar_def.convert(src_file, "drf", output_dir)

        for list_dir in out:
            for dir in list_dir:
                self.assertEqual(dir.parents[0], Path(output_dir))
                assert dir.is_dir()

    def test_mu_h5_convert_multiple_files(self):

        radar_def = RadarDef()
        src_files = [self.loc_test_data / "mu/MUI.191106.011550", self.loc_test_data / "mu/MUI.191106.042339"]
        output_dir = self.loc_tmp
        out = radar_def.convert(src_files, "h5", output_dir)

        self.assertEqual(out[0][0].parents[2], Path(output_dir))
        self.assertEqual(out[1][0].parents[2], Path(output_dir))

        for list_dir in out:
            for dir in list_dir:
                self.assertEqual(dir.parents[2], Path(output_dir))
                assert dir.is_dir()

                amount_of_files = len([x for x in dir.iterdir() if x.is_file()])

                self.assertGreater(amount_of_files, 1)

    # TODO: A test that checks that it is possible to read data from one file to the next

    def test_mu_convert_and_load_directory(self):

        radar_def = RadarDef()
        src_file = self.loc_test_data / "mu/MUI.191106.042339"
        output_dir = self.loc_tmp
        out = radar_def.convert(src_file, "h5", output_dir)

        loader = radar_def.load_data(out[0][0])

        assert loader is not None

        metadata = loader.meta

        self.assertEqual(metadata.experiment.name, src_file.name)
        self.assertEqual(metadata.experiment.radar_frequency, 46.5)
        self.assertEqual(metadata.experiment.t_ipp_usec, 3120)
        self.assertEqual(metadata.experiment.t_samp_usec, 6)
        self.assertEqual(metadata.experiment.ipp_samps, 520)
        self.assertAlmostEqual(metadata.experiment.sample_rate, 166666.66666666666)
        numpy.testing.assert_array_equal(
            metadata.experiment.rx_channels,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        )
        self.assertIsNone(metadata.experiment.tx_channel)
        self.assertIsNone(metadata.experiment.tx_pulse_length)
        self.assertEqual(metadata.experiment.t_rx_start_usec, 486)
        self.assertEqual(metadata.experiment.t_rx_end_usec, 996)
        self.assertEqual(metadata.experiment.t_tx_start_usec, 0)
        self.assertEqual(metadata.experiment.t_tx_end_usec, 162)
        self.assertIsNone(metadata.experiment.t_cal_on_usec)
        self.assertIsNone(metadata.experiment.t_cal_off_usec)
        self.assertEqual(metadata.experiment.wavelength, 6.447149634408603)
        self.assertIsNotNone(metadata.bounds.ts_start_usec)
        self.assertIsNotNone(metadata.bounds.ts_end_usec)
        print(loader.channels)
        for chnl in loader.channels:
            data = loader.read(channel=chnl)
            self.assertIsNotNone(data)
            self.assertNotEqual(len(data), 0)
            self.assertEqual(len(data), loader.bounds(channel=chnl)[1])

    def test_mu_convert_and_load_h5_data(self):

        # convert data
        radar_def = RadarDef()
        src_file = self.loc_test_data / "mu/MUI.191106.042339"
        output_dir = self.loc_tmp
        out = radar_def.convert(src_file, "h5", output_dir)

        files = [f for f in out[0][0].iterdir() if f.is_file()]

        for f in files:
            loader = radar_def.load_data(f, "h5")

            assert loader is not None

            metadata = loader.meta
            print(metadata)

            self.assertEqual(metadata.experiment.name, src_file.name)
            self.assertEqual(metadata.experiment.radar_frequency, 46.5)
            self.assertEqual(metadata.experiment.t_ipp_usec, 3120)
            self.assertEqual(metadata.experiment.t_samp_usec, 6)
            self.assertEqual(metadata.experiment.ipp_samps, 520)
            self.assertAlmostEqual(metadata.experiment.sample_rate, 166666.66666666666)
            numpy.testing.assert_array_equal(
                metadata.experiment.rx_channels,
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
            )
            self.assertIsNone(metadata.experiment.tx_channel)
            self.assertIsNone(metadata.experiment.tx_pulse_length)
            self.assertEqual(metadata.experiment.t_rx_start_usec, 486)
            self.assertEqual(metadata.experiment.t_rx_end_usec, 996)
            self.assertEqual(metadata.experiment.t_tx_start_usec, 0)
            self.assertEqual(metadata.experiment.t_tx_end_usec, 156)
            self.assertIsNone(metadata.experiment.t_cal_on_usec)
            self.assertIsNone(metadata.experiment.t_cal_off_usec)
            self.assertEqual(metadata.experiment.wavelength, 6.447149634408603)
            self.assertIsNotNone(metadata.bounds.ts_start_usec)
            self.assertIsNotNone(metadata.bounds.ts_end_usec)
            self.assertIsNotNone(loader.read(channel=1))
            data = loader.read(channel=2)
            self.assertNotEqual(len(data), 0)
            self.assertEqual(len(data), loader.bounds(channel=2)[1])

    def test_eiscat_convert_and_load_drf_data(self):

        radar_def = RadarDef()
        src_file = self.loc_test_data / "eiscat/leo_bpark_2.2_SW@32m_small"
        output_dir = self.loc_tmp
        out = radar_def.convert(src_file, "drf", output_dir)

        loader = radar_def.load_data(out[0][0], "drf")

        metadata = loader.meta

        self.assertEqual(metadata.experiment.name, "leo_bpark")
        self.assertEqual(metadata.experiment.radar_frequency, 500.5)
        self.assertEqual(metadata.experiment.t_ipp_usec, 20000)
        self.assertEqual(metadata.experiment.t_samp_usec, 1)
        self.assertEqual(metadata.experiment.ipp_samps, 20000)
        self.assertEqual(metadata.experiment.sample_rate, 1000000.0)
        self.assertEqual(metadata.experiment.rx_channels, ["32m"])
        self.assertEqual(metadata.experiment.tx_channel, "32m")
        self.assertEqual(metadata.experiment.tx_pulse_length, 1921.0)
        self.assertEqual(metadata.experiment.t_rx_start_usec, 0.0)
        self.assertEqual(metadata.experiment.t_rx_end_usec, 20000.0)
        self.assertEqual(metadata.experiment.t_tx_start_usec, 82.0)
        self.assertEqual(metadata.experiment.t_tx_end_usec, 2003.0)
        self.assertEqual(metadata.experiment.t_cal_on_usec, 19900.0)
        self.assertEqual(metadata.experiment.t_cal_off_usec, 19997.0)

        self.assertEqual(metadata.bounds.ts_start_usec, 1637668800.001245)
        self.assertEqual(metadata.bounds.ts_end_usec, 1637669017.601226)

        start, end = loader.bounds("32m")
        self.assertIsNotNone(loader.read(channel="32m", start_sample=start, vector_length=10000))
