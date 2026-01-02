"""Main CLI application using Typer."""

import typer
from rich.console import Console

from pdf2md.cli.commands import admin
from pdf2md.cli.commands.convert import convert_command
from pdf2md.cli.commands.info import info_command
from pdf2md.cli.commands.validate import validate_command

# Create Typer app
app = typer.Typer(
    name="pdf2md",
    help="PDF-to-Markdown converter with LLM token counting and security sandbox",
    no_args_is_help=True,
    add_completion=False,
)

# Create Rich console for pretty output
console = Console()

# Register commands
app.command(name="convert")(convert_command)
app.command(name="info")(info_command)
app.command(name="validate")(validate_command)

# Register admin subcommand
app.add_typer(admin.app, name="admin")


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
