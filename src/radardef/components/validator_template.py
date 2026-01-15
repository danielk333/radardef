"""Template class for all validators to inherit from"""

from abc import abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class Validator(Generic[T]):
    """
    Validator template, should be inherited by all validators

    Args:
        format: Format that the validator should be validator for
    """

    @property
    def format(self) -> T:
        """Format connected to the validator"""
        return self.__format

    def __init__(self, format: T) -> None:
        self.__format = format

    def __str__(self) -> str:
        """validator format string"""
        return f"{self.__format} validator"

    @abstractmethod
    def validate(self, src: str | Path) -> bool:
        """
        Abstract method, validate the format of given file

        Args:
            src: Path to file/directory
        """
        pass
