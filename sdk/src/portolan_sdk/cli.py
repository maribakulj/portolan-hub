"""`portolan` CLI entry point.

Sprint 1 commands load plugins locally (directory-based). Sprint 3 adds
API-backed commands (`--api-url`), and Sprint 4 fleshes out the CLI.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from portolan_core import PluginLoader, SourceRegistry
from portolan_sdk import __version__

app = typer.Typer(
    name="portolan",
    help="Portolan Hub CLI.",
    no_args_is_help=True,
    add_completion=False,
)

sources_app = typer.Typer(help="Manage and inspect registered sources.")
app.add_typer(sources_app, name="sources")

console = Console()
err_console = Console(stderr=True, style="red")


@app.command()
def version() -> None:
    """Print the CLI version."""
    console.print(f"portolan {__version__}")


@app.callback()
def _root(
    ctx: typer.Context,
    plugins_dir: Annotated[
        Path | None,
        typer.Option(
            "--plugins-dir",
            envvar="PORTOLAN_PLUGINS_DIR",
            help="Directory scanned for plugin manifests (defaults to ./plugins).",
        ),
    ] = None,
) -> None:
    """Root callback to thread shared options into subcommands."""
    resolved = plugins_dir or Path(os.environ.get("PORTOLAN_PLUGINS_DIR") or "plugins")
    ctx.obj = {"plugins_dir": resolved}


@sources_app.command("list")
def sources_list(ctx: typer.Context) -> None:
    """List registered sources."""
    registry = _build_registry(ctx)

    if not registry.list_sources():
        err_console.print(
            "No sources registered. "
            "Set PORTOLAN_PLUGINS_DIR or run from a directory with a `plugins/` folder."
        )
        raise typer.Exit(code=1)

    table = Table(title="Registered sources", show_lines=False)
    table.add_column("id", style="bold")
    table.add_column("name")
    table.add_column("protocol")
    table.add_column("status")
    table.add_column("capabilities", overflow="fold")

    for src in registry.list_sources():
        table.add_row(
            src.id,
            src.name,
            src.protocol,
            src.status.value,
            ", ".join(c.value for c in src.capabilities) or "—",
        )

    console.print(table)


@sources_app.command("show")
def sources_show(
    ctx: typer.Context,
    source_id: Annotated[str, typer.Argument(help="Source id to inspect.")],
) -> None:
    """Show details for a single source."""
    registry = _build_registry(ctx)
    connector = registry.get(source_id)
    if connector is None:
        err_console.print(f"Unknown source: {source_id!r}")
        raise typer.Exit(code=2)

    src = connector.source
    console.print(f"[bold]{src.name}[/bold]  ([cyan]{src.id}[/cyan])")
    console.print(f"  protocol      : {src.protocol}")
    console.print(f"  status        : {src.status.value}")
    console.print(f"  version       : {src.version}")
    if src.maintainer:
        console.print(f"  maintainer    : {src.maintainer}")
    if src.base_url:
        console.print(f"  base_url      : {src.base_url}")
    console.print(f"  auth_scheme   : {src.auth_scheme.value}")
    console.print(f"  rate_limit    : {src.rate_limit.rps} rps, burst {src.rate_limit.burst}")
    console.print(f"  rights_default: {src.rights_default.value}")
    console.print(
        "  capabilities  : "
        + (", ".join(c.value for c in src.capabilities) if src.capabilities else "—")
    )
    if src.coverage.description:
        console.print(f"  coverage      : {src.coverage.description.strip()}")
    if src.notes:
        console.print(f"  notes         : {src.notes.strip()}")


@sources_app.command("health")
def sources_health(ctx: typer.Context) -> None:
    """Ping each source's `health` method.

    Useful as a smoke test after editing a plugin manifest.
    """
    registry = _build_registry(ctx)
    if not registry.list_sources():
        err_console.print("No sources registered.")
        raise typer.Exit(code=1)

    async def _probe() -> list[tuple[str, bool, str]]:
        results: list[tuple[str, bool, str]] = []
        for src in registry.list_sources():
            connector = registry.require(src.id)
            status = await connector.health()
            results.append((src.id, status.ok, status.message or ""))
        return results

    outcomes = asyncio.run(_probe())
    table = Table(title="Source health")
    table.add_column("id", style="bold")
    table.add_column("ok")
    table.add_column("message")
    for source_id, ok, message in outcomes:
        table.add_row(source_id, "✓" if ok else "✗", message)
    console.print(table)


def _build_registry(ctx: typer.Context) -> SourceRegistry:
    plugins_dir: Path = (ctx.obj or {}).get("plugins_dir") or Path("plugins")

    loader = PluginLoader()
    loader.load_from_directory(plugins_dir)

    registry = SourceRegistry()
    for connector in loader.loaded:
        registry.register(connector)

    for failure in loader.errors:
        err_console.print(f"[warn] {failure.location}: {failure.error}")

    return registry


if __name__ == "__main__":
    app()
