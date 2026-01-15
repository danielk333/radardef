"""
Main entry for the CLI functionality
"""

import argparse
import logging
import sys
from collections.abc import Callable

try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:

    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()  # type: ignore[assignment]

from ..tools import profiling

logger = logging.getLogger(__name__)

COMMANDS: dict[str, dict] = dict()


def build_parser() -> argparse.ArgumentParser:
    """Build default CLI parser including arguments and subparsers."""

    parser = argparse.ArgumentParser(description="Radar data tool box")

    parser.add_argument("-p", "--profiler", action="store_true", help="Run profiler")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="count", default=0)

    subparsers = parser.add_subparsers(help="Available command line interfaces", dest="command")
    subparsers.required = True

    # Adds any item in the COMMAND dict as a subparser
    for name, dat in COMMANDS.items():
        parser_builder, command_help = dat["parser"]
        cmd_parser = subparsers.add_parser(name, help=command_help)
        parser_builder(cmd_parser)

    return parser


def add_command(
    name: str,
    function: Callable,
    parser_build: Callable[[argparse.ArgumentParser], argparse.ArgumentParser],
    command_help: str = "",
) -> None:
    """
    Adds a parser with related function to the global COMMAND dict.

    Args:
        name: Command name
        function: Main function of the callable argument
        parser_build: Parser builder, adds needed commands
        command_help: Command help text

    """

    global COMMANDS
    COMMANDS[name] = dict()
    COMMANDS[name]["function"] = function
    COMMANDS[name]["parser"] = (parser_build, command_help)


def main() -> None:
    """Create and execute CLI interface."""

    parser = build_parser()
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    if comm.size > 1:
        formatter = logging.Formatter(f"RANK{comm.rank} - %(asctime)s %(levelname)s %(name)s - %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)

    lib_logger = logging.getLogger("radardef")
    if args.verbose > 0:
        lib_logger.addHandler(handler)
        lib_logger.setLevel(logging.INFO)
    else:
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

    if args.verbose > 1:
        logger.info("Logging level set to debug")
        lib_logger.setLevel(logging.DEBUG)

    if args.profiler:
        profiling.profile()

    function = COMMANDS[args.command]["function"]
    logger.info(f"Executing command {args.command}")

    function(args, logger)

    if args.verbose > 0 and args.profiler:
        stats, total = profiling.get_profile()
        profiling.print_profile(stats, total=total)
        profiling.profile_stop()
