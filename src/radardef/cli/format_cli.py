"""
The CLI format functionality, abstracts the format functionality to a user friendly CLI interface
"""

import argparse
import logging

from radardef.collections import FormatCollection
from radardef.radar_stations import EiscatUHF, Mu

from .commands_cli import add_command


def main(args: argparse.Namespace, cli_logger: logging.Logger) -> None:
    """Converter CLI available to the user"""

    format_validator = FormatCollection([Mu(), EiscatUHF()])

    if args.list:
        print(format_validator.list_formats())
        if cli_logger:
            cli_logger.info("Listing complete, exiting...")
        return

    for path in args.paths:
        source_format = format_validator.get_format(path)
        print(f"Source format is: {source_format}")


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List available formats",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="Location of the file/files",
    )

    return parser


add_command(
    name="format",
    function=main,
    parser_build=parser_build,
    command_help="Returns the source format of the file",
)
