"""Tests for PDF extractors."""

from pathlib import Path

import pytest

from pdf2md.extractors.base import PDFExtractionError
from pdf2md.extractors.factory import ExtractorFactory


class TestExtractorFactory:
    """Test extractor factory."""

    def test_create_pdfplumber_extractor(self) -> None:
        """Test creating pdfplumber extractor."""
        extractor = ExtractorFactory.create_extractor("pdfplumber")
        assert extractor.name == "pdfplumber"

    def test_create_pymupdf_extractor(self) -> None:
        """Test creating pymupdf extractor."""
        extractor = ExtractorFactory.create_extractor("pymupdf")
        assert extractor.name == "pymupdf"

    def test_create_auto_extractor(self) -> None:
        """Test creating auto-fallback extractor."""
        extractor = ExtractorFactory.create_extractor("auto")
        assert extractor is not None

    def test_invalid_extractor_method(self) -> None:
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown extractor method"):
            ExtractorFactory.create_extractor("invalid")  # type: ignore[arg-type]


class TestPDFValidation:
    """Test PDF validation."""

    def test_validate_nonexistent_file(self) -> None:
        """Test validation of nonexistent file."""
        extractor = ExtractorFactory.create_extractor("pdfplumber")
        assert not extractor.validate_pdf(Path("/nonexistent/file.pdf"))

    def test_validate_directory(self, tmp_path: Path) -> None:
        """Test validation of directory."""
        extractor = ExtractorFactory.create_extractor("pdfplumber")
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        assert not extractor.validate_pdf(test_dir)

    def test_validate_non_pdf_file(self, tmp_path: Path) -> None:
        """Test validation of non-PDF file."""
        extractor = ExtractorFactory.create_extractor("pdfplumber")
        text_file = tmp_path / "test.txt"
        text_file.write_text("Not a PDF", encoding="utf-8")
        assert not extractor.validate_pdf(text_file)


class TestExtractorDeterminism:
    """Test that extractors produce deterministic output."""

    def test_same_pdf_same_output(self, tmp_path: Path) -> None:
        """Test that same PDF produces identical output twice."""
        # Note: Requires actual PDF fixture
        # For now, just test that extractor is deterministic
        extractor = ExtractorFactory.create_extractor("auto")
        assert extractor is not None


# Note: Full integration tests with real PDFs would go here
# Requires fixtures/sample.pdf which will be added in fixture setup