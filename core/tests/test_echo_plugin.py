"""Integration test: load and run the real `echo` plugin from plugins/."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from portolan_core import PluginLoader, Query, Result

PLUGINS_ROOT = Path(__file__).resolve().parents[2] / "plugins"


async def _collect(it: AsyncIterator[Result]) -> list[Result]:
    out: list[Result] = []
    async for r in it:
        out.append(r)
    return out


@pytest.fixture
def echo_connector() -> object:
    loader = PluginLoader()
    loader.load_from_directory(PLUGINS_ROOT)
    for connector in loader.loaded:
        if connector.source.id == "echo":
            return connector
    pytest.fail("echo plugin could not be loaded from plugins/ directory")


async def test_echo_returns_fixtures(echo_connector) -> None:  # type: ignore[no-untyped-def]
    results = await _collect(echo_connector.search(Query(intent="")))
    assert len(results) >= 5
    for r in results:
        assert r.source_id == "echo"
        assert r.rights.statement.value == "CC0"
        assert r.provenance.source_id == "echo"


async def test_echo_matches_substring(echo_connector) -> None:  # type: ignore[no-untyped-def]
    results = await _collect(echo_connector.search(Query(intent="Moreau")))
    titles = [r.title for r in results if r.title]
    assert all(
        "moreau" in (t or "").casefold() or any("moreau" in (c.name.casefold()) for c in r.creators)
        for r, t in zip(results, titles, strict=False)
    )
    assert results
    for r in results:
        assert r.provenance.latency_ms is not None


async def test_echo_honors_limit_and_offset(echo_connector) -> None:  # type: ignore[no-untyped-def]
    first_page = await _collect(echo_connector.search(Query(intent="", limit=2, offset=0)))
    second_page = await _collect(echo_connector.search(Query(intent="", limit=2, offset=2)))

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert {r.native_id for r in first_page}.isdisjoint({r.native_id for r in second_page})


async def test_echo_empty_query_returns_all(echo_connector) -> None:  # type: ignore[no-untyped-def]
    results = await _collect(echo_connector.search(Query(intent="Cresques")))
    assert len(results) == 1
    assert results[0].creators[0].name == "Abraham Cresques"
