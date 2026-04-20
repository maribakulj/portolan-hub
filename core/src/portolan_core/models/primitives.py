"""Shared building blocks used across Query and Result models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)


class AgentRole(StrEnum):
    """How an agent relates to a resource.

    Kept coarse on purpose — fine-grained library roles (MARC relator codes)
    go into `Agent.extras` if a plugin wants to preserve them.
    """

    CREATOR = "creator"
    CONTRIBUTOR = "contributor"
    PUBLISHER = "publisher"
    SUBJECT = "subject"
    OWNER = "owner"
    OTHER = "other"


class Agent(BaseModel):
    """A person or organization associated with a resource."""

    model_config = _STRICT

    name: str = Field(min_length=1)
    role: AgentRole = AgentRole.CREATOR
    authority_id: str | None = Field(
        default=None,
        description="External identifier: VIAF, Wikidata Q-id, Getty ULAN, etc.",
    )


class TemporalSpan(BaseModel):
    """A date or date range, human-readable or machine-readable or both.

    We accept free-form `label` because heritage dates are often imprecise
    ("circa 1520", "16th century"); `start` and `end` carry the machine
    form when the source provides it (ISO 8601 or EDTF).
    """

    model_config = _STRICT

    label: str | None = None
    start: str | None = None
    end: str | None = None


class Place(BaseModel):
    """A place associated with a resource."""

    model_config = _STRICT

    name: str = Field(min_length=1)
    authority_id: str | None = None
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)


class Concept(BaseModel):
    """A subject, genre, or iconographic theme."""

    model_config = _STRICT

    label: str = Field(min_length=1)
    scheme: str | None = Field(
        default=None,
        description="Source vocabulary: Iconclass, AAT, RAMEAU, LCSH, etc.",
    )
    uri: str | None = None


class MediaKind(StrEnum):
    IMAGE = "image"
    THUMBNAIL = "thumbnail"
    IIIF_MANIFEST = "iiif_manifest"
    VIDEO = "video"
    AUDIO = "audio"
    MODEL_3D = "model_3d"
    DOCUMENT = "document"
    OTHER = "other"


class Media(BaseModel):
    """A media asset attached to a resource."""

    model_config = _STRICT

    kind: MediaKind
    url: str = Field(min_length=1)
    mime_type: str | None = None
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    description: str | None = None


class RightsStatement(StrEnum):
    """Coarse rights bucket.

    Mapping to full RightsStatements.org / CC URIs is done in Sprint 7.
    `UNKNOWN` is a first-class value: it is better for a plugin to say
    "I don't know" than to guess.
    """

    UNKNOWN = "unknown"
    PUBLIC_DOMAIN = "public_domain"
    NO_COPYRIGHT = "no_copyright"
    IN_COPYRIGHT = "in_copyright"
    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_ND = "CC-BY-ND"
    OTHER = "other"


class Rights(BaseModel):
    """Rights status for a resource.

    `statement` can be `UNKNOWN` but the field itself is mandatory on
    `Result` — we force plugins to acknowledge the question exists.
    """

    model_config = _STRICT

    statement: RightsStatement = RightsStatement.UNKNOWN
    url: str | None = Field(
        default=None,
        description="Canonical rights URI (e.g. rightsstatements.org, creativecommons.org).",
    )
    notes: str | None = None


class Link(BaseModel):
    """A typed link to a related resource."""

    model_config = _STRICT

    rel: str = Field(min_length=1, description="Relation type (canonical, alternate, source…).")
    url: str = Field(min_length=1)
    label: str | None = None
