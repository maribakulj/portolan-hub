"""Generic IIIF Search API v1 connector.

Sends a ``q=<intent>`` parameter to the configured ``base_url`` and
parses the returned AnnotationList / AnnotationPage into pivot Results.
One annotation becomes one Result ; the parent manifest URI (`on`) is
used as the Portolan identifier when available.

Sprint 2 will add OAI-PMH + SRU siblings and the federator ; for Sprint 1
this plugin's job is to prove the contract can accommodate a real
async, HTTP-backed connector.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any

import httpx

from portolan_core import (
    Connector,
    InvalidQuery,
    Media,
    MediaKind,
    ParseError,
    Provenance,
    Query,
    Result,
    ResultType,
    Rights,
    RightsStatement,
    Source,
    SourceUnavailable,
)

_HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_USER_AGENT = "PortolanHub/0.1 (+https://github.com/maribakulj/portolan-hub)"


class IIIFGenericConnector(Connector):
    """IIIF Content Search API v1 client."""

    def __init__(
        self,
        source: Source,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(source=source)
        if not source.base_url:
            raise InvalidQuery(
                f"source {source.id!r} has no base_url — the IIIF Search "
                "connector cannot function without one"
            )
        self._own_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/ld+json, application/json"},
        )

    async def search(self, query: Query) -> AsyncIterator[Result]:
        started = perf_counter()
        params = {"q": query.intent}
        try:
            response = await self._client.get(self.source.base_url or "", params=params)
        except httpx.TimeoutException as exc:
            raise SourceUnavailable(f"{self.source.id} timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise SourceUnavailable(f"{self.source.id} transport error: {exc}") from exc

        if response.status_code >= 500:
            raise SourceUnavailable(
                f"{self.source.id} returned {response.status_code}: {response.text[:200]}"
            )
        if response.status_code >= 400:
            raise InvalidQuery(
                f"{self.source.id} rejected the query with {response.status_code}: "
                f"{response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ParseError(f"{self.source.id} returned non-JSON: {exc}") from exc

        annotations = _extract_annotations(payload)
        latency_ms = int((perf_counter() - started) * 1000)

        sliced = annotations[query.offset : query.offset + query.limit]
        for ann in sliced:
            yield _annotation_to_result(
                ann,
                source_id=self.source.id,
                plugin_version=self.source.version,
                latency_ms=latency_ms,
                query=query,
            )

    async def aclose(self) -> None:
        if self._own_client:
            await self._client.aclose()


def _extract_annotations(payload: Any) -> list[dict[str, Any]]:
    """Accept v1 (AnnotationList) and v2 (AnnotationPage) shapes."""
    if not isinstance(payload, dict):
        raise ParseError(f"IIIF Search response must be an object, got {type(payload).__name__}")

    # IIIF Search v1 (the most deployed shape).
    if "resources" in payload and isinstance(payload["resources"], list):
        return [a for a in payload["resources"] if isinstance(a, dict)]

    # IIIF Search v2 / W3C Web Annotation AnnotationPage.
    if "items" in payload and isinstance(payload["items"], list):
        return [a for a in payload["items"] if isinstance(a, dict)]

    return []


def _annotation_to_result(
    ann: dict[str, Any],
    *,
    source_id: str,
    plugin_version: str,
    latency_ms: int,
    query: Query,
) -> Result:
    native_id = str(ann.get("@id") or ann.get("id") or "")
    if not native_id:
        raise ParseError("annotation is missing both @id and id")

    manifest_uri = _coerce_str(ann.get("on"))
    resource = ann.get("resource") if isinstance(ann.get("resource"), dict) else None
    body = ann.get("body") if isinstance(ann.get("body"), dict) else None

    title = None
    for candidate in (resource, body):
        if candidate:
            chars = candidate.get("chars") or candidate.get("value")
            if isinstance(chars, str) and chars.strip():
                title = chars.strip()
                break

    media: list[Media] = []
    if manifest_uri:
        media.append(Media(kind=MediaKind.IIIF_MANIFEST, url=manifest_uri))

    return Result(
        id=f"urn:portolan:{source_id}:{_slug(native_id)}",
        source_id=source_id,
        native_id=native_id,
        type=ResultType.MANIFEST,
        title=title,
        media=media,
        rights=Rights(statement=RightsStatement.UNKNOWN),
        provenance=Provenance(
            source_id=source_id,
            plugin_version=plugin_version,
            query_sent={"q": query.intent, "limit": query.limit, "offset": query.offset},
            latency_ms=latency_ms,
        ),
        extras={"iiif_annotation": ann},
    )


def _coerce_str(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, str):
            return first
    return None


def _slug(value: str) -> str:
    """Make an `id` URL-safe. Not perfect ; good enough for Sprint 1."""
    return value.replace("://", "_").replace("/", "_").replace(":", "_").replace("#", "_")
