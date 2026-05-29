"""
Format validator gathers all given radars and extracts their source validators, the collection can then solve
what format any given file is, given that the format is the source format of atleast one radar.
"""

import logging
from pathlib import Path

from radardef.components.validator_template import Validator
from radardef.types import SourceFormat


class FormatCollection:
    """
    Collection of all available validators from the available radar objects,
    provides a way to gather and provide source validators for many different formats in one place and make
    it possible to solve the source format of a given file.

    Args:
        validators: List of validators that the collection will be based upon.

    """

    __logger = logging.getLogger(__name__)

    def __init__(self, validators: list[Validator]) -> None:

        self.__formats: dict[SourceFormat, Validator] = dict()

        for validator in validators:
            self.__logger.debug(f"registering  {validator}")
            self.add_validator(validator)

    def add_validator(self, validator: Validator) -> None:
        """Register a validator related to a source format to collection."""
        self.__formats[validator.format] = validator

    def get_format(self, path: Path) -> SourceFormat:
        """Returns the source format of the file."""

        for source_format, validator in self.__formats.items():
            if validator.validate(path):
                return source_format
        return SourceFormat.UNKNOWN

    def is_format(self, path: Path, source_format: SourceFormat) -> bool:
        """Validates that the file is of the expected format"""
        try:
            return self.__formats[source_format].validate(path)
        except KeyError:
            self.__logger.debug(f"No validator available for {source_format} format")
            return False

    def list_formats(self) -> str:
        """Lists formats with a validator as a string"""

        st = ""
        if self.__formats is not None:
            for source_format, _ in self.__formats.items():
                st += f">{source_format}\n"
        return st
