"""Table handling strategies for PDF conversion."""

from typing import Any, Literal


class TableHandler:
    """Handle tables extracted from PDF with different output formats."""

    def __init__(
        self, format: Literal["markdown", "html", "code", "csv"] = "markdown"
    ) -> None:
        """
        Initialize table handler.

        Args:
            format: Table output format
                - markdown: Markdown table syntax
                - html: HTML table tags
                - code: Preformatted code block
                - csv: Comma-separated values
        """
        self.format = format

    def process_tables(self, tables: list[dict[str, Any]], page_num: int) -> str:
        """
        Process tables from a page.

        Args:
            tables: List of table dictionaries from extractor
            page_num: Page number

        Returns:
            Formatted table string
        """
        if not tables:
            return ""

        result_parts: list[str] = []

        for table_idx, table in enumerate(tables, start=1):
            table_data = table.get("data", [])
            if not table_data:
                continue

            if self.format == "markdown":
                result_parts.append(self._format_markdown_table(table_data))
            elif self.format == "html":
                result_parts.append(self._format_html_table(table_data))
            elif self.format == "code":
                result_parts.append(self._format_code_table(table_data))
            elif self.format == "csv":
                result_parts.append(self._format_csv_table(table_data))

            result_parts.append("")  # Blank line after table

        return "\n".join(result_parts)

    def _format_markdown_table(self, table_data: list[list[str]]) -> str:
        """Format table as Markdown."""
        if not table_data:
            return ""

        lines = []

        # Use first row as header
        header = table_data[0] if table_data else []
        rows = table_data[1:] if len(table_data) > 1 else []

        if header:
            # Header row
            header_str = " | ".join(str(cell or "") for cell in header)
            lines.append(f"| {header_str} |")

            # Separator row
            separator = " | ".join("---" for _ in header)
            lines.append(f"| {separator} |")

            # Data rows
            for row in rows:
                # Pad row to match header length
                padded_row = row + [""] * (len(header) - len(row))
                row_str = " | ".join(str(cell or "") for cell in padded_row[: len(header)])
                lines.append(f"| {row_str} |")

        return "\n".join(lines)

    def _format_html_table(self, table_data: list[list[str]]) -> str:
        """Format table as HTML."""
        if not table_data:
            return ""

        lines = ["<table>"]

        # Header
        if table_data:
            lines.append("  <thead>")
            lines.append("    <tr>")
            for cell in table_data[0]:
                lines.append(f"      <th>{cell or ''}</th>")
            lines.append("    </tr>")
            lines.append("  </thead>")

        # Body
        if len(table_data) > 1:
            lines.append("  <tbody>")
            for row in table_data[1:]:
                lines.append("    <tr>")
                for cell in row:
                    lines.append(f"      <td>{cell or ''}</td>")
                lines.append("    </tr>")
            lines.append("  </tbody>")

        lines.append("</table>")

        return "\n".join(lines)

    def _format_code_table(self, table_data: list[list[str]]) -> str:
        """Format table as preformatted code block."""
        if not table_data:
            return ""

        lines = ["```"]
        for row in table_data:
            row_str = "\t".join(str(cell or "") for cell in row)
            lines.append(row_str)
        lines.append("```")

        return "\n".join(lines)

    def _format_csv_table(self, table_data: list[list[str]]) -> str:
        """Format table as CSV."""
        if not table_data:
            return ""

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        for row in table_data:
            writer.writerow([str(cell or "") for cell in row])

        return output.getvalue().rstrip()