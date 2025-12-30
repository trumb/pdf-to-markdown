"""JSON formatter for structured output."""

import json
from datetime import datetime, timezone
from typing import Any

from pdf2md.extractors.base import PDFExtraction
from pdf2md.formatters.base import FormattedOutput, FormattingError, OutputFormatter


class JSONFormatter(OutputFormatter):
    """Format PDF extraction as JSON."""

    @property
    def name(self) -> str:
        """Return formatter name."""
        return "json"

    def format(self, extraction: PDFExtraction, **options: Any) -> FormattedOutput:
        """
        Format extraction as JSON.

        Options:
            indent: JSON indentation (default: 2)
            tokens: Token count dictionary (optional)
            source_file: Source PDF filename (optional)
            source_hash: Source PDF hash (optional)

        Returns:
            FormattedOutput with JSON content
        """
        indent = options.get("indent", 2)
        tokens = options.get("tokens", {})
        source_file = options.get("source_file", "")
        source_hash = options.get("source_hash", "")

        try:
            # Build JSON structure
            data: dict[str, Any] = {
                "metadata": {
                    "source_file": source_file or None,
                    "source_hash": source_hash or None,
                    "converted_at": datetime.now(timezone.utc).isoformat(),
                    "converter_version": "1.0.0",
                    "pdf": {
                        "title": extraction.metadata.title,
                        "author": extraction.metadata.author,
                        "subject": extraction.metadata.subject,
                        "creator": extraction.metadata.creator,
                        "producer": extraction.metadata.producer,
                        "creation_date": (
                            extraction.metadata.creation_date.isoformat()
                            if extraction.metadata.creation_date
                            else None
                        ),
                        "modification_date": (
                            extraction.metadata.modification_date.isoformat()
                            if extraction.metadata.modification_date
                            else None
                        ),
                        "page_count": extraction.metadata.page_count,
                        "encrypted": extraction.metadata.encrypted,
                        "file_size_bytes": extraction.metadata.file_size_bytes,
                    },
                    "tokens": tokens if tokens else None,
                    "extraction_method": extraction.extraction_method,
                    "extraction_time_seconds": round(
                        extraction.extraction_time_seconds, 3
                    ),
                    "warnings": extraction.warnings if extraction.warnings else [],
                },
                "pages": [
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "images": page.images,
                        "tables": page.tables,
                        "width": page.width,
                        "height": page.height,
                    }
                    for page in extraction.pages
                ],
            }

            # Convert to JSON
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)

            return FormattedOutput(
                content=json_content,
                format=self.name,
                encoding="utf-8",
            )

        except Exception as e:
            raise FormattingError(f"JSON formatting failed: {e}") from e