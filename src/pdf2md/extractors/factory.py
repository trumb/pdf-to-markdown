"""Factory for creating PDF extractors with automatic fallback."""

from pathlib import Path
from typing import Literal

from pdf2md.extractors.base import PDFExtractor, PDFExtractionError
from pdf2md.extractors.pdfplumber_extractor import PDFPlumberExtractor
from pdf2md.extractors.pymupdf_extractor import PyMuPDFExtractor


class ExtractorFactory:
    """Factory for creating PDF extractors with fallback support."""

    @staticmethod
    def create_extractor(
        method: Literal["pdfplumber", "pymupdf", "auto"] = "auto",
    ) -> PDFExtractor:
        """
        Create PDF extractor instance.

        Args:
            method: Extraction method
                - "pdfplumber": Use pdfplumber (accuracy-focused)
                - "pymupdf": Use PyMuPDF (fallback)
                - "auto": Try pdfplumber first, fallback to pymupdf

        Returns:
            PDFExtractor instance

        Raises:
            ValueError: If method is invalid
        """
        if method == "pdfplumber":
            return PDFPlumberExtractor()
        elif method == "pymupdf":
            return PyMuPDFExtractor()
        elif method == "auto":
            # Return auto-fallback extractor
            return AutoFallbackExtractor()
        else:
            raise ValueError(f"Unknown extractor method: {method}")


class AutoFallbackExtractor(PDFExtractor):
    """
    Extractor with automatic fallback from pdfplumber to pymupdf.

    Tries pdfplumber first (accuracy-focused). If extraction fails,
    automatically falls back to pymupdf.
    """

    def __init__(self) -> None:
        """Initialize with both extractors."""
        self.primary = PDFPlumberExtractor()
        self.fallback = PyMuPDFExtractor()
        self._used_extractor: PDFExtractor | None = None

    @property
    def name(self) -> str:
        """Return name of actually used extractor."""
        if self._used_extractor:
            return self._used_extractor.name
        return "auto"

    def validate_pdf(self, pdf_path: Path) -> bool:
        """Validate PDF using primary extractor."""
        # Try primary first
        if self.primary.validate_pdf(pdf_path):
            return True

        # Fallback to secondary
        return self.fallback.validate_pdf(pdf_path)

    def get_metadata(self, pdf_path: Path) -> any:  # type: ignore[misc]
        """Extract metadata with automatic fallback."""
        # Try primary extractor
        try:
            self._used_extractor = self.primary
            return self.primary.get_metadata(pdf_path)
        except PDFExtractionError:
            # Fallback to secondary extractor
            try:
                self._used_extractor = self.fallback
                return self.fallback.get_metadata(pdf_path)
            except PDFExtractionError as e:
                raise PDFExtractionError(
                    f"Both extractors failed to get metadata: {e}"
                ) from e

    def extract(self, pdf_path: Path) -> any:  # type: ignore[misc]
        """Extract PDF with automatic fallback."""
        # Try primary extractor (pdfplumber)
        try:
            self._used_extractor = self.primary
            result = self.primary.extract(pdf_path)
            return result
        except PDFExtractionError:
            # Fallback to secondary extractor (pymupdf)
            try:
                self._used_extractor = self.fallback
                result = self.fallback.extract(pdf_path)
                # Add warning that fallback was used
                result.warnings.insert(
                    0,
                    f"Primary extractor ({self.primary.name}) failed, "
                    f"using fallback ({self.fallback.name})",
                )
                return result
            except PDFExtractionError as e:
                raise PDFExtractionError(
                    f"Both extractors failed: primary={self.primary.name}, "
                    f"fallback={self.fallback.name}. Error: {e}"
                ) from e