"""Markdown formatter with YAML frontmatter."""

from datetime import datetime, timezone
from typing import Any

import yaml

from pdf2md.extractors.base import PDFExtraction
from pdf2md.formatters.base import FormattedOutput, FormattingError, OutputFormatter


class MarkdownFormatter(OutputFormatter):
    """Format PDF extraction as Markdown with YAML frontmatter."""

    @property
    def name(self) -> str:
        """Return formatter name."""
        return "markdown"

    def format(self, extraction: PDFExtraction, **options: Any) -> FormattedOutput:
        """
        Format extraction as Markdown.

        Options:
            include_frontmatter: Include YAML frontmatter (default: True)
            include_tokens: Include token counts in frontmatter (default: True)
            tokens: Token count dictionary (optional)
            source_file: Source PDF filename (optional)
            source_hash: Source PDF hash (optional)

        Returns:
            FormattedOutput with Markdown content
        """
        include_frontmatter = options.get("include_frontmatter", True)
        include_tokens = options.get("include_tokens", True)
        tokens = options.get("tokens", {})
        source_file = options.get("source_file", "")
        source_hash = options.get("source_hash", "")

        try:
            # Build content
            parts: list[str] = []

            # Add frontmatter if requested
            if include_frontmatter:
                frontmatter = self._build_frontmatter(
                    extraction=extraction,
                    include_tokens=include_tokens,
                    tokens=tokens,
                    source_file=source_file,
                    source_hash=source_hash,
                )
                parts.append("---")
                parts.append(frontmatter)
                parts.append("---")
                parts.append("")  # Blank line after frontmatter

            # Add page content
            for page in extraction.pages:
                if page.text.strip():
                    parts.append(page.text.strip())
                    parts.append("")  # Blank line between pages

            content = "\n".join(parts)

            return FormattedOutput(
                content=content,
                format=self.name,
                encoding="utf-8",
            )

        except Exception as e:
            raise FormattingError(f"Markdown formatting failed: {e}") from e

    def _build_frontmatter(
        self,
        extraction: PDFExtraction,
        include_tokens: bool,
        tokens: dict[str, int],
        source_file: str,
        source_hash: str,
    ) -> str:
        """Build YAML frontmatter with metadata."""
        # Build frontmatter dict with stable key ordering
        frontmatter_dict: dict[str, Any] = {}

        # Source information
        if source_file:
            frontmatter_dict["source_file"] = source_file
        if source_hash:
            frontmatter_dict["source_hash"] = source_hash

        # Conversion metadata
        frontmatter_dict["converted_at"] = datetime.now(timezone.utc).isoformat()
        frontmatter_dict["converter_version"] = "1.0.0"

        # PDF metadata
        if extraction.metadata.title:
            frontmatter_dict["title"] = extraction.metadata.title
        if extraction.metadata.author:
            frontmatter_dict["author"] = extraction.metadata.author

        frontmatter_dict["pages"] = extraction.metadata.page_count

        # Token counts if provided
        if include_tokens and tokens:
            frontmatter_dict["tokens"] = tokens

        # Extraction information
        frontmatter_dict["extraction_method"] = extraction.extraction_method
        frontmatter_dict["extraction_time_seconds"] = round(
            extraction.extraction_time_seconds, 3
        )

        # Warnings if any
        if extraction.warnings:
            frontmatter_dict["warnings"] = extraction.warnings

        # Convert to YAML with stable ordering
        yaml_content = yaml.dump(
            frontmatter_dict,
            default_flow_style=False,
            sort_keys=False,  # Preserve insertion order
            allow_unicode=True,
        )

        return yaml_content.rstrip()