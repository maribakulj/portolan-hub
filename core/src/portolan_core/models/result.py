"""Result pivot model + provenance."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from portolan_core.models.primitives import (
    Agent,
    Concept,
    Link,
    Media,
    Place,
    Rights,
    TemporalSpan,
)

_STRICT = ConfigDict(extra="forbid", str_strip_whitespace=True)
_LOOSE = ConfigDict(extra="forbid")  # for models carrying dict/Any payloads


class ResultType(StrEnum):
    WORK = "work"
    OBJECT = "object"
    MANIFEST = "manifest"
    PERSON = "person"
    PLACE = "place"
    SET = "set"
    OTHER = "other"


class Transformation(BaseModel):
    """One step in the pipeline that produced a Result.

    Recorded in provenance so we can explain where a field came from.
    """

    model_config = _STRICT

    name: str = Field(min_length=1)
    applied_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None


class Provenance(BaseModel):
    """How a Result came to exist.

    Close in spirit to W3C PROV-O but intentionally lighter: we want
    citability and reproducibility, not a full ontology.
    """

    model_config = _LOOSE

    source_id: str = Field(min_length=1)
    plugin_version: str = Field(min_length=1)
    query_sent: dict[str, Any] = Field(
        default_factory=dict,
        description="The request as seen by the source (serializable).",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: int | None = Field(default=None, ge=0)
    transformations: list[Transformation] = Field(default_factory=list)


class Result(BaseModel):
    """A normalized heritage resource.

    Only `id`, `source_id`, `native_id`, `provenance` and `rights` are
    mandatory. Everything else is optional so that thin sources (an OAI
    feed with Dublin Core only) and rich sources (a LinkedArt endpoint)
    fit the same pivot.

    Source-specific fields the pivot does not cover go into `extras`.
    """

    model_config = _LOOSE

    id: str = Field(
        min_length=1,
        description="Stable Portolan identifier (URN or opaque string).",
    )
    source_id: str = Field(min_length=1)
    native_id: str = Field(
        min_length=1,
        description="Identifier as assigned by the source.",
    )
    type: ResultType = ResultType.WORK
    title: str | None = None
    creators: list[Agent] = Field(default_factory=list)
    dates: list[TemporalSpan] = Field(default_factory=list)
    places: list[Place] = Field(default_factory=list)
    subjects: list[Concept] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    description: str | None = None
    media: list[Media] = Field(default_factory=list)
    rights: Rights
    links: list[Link] = Field(default_factory=list)
    provenance: Provenance
    extras: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific fields preserved verbatim.",
    )
