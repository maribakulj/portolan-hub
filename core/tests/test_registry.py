"""SourceRegistry behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from portolan_core import (
    Capability,
    Connector,
    Query,
    Result,
    Source,
    SourceRegistry,
)


class _FakeConnector(Connector):
    async def search(self, query: Query) -> AsyncIterator[Result]:
        return
        yield  # pragma: no cover


def _make_source(
    id_: str,
    capabilities: list[Capability] | None = None,
) -> Source:
    return Source(
        id=id_,
        name=id_.capitalize(),
        protocol="x",
        capabilities=capabilities or [],
    )


def test_register_and_get() -> None:
    reg = SourceRegistry()
    c = _FakeConnector(_make_source("demo"))
    reg.register(c)

    assert reg.get("demo") is c
    assert reg.get("other") is None
    assert "demo" in reg
    assert len(reg) == 1


def test_register_replaces_existing() -> None:
    reg = SourceRegistry()
    reg.register(_FakeConnector(_make_source("demo")))
    replacement = _FakeConnector(_make_source("demo", [Capability.FULL_TEXT]))
    reg.register(replacement)
    assert reg.get("demo") is replacement
    assert len(reg) == 1


def test_list_sources_is_sorted_by_id() -> None:
    reg = SourceRegistry()
    reg.register(_FakeConnector(_make_source("bravo")))
    reg.register(_FakeConnector(_make_source("alpha")))
    ids = [s.id for s in reg.list_sources()]
    assert ids == ["alpha", "bravo"]


def test_filter_by_capability() -> None:
    reg = SourceRegistry()
    reg.register(_FakeConnector(_make_source("a", [Capability.FULL_TEXT])))
    reg.register(_FakeConnector(_make_source("b", [Capability.IIIF_MANIFEST])))
    reg.register(
        _FakeConnector(_make_source("c", [Capability.FULL_TEXT, Capability.IIIF_MANIFEST]))
    )

    ids = [s.id for s in reg.filter_by_capability(Capability.FULL_TEXT)]
    assert ids == ["a", "c"]


def test_require_raises_when_missing() -> None:
    reg = SourceRegistry()
    with pytest.raises(KeyError):
        reg.require("nope")


def test_unregister_removes_source() -> None:
    reg = SourceRegistry()
    reg.register(_FakeConnector(_make_source("demo")))
    reg.unregister("demo")
    assert "demo" not in reg
    reg.unregister("demo")  # idempotent
