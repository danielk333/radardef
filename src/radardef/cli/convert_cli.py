"""
The CLI convert functionality, abstracts the convert functionality to a user friendly CLI interface
"""

import argparse
import logging
import os
from pathlib import Path

from radardef import RadarDef
from radardef.types import TargetFormat

from .commands_cli import add_command


def main(args: argparse.Namespace, cli_logger: logging.Logger) -> None:
    """Converter CLI available to the user"""
    radar_def = RadarDef()

    if args.list:
        print(radar_def.converter_collection.list_collection())
        if cli_logger:
            cli_logger.info("Listing complete, exiting...")
        return

    # If no files available, exit
    if len(args.files) == 0:
        print("No input paths!")
        return

    target_format = args.format.lower()

    # Extract wanted target format
    if target_format not in iter(TargetFormat):
        target_format = TargetFormat.UNKNOWN
        print("No conversion to target format is present, use -l to list available formats")
        return

    converted_data = radar_def.convert(args.files, target_format, args.output)

    if converted_data is None:
        print("Path/paths was not valid")
        return

    if cli_logger:
        cli_logger.info("Conversion complete")


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List avalible convertable formats and target format",
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=[],
        help="Input the locations of the files (or folders) to be converted",
    )
    parser.add_argument(
        "format",
        default=None,
        help="Target format to convert to",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(Path(os.getcwd()).resolve()),
        help="The output location of the converted files",
    )
    parser.add_argument(
        "-s",
        "--sourceformat",
        default=None,
        help="optional, format of source data, if specified all other formats will be ignored",
    )

    return parser


add_command(
    name="convert",
    function=main,
    parser_build=parser_build,
    command_help="Convert the target files to a supported format",
)
