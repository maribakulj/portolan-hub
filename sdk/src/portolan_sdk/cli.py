"""`portolan` CLI entry point.

Sprint 0 ships a placeholder so packaging and entry points are exercised
end-to-end. Real commands (`sources`, `query`, `plugin`) land in Sprint 4.
"""

from __future__ import annotations

import typer

from portolan_sdk import __version__

app = typer.Typer(
    name="portolan",
    help="Portolan Hub CLI. Not functional yet — see ROADMAP.md (Sprint 4).",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo(f"portolan {__version__}")


@app.command()
def sources() -> None:
    """List registered sources. Not implemented yet (see ROADMAP.md, Sprint 1)."""
    typer.echo("Not implemented yet. This lands in Sprint 1.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
