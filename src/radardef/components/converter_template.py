"""Template class for all converters to inherit from"""

from abc import abstractmethod
from pathlib import Path

from radardef.types import SourceFormat, TargetFormat


class Converter:
    """
    Converter template, should be inherited by all converters

    Args:
        source_format: The format the converter takes as input
        target_format: The format the converter converts to

    """

    @property
    def source_format(self) -> SourceFormat:
        """Source format of the data compatible with the converter"""
        return self.__source_format

    @property
    def target_format(self) -> TargetFormat:
        """Format the converter converts to"""

        return self.__target_format

    def __init__(self, source_format: SourceFormat, target_format: TargetFormat) -> None:
        self.__source_format = source_format
        self.__target_format = target_format

    def __str__(self) -> str:
        """Converter source to target specification string"""
        return f"converter from {self.__source_format} to {self.__target_format}"

    @abstractmethod
    def convert(self, src: Path, dst: Path) -> list[Path]:
        """
        Abstract method, convert from source format to target format

        Args:
            src: Path to source directory
            dst: Path to destination directory

        Returns:
            output: List of the generated files directories
        """
        pass
