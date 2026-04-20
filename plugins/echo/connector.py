"""Echo connector.

Matches `Query.intent` as a case-insensitive substring against fixture
titles, descriptions, creators, and subjects. Respects `limit` and
`offset`. No network I/O. Ideal for tests and the first smoke demo.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from time import perf_counter

from portolan_core import (
    Agent,
    AgentRole,
    Concept,
    Connector,
    Media,
    MediaKind,
    Place,
    Provenance,
    Query,
    Result,
    ResultType,
    Rights,
    RightsStatement,
    TemporalSpan,
)

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"


class EchoConnector(Connector):
    """Returns substring-matched fixtures as Portolan Results."""

    def __init__(self, source: object) -> None:  # type: ignore[override]
        # The loader passes a typed `Source`; keep the loose signature so
        # the plugin stays minimal in its imports (it should not need to
        # import Source directly to be loaded).
        super().__init__(source=source)  # type: ignore[arg-type]
        self._fixtures: list[dict[str, object]] = json.loads(
            FIXTURES_PATH.read_text(encoding="utf-8")
        )

    async def search(self, query: Query) -> AsyncIterator[Result]:
        started = perf_counter()
        needle = query.intent.casefold().strip()
        haystack_fields = ("title", "description", "creator", "subject")

        def _match(fx: dict[str, object]) -> bool:
            if not needle:
                return True
            for field in haystack_fields:
                value = fx.get(field)
                if isinstance(value, str) and needle in value.casefold():
                    return True
            return False

        matches = [fx for fx in self._fixtures if _match(fx)]
        matches = matches[query.offset : query.offset + query.limit]

        for fx in matches:
            yield _fixture_to_result(
                fx,
                source_id=self.source.id,
                plugin_version=self.source.version,
                latency_ms=int((perf_counter() - started) * 1000),
                query=query,
            )


def _fixture_to_result(
    fx: dict[str, object],
    *,
    source_id: str,
    plugin_version: str,
    latency_ms: int,
    query: Query,
) -> Result:
    native_id = str(fx["native_id"])

    creators = []
    creator = fx.get("creator")
    if isinstance(creator, str) and creator:
        creators.append(Agent(name=creator, role=AgentRole.CREATOR))

    dates: list[TemporalSpan] = []
    start = fx.get("date_start")
    end = fx.get("date_end")
    if isinstance(start, str) or isinstance(end, str):
        dates.append(
            TemporalSpan(
                start=start if isinstance(start, str) else None,
                end=end if isinstance(end, str) else None,
            )
        )

    places: list[Place] = []
    place = fx.get("place")
    if isinstance(place, str) and place:
        places.append(Place(name=place))

    subjects: list[Concept] = []
    subject = fx.get("subject")
    if isinstance(subject, str) and subject:
        subjects.append(Concept(label=subject))

    media: list[Media] = []
    image_url = fx.get("image_url")
    if isinstance(image_url, str) and image_url:
        media.append(Media(kind=MediaKind.IMAGE, url=image_url))
    manifest_url = fx.get("iiif_manifest")
    if isinstance(manifest_url, str) and manifest_url:
        media.append(Media(kind=MediaKind.IIIF_MANIFEST, url=manifest_url))

    type_value = fx.get("type")
    result_type = (
        ResultType(type_value) if isinstance(type_value, str) and type_value else ResultType.WORK
    )

    return Result(
        id=f"urn:portolan:{source_id}:{native_id}",
        source_id=source_id,
        native_id=native_id,
        type=result_type,
        title=str(fx.get("title") or "") or None,
        creators=creators,
        dates=dates,
        places=places,
        subjects=subjects,
        media=media,
        rights=Rights(statement=RightsStatement.CC0),
        description=str(fx.get("description") or "") or None,
        provenance=Provenance(
            source_id=source_id,
            plugin_version=plugin_version,
            query_sent={"intent": query.intent, "limit": query.limit, "offset": query.offset},
            latency_ms=latency_ms,
        ),
    )
