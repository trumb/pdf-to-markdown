"""Convert command for CLI."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pdf2md.core.converter import PDFConverter

console = Console()


def convert_command(
    pdf_file: Optional[Path] = typer.Argument(
        None,
        help="PDF file to convert (reads from stdin if not provided)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (writes to stdout if not provided)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format (markdown, json, yaml, text)",
    ),
    no_frontmatter: bool = typer.Option(
        False,
        "--no-frontmatter",
        help="Disable YAML frontmatter in markdown",
    ),
    no_tokens: bool = typer.Option(
        False,
        "--no-tokens",
        help="Disable token counting",
    ),
    extractor: str = typer.Option(
        "auto",
        "--extractor",
        "-e",
        help="Extraction engine (auto, pdfplumber, pymupdf)",
    ),
    no_sandbox: bool = typer.Option(
        False,
        "--no-sandbox",
        help="Disable security sandbox (not recommended)",
    ),
) -> None:
    """
    Convert PDF to Markdown or other formats.

    Examples:

        # Convert PDF to markdown
        pdf2md convert document.pdf -o output.md

        # Pipe PDF from stdin
        cat document.pdf | pdf2md convert > output.md

        # JSON output with custom extractor
        pdf2md convert document.pdf -f json -e pdfplumber
    """
    try:
        # Handle stdin if no file provided
        if pdf_file is None:
            # Read from stdin to temporary file
            import tempfile

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".pdf"
            ) as temp_file:
                stdin_data = sys.stdin.buffer.read()
                temp_file.write(stdin_data)
                temp_path = Path(temp_file.name)

            pdf_file = temp_path

        # Create converter
        from pdf2md.core.config import Settings

        settings = Settings(
            extractor=extractor,  # type: ignore[arg-type]
            output_format=format,  # type: ignore[arg-type]
            include_frontmatter=not no_frontmatter,
            include_tokens=not no_tokens,
            sandbox_enabled=not no_sandbox,
        )

        converter = PDFConverter(settings)

        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Converting {pdf_file.name}...", total=None)

            # Convert
            result = converter.convert(pdf_file, output_format=format)  # type: ignore[arg-type]

            progress.update(task, description=f"✅ Converted {pdf_file.name}")

        # Output result
        if output:
            output.write_text(result, encoding="utf-8")
            console.print(f"[green]Output written to: {output}[/green]")
        else:
            # Write to stdout
            sys.stdout.write(result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", err=True)
        raise typer.Exit(code=1)