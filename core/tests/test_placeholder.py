"""Placeholder test so pytest has something to run in Sprint 0."""

from portolan_core import __version__


def test_version_is_defined() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""
