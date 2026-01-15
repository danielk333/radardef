"""
The CLI download functionality, abstracts the download functionality to a user friendly CLI interface
"""

import argparse
import logging

from radardef.download.eiscat.download import download

from .commands_cli import add_command


def main(args: argparse.Namespace, cli_logger: logging.Logger) -> None:
    """Download CLI available to the user"""
    download(
        args.day,
        args.mode,
        args.instrument,
        args.dst,
        logger=cli_logger,
        progress=args.progress,
        wget=args.wget,
    )


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument("day", help='Experiment day, e.g. "20210412"')
    parser.add_argument("mode", help='Experiment mode, e.g. "leo_bpark_2.1u_NO"')
    parser.add_argument("instrument", help='Experiment instrument, e.g. "uhf|32m|42m"')
    parser.add_argument("dst", default=".", help="destination folder")
    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="show progressbar for download",
    )
    parser.add_argument(
        "--wget",
        action="store_true",
        help="use wget instead of requests for download",
    )

    return parser


add_command(
    name="download",
    function=main,
    parser_build=parser_build,
    command_help="Download data files from the given radar (Only Eiscat is supported for now)",
)
