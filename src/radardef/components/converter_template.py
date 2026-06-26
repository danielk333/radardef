"""Template class for all converters to inherit from"""

import itertools
import logging
from abc import abstractmethod
from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.tools.mpi_tools import CommBar, get_mpi
from radardef.types import SourceFormat, TargetFormat


class Converter:
    """
    Converter template, should be inherited by all converters

    Args:
        source_validator: Validator connected to the source format of the converter.
        target_format: The format the converter converts to.

    """

    logger = logging.getLogger(__name__)

    @property
    def source_format(self) -> SourceFormat:
        """Source format of the data compatible with the converter"""
        return self.validator.format

    @property
    def target_format(self) -> TargetFormat:
        """Format the converter converts to"""

        return self.__target_format

    @property
    def validator(self) -> Validator:
        """Source format validator"""
        return self.__validator

    def __init__(self, source_validator: Validator, target_format: TargetFormat) -> None:
        self.__validator = source_validator
        self.__target_format = target_format

    def __str__(self) -> str:
        """Converter source to target specification string"""
        return f"converter from {self.source_format} to {self.target_format}"

    def convert(self, src: Path, dst: Path, progress: bool | CommBar = False) -> list[Path]:
        """
        Convert given file or directory.

        Args:
            src: Path to source directory
            dst: Path to destination directory

        Returns:
            output: List of the generated files directories
        """
        comm = get_mpi()

        conv_files = self._get_all_files(src)
        if len(conv_files) == 0:
            self.logger.warning(f"No convertable files at: {src}")

        rank_conv_files = conv_files[comm.rank : len(conv_files) : comm.size]
        output = []

        if progress:
            pbar = CommBar(
                tot=len(conv_files),
                desc=f"{str(self.source_format).upper()} to {str(self.target_format).upper()}",
                parent_progress=progress if isinstance(progress, CommBar) else None,
                transient=isinstance(progress, CommBar),
            )
        else:
            pbar = None

        for file in rank_conv_files:
            output += self.convert_single_object(file, dst)
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()
        else:
            comm.barrier()

        if comm.size > 1:
            all_outputs = comm.gather(output, root=0)

            if comm.rank == 0:
                output = list(itertools.chain.from_iterable(all_outputs))  # type: ignore[arg-type]
            else:
                output = None  # type: ignore[assignment]

            output = comm.bcast(output, root=0)
            comm.barrier()

        # Remove duplicates
        output = list(set(output))
        return output

    @abstractmethod
    def convert_single_object(self, src: Path, dst: Path) -> list[Path]:
        """
        Abstract method, convert from source format to target format

        Args:
            src: Path to file to convert
            dst: Path to destination directory

        Returns:
            output: List of the generated files directories
        """
        pass

    def _get_all_files(self, path: Path) -> list[Path]:

        if path.is_dir() and not self.validator.validate(path):
            return [file for file in path.rglob(".") if self.validator.validate(file)]
        elif self.validator.validate(path):
            return [path]
        return []
