"""Tests for output formatters."""

from datetime import datetime

from pdf2md.extractors.base import PDFExtraction, PDFMetadata, PDFPage
from pdf2md.formatters.json_formatter import JSONFormatter
from pdf2md.formatters.markdown import MarkdownFormatter
from pdf2md.formatters.text_formatter import TextFormatter
from pdf2md.formatters.yaml_formatter import YAMLFormatter


class TestMarkdownFormatter:
    """Test Markdown formatter."""

    def test_format_with_frontmatter(self) -> None:
        """Test Markdown formatting with frontmatter."""
        formatter = MarkdownFormatter()

        # Create sample extraction
        extraction = self._create_sample_extraction()

        # Format
        result = formatter.format(
            extraction,
            include_frontmatter=True,
            source_file="test.pdf",
            source_hash="sha256:abc123",
        )

        assert result.format == "markdown"
        assert "---" in result.content
        assert "test.pdf" in result.content
        assert "Test Page 1" in result.content

    def test_format_without_frontmatter(self) -> None:
        """Test Markdown formatting without frontmatter."""
        formatter = MarkdownFormatter()
        extraction = self._create_sample_extraction()

        result = formatter.format(extraction, include_frontmatter=False)

        assert "---" not in result.content
        assert "Test Page 1" in result.content

    def _create_sample_extraction(self) -> PDFExtraction:
        """Create sample extraction for testing."""
        metadata = PDFMetadata(
            title="Test PDF",
            author="Test Author",
            subject=None,
            creator=None,
            producer=None,
            creation_date=None,
            modification_date=None,
            page_count=2,
            encrypted=False,
            file_size_bytes=1024,
        )

        pages = [
            PDFPage(
                page_number=1,
                text="Test Page 1",
                images=[],
                tables=[],
                width=612.0,
                height=792.0,
            ),
            PDFPage(
                page_number=2,
                text="Test Page 2",
                images=[],
                tables=[],
                width=612.0,
                height=792.0,
            ),
        ]

        return PDFExtraction(
            metadata=metadata,
            pages=pages,
            extraction_method="pdfplumber",
            extraction_time_seconds=1.5,
            warnings=[],
        )


class TestJSONFormatter:
    """Test JSON formatter."""

    def test_format_as_json(self) -> None:
        """Test JSON formatting."""
        formatter = JSONFormatter()
        extraction = TestMarkdownFormatter()._create_sample_extraction()

        result = formatter.format(extraction, source_file="test.pdf")

        assert result.format == "json"
        assert '"pages":' in result.content
        assert '"metadata":' in result.content


class TestYAMLFormatter:
    """Test YAML formatter."""

    def test_format_as_yaml(self) -> None:
        """Test YAML formatting."""
        formatter = YAMLFormatter()
        extraction = TestMarkdownFormatter()._create_sample_extraction()

        result = formatter.format(extraction, source_file="test.pdf")

        assert result.format == "yaml"
        assert "pages:" in result.content
        assert "metadata:" in result.content


class TestTextFormatter:
    """Test plain text formatter."""

    def test_format_as_text(self) -> None:
        """Test text formatting."""
        formatter = TextFormatter()
        extraction = TestMarkdownFormatter()._create_sample_extraction()

        result = formatter.format(extraction)

        assert result.format == "text"
        assert "Test Page 1" in result.content
        assert "Test Page 2" in result.content
        # Should not have frontmatter
        assert "---" not in result.content