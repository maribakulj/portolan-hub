"""Plugin loader: directory-based discovery and error isolation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from portolan_core import PluginLoader, Query, Result

VALID_MANIFEST = """
manifest_version: "1"
id: {id}
name: "{name}"
protocol: test
capabilities: [full_text]
entry_point: "connector:{cls}"
"""

CONNECTOR_TEMPLATE = """
from collections.abc import AsyncIterator
from portolan_core import Connector, Query, Result


class {cls}(Connector):
    async def search(self, query: Query) -> AsyncIterator[Result]:
        return
        yield  # pragma: no cover
"""


def _write_plugin(root: Path, plugin_id: str, cls: str, connector_body: str | None = None) -> None:
    plugin_dir = root / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.yaml").write_text(
        VALID_MANIFEST.format(id=plugin_id, name=plugin_id, cls=cls), encoding="utf-8"
    )
    (plugin_dir / "connector.py").write_text(
        connector_body or CONNECTOR_TEMPLATE.format(cls=cls), encoding="utf-8"
    )


def test_loader_discovers_multiple_plugins(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "alpha", "AlphaConnector")
    _write_plugin(tmp_path, "bravo", "BravoConnector")

    loader = PluginLoader()
    loader.load_from_directory(tmp_path)

    ids = {c.source.id for c in loader.loaded}
    assert ids == {"alpha", "bravo"}
    assert loader.errors == []


def test_loader_isolates_failures(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "ok", "OkConnector")
    # Bad plugin: connector.py has a syntax error.
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "manifest.yaml").write_text(
        VALID_MANIFEST.format(id="bad", name="bad", cls="BadConnector"),
        encoding="utf-8",
    )
    (bad_dir / "connector.py").write_text("def broken(:\n", encoding="utf-8")

    loader = PluginLoader()
    loader.load_from_directory(tmp_path)

    assert [c.source.id for c in loader.loaded] == ["ok"]
    assert len(loader.errors) == 1
    assert loader.errors[0].code == "plugin_load_error"


def test_loader_rejects_non_connector(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "rogue"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.yaml").write_text(
        VALID_MANIFEST.format(id="rogue", name="rogue", cls="NotAConnector"),
        encoding="utf-8",
    )
    (plugin_dir / "connector.py").write_text("class NotAConnector: pass\n", encoding="utf-8")

    loader = PluginLoader()
    loader.load_from_directory(tmp_path)
    assert loader.loaded == []
    assert loader.errors
    assert "does not resolve to a Connector" in loader.errors[0].error


def test_loader_handles_missing_directory(tmp_path: Path) -> None:
    loader = PluginLoader()
    loader.load_from_directory(tmp_path / "missing")
    assert loader.loaded == []
    assert loader.errors == []


def test_loaded_plugins_have_working_source(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "alpha", "AlphaConnector")
    loader = PluginLoader()
    loader.load_from_directory(tmp_path)

    connector = loader.loaded[0]
    source = connector.source
    assert source.id == "alpha"
    assert source.protocol == "test"


async def _consume(iterator: AsyncIterator[Result]) -> list[Result]:
    items: list[Result] = []
    async for item in iterator:
        items.append(item)
    return items


async def test_loaded_empty_connector_yields_nothing(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "alpha", "AlphaConnector")
    loader = PluginLoader()
    loader.load_from_directory(tmp_path)
    connector = loader.loaded[0]
    results = await _consume(connector.search(Query(intent="anything")))
    assert results == []
