"""CLI tests for the `portolan sources` subcommands.

Uses the real `plugins/` directory so the tests double as an end-to-end
smoke test of loader + registry + CLI rendering.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from portolan_sdk.cli import app

PLUGINS_ROOT = Path(__file__).resolve().parents[2] / "plugins"
runner = CliRunner()


def test_sources_list_includes_echo_and_iiif() -> None:
    result = runner.invoke(app, ["--plugins-dir", str(PLUGINS_ROOT), "sources", "list"])
    assert result.exit_code == 0, result.output
    assert "echo" in result.output
    assert "iiif-generic" in result.output


def test_sources_show_for_echo() -> None:
    result = runner.invoke(app, ["--plugins-dir", str(PLUGINS_ROOT), "sources", "show", "echo"])
    assert result.exit_code == 0
    assert "Echo" in result.output
    assert "full_text" in result.output


def test_sources_show_unknown_returns_error() -> None:
    result = runner.invoke(app, ["--plugins-dir", str(PLUGINS_ROOT), "sources", "show", "nope"])
    assert result.exit_code == 2
    assert "Unknown source" in result.output


def test_sources_list_empty_directory_returns_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--plugins-dir", str(tmp_path), "sources", "list"])
    assert result.exit_code == 1


def test_sources_health_pings_defaults() -> None:
    result = runner.invoke(app, ["--plugins-dir", str(PLUGINS_ROOT), "sources", "health"])
    assert result.exit_code == 0
    assert "default health check" in result.output
