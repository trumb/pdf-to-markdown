"""YAML formatter for structured output."""

from datetime import datetime, timezone
from typing import Any

import yaml

from pdf2md.extractors.base import PDFExtraction
from pdf2md.formatters.base import FormattedOutput, FormattingError, OutputFormatter


class YAMLFormatter(OutputFormatter):
    """Format PDF extraction as YAML."""

    @property
    def name(self) -> str:
        """Return formatter name."""
        return "yaml"

    def format(self, extraction: PDFExtraction, **options: Any) -> FormattedOutput:
        """
        Format extraction as YAML.

        Options:
            tokens: Token count dictionary (optional)
            source_file: Source PDF filename (optional)
            source_hash: Source PDF hash (optional)

        Returns:
            FormattedOutput with YAML content
        """
        tokens = options.get("tokens", {})
        source_file = options.get("source_file", "")
        source_hash = options.get("source_hash", "")

        try:
            # Build YAML structure (similar to JSON but YAML output)
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

            # Convert to YAML
            yaml_content = yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

            return FormattedOutput(
                content=yaml_content,
                format=self.name,
                encoding="utf-8",
            )

        except Exception as e:
            raise FormattingError(f"YAML formatting failed: {e}") from e