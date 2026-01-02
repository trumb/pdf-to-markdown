"""Abstract base class for PDF extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PDFMetadata:
    """PDF document metadata."""

    title: str | None
    author: str | None
    subject: str | None
    creator: str | None
    producer: str | None
    creation_date: datetime | None
    modification_date: datetime | None
    page_count: int
    encrypted: bool
    file_size_bytes: int


@dataclass
class PDFPage:
    """Extracted content from a single PDF page."""

    page_number: int
    text: str
    images: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    width: float
    height: float


@dataclass
class PDFExtraction:
    """Complete PDF extraction result."""

    metadata: PDFMetadata
    pages: list[PDFPage]
    extraction_method: str
    extraction_time_seconds: float
    warnings: list[str]


class PDFExtractor(ABC):
    """Abstract base class for PDF extraction engines."""

    @abstractmethod
    def extract(self, pdf_path: Path) -> PDFExtraction:
        """
        Extract text, images, and tables from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFExtraction with all content and metadata

        Raises:
            PDFExtractionError: If extraction fails
        """
        pass

    @abstractmethod
    def get_metadata(self, pdf_path: Path) -> PDFMetadata:
        """
        Extract only metadata from PDF without full content extraction.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFMetadata with document information

        Raises:
            PDFExtractionError: If metadata extraction fails
        """
        pass

    @abstractmethod
    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        Validate that file is a readable PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if valid PDF, False otherwise
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return extractor name (e.g., 'pdfplumber', 'pymupdf')."""
        pass


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""

    pass
