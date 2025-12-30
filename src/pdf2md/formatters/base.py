"""Abstract base class for output formatters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pdf2md.extractors.base import PDFExtraction


@dataclass
class FormattedOutput:
    """Formatted conversion output."""

    content: str
    format: str
    encoding: str = "utf-8"


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, extraction: PDFExtraction, **options: any) -> FormattedOutput:  # type: ignore[misc]
        """
        Format PDF extraction into output format.

        Args:
            extraction: PDF extraction result
            **options: Format-specific options

        Returns:
            FormattedOutput with content and metadata

        Raises:
            FormattingError: If formatting fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return formatter name (e.g., 'markdown', 'json')."""
        pass


class FormattingError(Exception):
    """Raised when formatting fails."""

    pass