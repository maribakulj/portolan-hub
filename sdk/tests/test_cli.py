"""Smoke test for the CLI entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from portolan_sdk import __version__
from portolan_sdk.cli import app


def test_version_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
