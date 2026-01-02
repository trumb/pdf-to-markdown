"""Unified PDF-to-Markdown conversion pipeline."""

from pathlib import Path
from typing import Any, Literal

from pdf2md.core.config import Settings
from pdf2md.extractors.base import PDFExtraction
from pdf2md.extractors.factory import ExtractorFactory
from pdf2md.formatters.base import FormattedOutput
from pdf2md.formatters.json_formatter import JSONFormatter
from pdf2md.formatters.markdown import MarkdownFormatter
from pdf2md.formatters.text_formatter import TextFormatter
from pdf2md.formatters.yaml_formatter import YAMLFormatter
from pdf2md.handlers.images import ImageHandler
from pdf2md.handlers.tables import TableHandler
from pdf2md.security.sandbox import PDFSandbox
from pdf2md.security.validator import PDFValidator
from pdf2md.tokens.claude_counter import ClaudeTokenCounter
from pdf2md.tokens.openai_counter import OpenAITokenCounter


class PDFConverter:
    """
    Unified PDF-to-Markdown conversion pipeline.

    This is the single source of truth for conversion logic,
    used by both CLI and API (future phases).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize converter with settings.

        Args:
            settings: Application settings (uses defaults if None)
        """
        self.settings = settings or Settings()

    def convert(
        self,
        pdf_path: Path,
        output_format: Literal["markdown", "json", "yaml", "text"] | None = None,
        **options: Any,
    ) -> str:
        """
        Convert PDF to specified format.

        Args:
            pdf_path: Path to PDF file
            output_format: Output format (overrides settings)
            **options: Additional conversion options

        Returns:
            Formatted output string

        Raises:
            ValueError: If PDF validation fails
            Exception: If conversion fails
        """
        # Convert to Path if string
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        # Validate PDF
        is_valid, error_msg = PDFValidator.validate_file(pdf_path)
        if not is_valid:
            raise ValueError(f"PDF validation failed: {error_msg}")

        # Compute file hash
        file_hash = PDFValidator.compute_file_hash(pdf_path)

        # Extract PDF (in sandbox if enabled)
        if self.settings.sandbox_enabled:
            extraction = self._extract_sandboxed(pdf_path)
        else:
            extraction = self._extract_direct(pdf_path)

        # Format output
        format_type = output_format or self.settings.output_format
        formatted = self._format_output(
            extraction=extraction,
            format_type=format_type,
            source_file=pdf_path.name,
            source_hash=f"sha256:{file_hash}",
            **options,
        )

        return formatted.content

    def convert_to_file(
        self,
        pdf_path: Path,
        output_path: Path,
        output_format: Literal["markdown", "json", "yaml", "text"] | None = None,
        **options: Any,
    ) -> None:
        """
        Convert PDF and write to file.

        Args:
            pdf_path: Path to PDF file
            output_path: Path to output file
            output_format: Output format (overrides settings)
            **options: Additional conversion options
        """
        content = self.convert(pdf_path, output_format, **options)

        # Write to file
        output_path.write_text(content, encoding="utf-8")

    def get_metadata(self, pdf_path: Path) -> dict[str, Any]:
        """
        Get PDF metadata without full conversion.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF metadata

        Raises:
            ValueError: If PDF validation fails
        """
        # Convert to Path if string
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        # Validate PDF
        is_valid, error_msg = PDFValidator.validate_file(pdf_path)
        if not is_valid:
            raise ValueError(f"PDF validation failed: {error_msg}")

        # Get file info
        file_info = PDFValidator.get_file_info(pdf_path)

        # Extract metadata using extractor
        extractor = ExtractorFactory.create_extractor(self.settings.extractor)
        metadata = extractor.get_metadata(pdf_path)

        return {
            "file": file_info,
            "pdf": {
                "title": metadata.title,
                "author": metadata.author,
                "subject": metadata.subject,
                "creator": metadata.creator,
                "producer": metadata.producer,
                "creation_date": (
                    metadata.creation_date.isoformat() if metadata.creation_date else None
                ),
                "modification_date": (
                    metadata.modification_date.isoformat()
                    if metadata.modification_date
                    else None
                ),
                "page_count": metadata.page_count,
                "encrypted": metadata.encrypted,
            },
        }

    def _extract_sandboxed(self, pdf_path: Path) -> PDFExtraction:
        """Extract PDF in security sandbox."""
        sandbox = PDFSandbox(
            memory_limit_mb=self.settings.sandbox_memory_limit_mb,
            timeout_seconds=self.settings.sandbox_timeout,
        )

        return sandbox.extract_pdf(pdf_path, self.settings.extractor)

    def _extract_direct(self, pdf_path: Path) -> PDFExtraction:
        """Extract PDF without sandbox (not recommended for production)."""
        extractor = ExtractorFactory.create_extractor(self.settings.extractor)
        return extractor.extract(pdf_path)

    def _format_output(
        self,
        extraction: PDFExtraction,
        format_type: str,
        source_file: str,
        source_hash: str,
        **options: Any,
    ) -> FormattedOutput:
        """Format extraction result."""
        # Calculate token counts if requested
        tokens: dict[str, int] = {}
        if self.settings.include_tokens:
            tokens = self._count_tokens(extraction)

        # Select formatter
        if format_type == "markdown":
            formatter = MarkdownFormatter()
        elif format_type == "json":
            formatter = JSONFormatter()
        elif format_type == "yaml":
            formatter = YAMLFormatter()
        elif format_type == "text":
            formatter = TextFormatter()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Format output
        return formatter.format(
            extraction,
            include_frontmatter=self.settings.include_frontmatter,
            include_tokens=self.settings.include_tokens,
            tokens=tokens,
            source_file=source_file,
            source_hash=source_hash,
            **options,
        )

    def _count_tokens(self, extraction: PDFExtraction) -> dict[str, int]:
        """Count tokens in extracted text."""
        # Combine all page text
        full_text = "\n\n".join(page.text for page in extraction.pages)

        tokens: dict[str, int] = {}

        # Count using enabled encodings
        for encoding in self.settings.token_encodings:
            try:
                if encoding == "cl100k_base":
                    counter = OpenAITokenCounter("cl100k_base")
                    tokens["openai_cl100k"] = counter.count_tokens(full_text)
                elif encoding == "p50k_base":
                    counter = OpenAITokenCounter("p50k_base")
                    tokens["openai_p50k"] = counter.count_tokens(full_text)
                elif encoding == "claude":
                    counter = ClaudeTokenCounter()
                    tokens["claude_estimate"] = counter.count_tokens(full_text)
            except Exception:
                # Continue if a counter fails
                pass

        return tokens
