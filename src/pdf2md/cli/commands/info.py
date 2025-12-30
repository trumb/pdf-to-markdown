"""Info command for CLI - display PDF metadata."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pdf2md.core.converter import PDFConverter

console = Console()


def info_command(
    pdf_file: Path = typer.Argument(
        ...,
        help="PDF file to inspect",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output metadata as JSON",
    ),
) -> None:
    """
    Display PDF metadata and file information.

    Examples:

        # Show PDF metadata
        pdf2md info document.pdf

        # Output as JSON
        pdf2md info document.pdf --json
    """
    try:
        # Create converter
        converter = PDFConverter()

        # Get metadata
        metadata = converter.get_metadata(pdf_file)

        if json_output:
            # Output as JSON
            print(json.dumps(metadata, indent=2))
        else:
            # Display as Rich table
            _display_metadata_table(metadata, pdf_file)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", err=True)
        raise typer.Exit(code=1)


def _display_metadata_table(metadata: dict, pdf_file: Path) -> None:
    """Display metadata as formatted table."""
    # File Information Table
    file_table = Table(title=f"📄 File Information: {pdf_file.name}")
    file_table.add_column("Property", style="cyan")
    file_table.add_column("Value", style="green")

    file_info = metadata.get("file", {})
    file_table.add_row("Path", str(file_info.get("path", "")))
    file_table.add_row(
        "Size", f"{file_info.get('size_mb', 0):.2f} MB ({file_info.get('size_bytes', 0):,} bytes)"
    )
    file_table.add_row("SHA256", file_info.get("sha256", "")[:64])
    file_table.add_row("Readable", "✅ Yes" if file_info.get("is_readable") else "❌ No")

    console.print(file_table)
    console.print()

    # PDF Metadata Table
    pdf_table = Table(title="📋 PDF Metadata")
    pdf_table.add_column("Property", style="cyan")
    pdf_table.add_column("Value", style="green")

    pdf_info = metadata.get("pdf", {})
    pdf_table.add_row("Title", pdf_info.get("title") or "(none)")
    pdf_table.add_row("Author", pdf_info.get("author") or "(none)")
    pdf_table.add_row("Subject", pdf_info.get("subject") or "(none)")
    pdf_table.add_row("Creator", pdf_info.get("creator") or "(none)")
    pdf_table.add_row("Producer", pdf_info.get("producer") or "(none)")
    pdf_table.add_row("Pages", str(pdf_info.get("page_count", 0)))
    pdf_table.add_row("Encrypted", "🔒 Yes" if pdf_info.get("encrypted") else "🔓 No")

    if pdf_info.get("creation_date"):
        pdf_table.add_row("Created", pdf_info["creation_date"])
    if pdf_info.get("modification_date"):
        pdf_table.add_row("Modified", pdf_info["modification_date"])

    console.print(pdf_table)