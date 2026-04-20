"""Integration test for the iiif-generic plugin with a mocked HTTP transport."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from portolan_core import PluginLoader, Query, Result, Source, SourceUnavailable

PLUGINS_ROOT = Path(__file__).resolve().parents[2] / "plugins"

IIIF_V1_PAYLOAD = {
    "@context": "http://iiif.io/api/search/1/context.json",
    "@id": "https://example.org/search?q=moreau",
    "@type": "sc:AnnotationList",
    "within": {"@type": "sc:Layer", "total": 2},
    "resources": [
        {
            "@id": "https://example.org/annotations/1",
            "@type": "oa:Annotation",
            "motivation": "sc:painting",
            "on": "https://example.org/iiif/work1/manifest.json",
            "resource": {"@type": "cnt:ContentAsText", "chars": "Salome"},
        },
        {
            "@id": "https://example.org/annotations/2",
            "@type": "oa:Annotation",
            "motivation": "sc:painting",
            "on": "https://example.org/iiif/work2/manifest.json",
            "resource": {"@type": "cnt:ContentAsText", "chars": "The Apparition"},
        },
    ],
}


async def _collect(it: AsyncIterator[Result]) -> list[Result]:
    out: list[Result] = []
    async for r in it:
        out.append(r)
    return out


def _load_iiif_class() -> type:
    """Reuse the loader's path resolution to import the plugin class."""
    loader = PluginLoader()
    loader.load_from_directory(PLUGINS_ROOT)
    for connector in loader.loaded:
        if connector.source.id == "iiif-generic":
            return type(connector)
    pytest.fail("iiif-generic plugin could not be loaded")


def _make_source(base_url: str = "https://example.org/search") -> Source:
    return Source(
        id="iiif-generic",
        name="IIIF Search",
        protocol="iiif-search",
        base_url=base_url,
    )


def _client_returning(payload: dict | str, status: int = 200) -> httpx.AsyncClient:
    def handler(_: httpx.Request) -> httpx.Response:
        if isinstance(payload, str):
            return httpx.Response(status_code=status, text=payload)
        return httpx.Response(status_code=status, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_iiif_parses_v1_annotation_list() -> None:
    cls = _load_iiif_class()
    async with _client_returning(IIIF_V1_PAYLOAD) as client:
        connector = cls(_make_source(), client=client)
        results = await _collect(connector.search(Query(intent="Moreau")))

    assert len(results) == 2
    titles = [r.title for r in results]
    assert titles == ["Salome", "The Apparition"]
    manifest_urls = [m.url for r in results for m in r.media if m.kind.value == "iiif_manifest"]
    assert manifest_urls == [
        "https://example.org/iiif/work1/manifest.json",
        "https://example.org/iiif/work2/manifest.json",
    ]


async def test_iiif_parses_v2_items_list() -> None:
    cls = _load_iiif_class()
    v2 = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": "https://example.org/search",
        "type": "AnnotationPage",
        "items": [
            {
                "id": "https://example.org/annotations/10",
                "type": "Annotation",
                "body": {"type": "TextualBody", "value": "Art déco"},
                "on": "https://example.org/iiif/10/manifest",
            }
        ],
    }
    async with _client_returning(v2) as client:
        connector = cls(_make_source(), client=client)
        results = await _collect(connector.search(Query(intent="art déco")))
    assert len(results) == 1
    assert results[0].title == "Art déco"


async def test_iiif_reports_source_unavailable_on_5xx() -> None:
    cls = _load_iiif_class()
    async with _client_returning({"error": "boom"}, status=503) as client:
        connector = cls(_make_source(), client=client)
        with pytest.raises(SourceUnavailable):
            async for _ in connector.search(Query(intent="x")):
                pass


async def test_iiif_requires_base_url() -> None:
    cls = _load_iiif_class()
    with pytest.raises(Exception):  # noqa: B017 — we just want non-crashing instantiation path
        cls(
            Source(id="iiif-generic", name="x", protocol="iiif-search", base_url=None),
        )
