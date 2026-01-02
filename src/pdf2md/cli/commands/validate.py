"""Validate command for CLI - security check for PDF files."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pdf2md.extractors.factory import ExtractorFactory
from pdf2md.security.validator import PDFValidator

console = Console()


def validate_command(
    pdf_file: Path = typer.Argument(
        ...,
        help="PDF file to validate",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    max_size: int = typer.Option(
        100,
        "--max-size",
        help="Maximum file size in MB",
    ),
) -> None:
    """
    Validate PDF file for security and readability.

    Performs the following checks:
    - File exists and is readable
    - Valid PDF magic bytes
    - File size within limits
    - Can be opened by extractors

    Examples:

        # Validate PDF
        pdf2md validate document.pdf

        # Validate with custom size limit
        pdf2md validate large.pdf --max-size 500
    """
    try:
        # Validation table
        table = Table(title=f"🔍 PDF Validation: {pdf_file.name}")
        table.add_column("Check", style="cyan")
        table.add_column("Result", style="white")

        # File validation
        is_valid, error_msg = PDFValidator.validate_file(pdf_file, max_size)

        if is_valid:
            table.add_row("File Validation", "✅ PASS")
        else:
            table.add_row("File Validation", f"❌ FAIL: {error_msg}")
            console.print(table)
            raise typer.Exit(code=1)

        # File info
        file_info = PDFValidator.get_file_info(pdf_file)
        table.add_row(
            "File Size",
            f"{file_info['size_mb']:.2f} MB ({file_info['size_bytes']:,} bytes)",
        )
        table.add_row("SHA256 Hash", file_info["sha256"][:64])

        # Try pdfplumber
        try:
            extractor = ExtractorFactory.create_extractor("pdfplumber")
            if extractor.validate_pdf(pdf_file):
                table.add_row("pdfplumber", "✅ Can extract")
            else:
                table.add_row("pdfplumber", "❌ Cannot extract")
        except Exception as e:
            table.add_row("pdfplumber", f"❌ Error: {e}")

        # Try pymupdf
        try:
            extractor = ExtractorFactory.create_extractor("pymupdf")
            if extractor.validate_pdf(pdf_file):
                table.add_row("PyMuPDF", "✅ Can extract")
            else:
                table.add_row("PyMuPDF", "❌ Cannot extract")
        except Exception as e:
            table.add_row("PyMuPDF", f"❌ Error: {e}")

        # Try to get metadata
        try:
            extractor = ExtractorFactory.create_extractor("auto")
            metadata = extractor.get_metadata(pdf_file)
            table.add_row("Metadata Extraction", "✅ Success")
            table.add_row("Page Count", str(metadata.page_count))
            table.add_row("Encrypted", "🔒 Yes" if metadata.encrypted else "🔓 No")
        except Exception as e:
            table.add_row("Metadata Extraction", f"❌ Failed: {e}")

        console.print(table)

        # Final verdict
        console.print()
        console.print("[bold green]✅ PDF is valid and can be processed[/bold green]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", err=True)
        raise typer.Exit(code=1)
