"""Admin CLI commands for token management."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pdf2md.auth.models import Role
from pdf2md.auth.token_manager import TokenManager
from pdf2md.database import Database

app = typer.Typer(help="Admin commands for token management")
console = Console()


@app.command("create-token")
def create_token_cmd(
    user_id: str = typer.Option(..., "--user-id", help="User ID for the token"),
    role: str = typer.Option(..., "--role", help="Role (admin, job_manager, job_writer, job_reader)"),
    expires: Optional[int] = typer.Option(None, "--expires", help="Days until expiration (optional)"),
    rate_limit: Optional[int] = typer.Option(None, "--rate-limit", help="Custom rate limit (optional)"),
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
) -> None:
    """
    Create a new API token.
    
    SECURITY: This is the ONLY way to create admin tokens.
    Admin tokens cannot be created via API.
    """
    asyncio.run(_create_token(user_id, role, expires, rate_limit, db_path))


async def _create_token(
    user_id: str, role_str: str, expires_days: Optional[int], rate_limit: Optional[int], db_path: str
) -> None:
    """Async implementation of create-token command."""
    # Validate role
    try:
        role = Role(role_str)
    except ValueError:
        console.print(f"[red]Error: Invalid role '{role_str}'[/red]")
        console.print("Valid roles: admin, job_manager, job_writer, job_reader")
        raise typer.Exit(1)

    # Connect to database
    database = Database(db_path)
    await database.connect()

    try:
        # Create token
        token_manager = TokenManager(database)
        token_id, token = await token_manager.create_token(
            user_id, role, optExpiresDays=expires_days, intRateLimit=rate_limit
        )

        # Display results
        console.print("\n[green]✓ Token created successfully![/green]\n")
        console.print(f"[bold]Token:[/bold] {token}")
        console.print(f"[bold]Token ID:[/bold] {token_id}")
        console.print(f"[bold]User ID:[/bold] {user_id}")
        console.print(f"[bold]Role:[/bold] {role.value}")

        if role == Role.ADMIN:
            console.print("\n[yellow]⚠️  This is an ADMIN token with full system access![/yellow]")

        console.print("\n[yellow]⚠️  Store this token securely - it will not be shown again![/yellow]\n")

    finally:
        await database.disconnect()


@app.command("list-tokens")
def list_tokens_cmd(
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
) -> None:
    """List all tokens."""
    asyncio.run(_list_tokens(db_path))


async def _list_tokens(db_path: str) -> None:
    """Async implementation of list-tokens command."""
    database = Database(db_path)
    await database.connect()

    try:
        token_manager = TokenManager(database)
        tokens = await token_manager.list_tokens()

        if not tokens:
            console.print("[yellow]No tokens found[/yellow]")
            return

        # Create table
        table = Table(title="API Tokens")
        table.add_column("Token ID", style="cyan")
        table.add_column("User ID", style="green")
        table.add_column("Role", style="magenta")
        table.add_column("Active", style="yellow")
        table.add_column("Rate Limit", style="blue")
        table.add_column("Expires At", style="red")

        for token in tokens:
            table.add_row(
                token.strTokenId[:8] + "...",
                token.strUserId,
                token.role.value,
                "✓" if token.boolIsActive else "✗",
                str(token.intRateLimit),
                token.optExpiresAt.isoformat() if token.optExpiresAt else "Never",
            )

        console.print(table)

    finally:
        await database.disconnect()


@app.command("revoke-token")
def revoke_token_cmd(
    token_id: str = typer.Option(..., "--token-id", help="Token ID to revoke"),
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Permanently delete a token."""
    asyncio.run(_revoke_token(token_id, db_path, confirm))


async def _revoke_token(token_id: str, db_path: str, confirm: bool) -> None:
    """Async implementation of revoke-token command."""
    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to revoke token {token_id}?")
        if not confirmed:
            console.print("[yellow]Cancelled[/yellow]")
            return

    database = Database(db_path)
    await database.connect()

    try:
        token_manager = TokenManager(database)
        success = await token_manager.revoke_token(token_id)

        if success:
            console.print(f"[green]✓ Token {token_id} revoked successfully[/green]")
        else:
            console.print(f"[red]Error: Token {token_id} not found[/red]")
            raise typer.Exit(1)

    finally:
        await database.disconnect()


@app.command("disable-token")
def disable_token_cmd(
    token_id: str = typer.Option(..., "--token-id", help="Token ID to disable"),
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
) -> None:
    """Temporarily disable a token (reversible)."""
    asyncio.run(_disable_token(token_id, db_path))


async def _disable_token(token_id: str, db_path: str) -> None:
    """Async implementation of disable-token command."""
    database = Database(db_path)
    await database.connect()

    try:
        token_manager = TokenManager(database)
        success = await token_manager.disable_token(token_id)

        if success:
            console.print(f"[green]✓ Token {token_id} disabled successfully[/green]")
        else:
            console.print(f"[red]Error: Token {token_id} not found[/red]")
            raise typer.Exit(1)

    finally:
        await database.disconnect()


@app.command("enable-token")
def enable_token_cmd(
    token_id: str = typer.Option(..., "--token-id", help="Token ID to enable"),
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
) -> None:
    """Re-enable a disabled token."""
    asyncio.run(_enable_token(token_id, db_path))


async def _enable_token(token_id: str, db_path: str) -> None:
    """Async implementation of enable-token command."""
    database = Database(db_path)
    await database.connect()

    try:
        token_manager = TokenManager(database)
        success = await token_manager.enable_token(token_id)

        if success:
            console.print(f"[green]✓ Token {token_id} enabled successfully[/green]")
        else:
            console.print(f"[red]Error: Token {token_id} not found[/red]")
            raise typer.Exit(1)

    finally:
        await database.disconnect()


@app.command("token-usage")
def token_usage_cmd(
    token_id: str = typer.Option(..., "--token-id", help="Token ID"),
    days: int = typer.Option(7, "--days", help="Number of days to look back"),
    db_path: str = typer.Option("data/pdf2md.db", "--db", help="Database path"),
) -> None:
    """View token usage audit trail."""
    asyncio.run(_token_usage(token_id, days, db_path))


async def _token_usage(token_id: str, days: int, db_path: str) -> None:
    """Async implementation of token-usage command."""
    database = Database(db_path)
    await database.connect()

    try:
        token_manager = TokenManager(database)
        
        # Check token exists
        token = await token_manager.get_token_by_id(token_id)
        if token is None:
            console.print(f"[red]Error: Token {token_id} not found[/red]")
            raise typer.Exit(1)

        usage = await token_manager.get_token_usage(token_id, days)

        if not usage:
            console.print(f"[yellow]No usage found for token {token_id} in the last {days} days[/yellow]")
            return

        # Create table
        table = Table(title=f"Token Usage (Last {days} Days)")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Method", style="green")
        table.add_column("Endpoint", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Response Time", style="blue")

        for record in usage:
            table.add_row(
                record["timestamp"],
                record["method"],
                record["endpoint"],
                str(record["status_code"]),
                f"{record['response_time_ms']}ms" if record["response_time_ms"] else "N/A",
            )

        console.print(table)
        console.print(f"\n[bold]Total requests:[/bold] {len(usage)}")

    finally:
        await database.disconnect()
