"""Plain text formatter."""

from typing import Any

from pdf2md.extractors.base import PDFExtraction
from pdf2md.formatters.base import FormattedOutput, FormattingError, OutputFormatter


class TextFormatter(OutputFormatter):
    """Format PDF extraction as plain text (no formatting)."""

    @property
    def name(self) -> str:
        """Return formatter name."""
        return "text"

    def format(self, extraction: PDFExtraction, **options: Any) -> FormattedOutput:
        """
        Format extraction as plain text.

        Options:
            page_separator: String to separate pages (default: double newline)

        Returns:
            FormattedOutput with plain text content
        """
        page_separator = options.get("page_separator", "\n\n")

        try:
            # Extract text from all pages
            page_texts: list[str] = []

            for page in extraction.pages:
                if page.text.strip():
                    page_texts.append(page.text.strip())

            # Join pages
            content = page_separator.join(page_texts)

            return FormattedOutput(
                content=content,
                format=self.name,
                encoding="utf-8",
            )

        except Exception as e:
            raise FormattingError(f"Text formatting failed: {e}") from e