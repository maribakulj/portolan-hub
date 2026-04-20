"""Source model: describes an institution / portal / endpoint."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from portolan_core.models.primitives import RightsStatement

_STRICT = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Capability(StrEnum):
    """What a source lets us do.

    This list is intentionally finite and stable. Sources that can do more
    exotic things describe them in `Source.notes` — a plugin should not
    invent new capability strings.
    """

    FULL_TEXT = "full_text"
    FACET_DATE = "facet_date"
    FACET_CREATOR = "facet_creator"
    FACET_PLACE = "facet_place"
    FACET_TYPE = "facet_type"
    FACET_LANGUAGE = "facet_language"
    IIIF_MANIFEST = "iiif_manifest"
    IIIF_IMAGE_API = "iiif_image_api"
    PAGINATION = "pagination"
    STREAMING = "streaming"


class AuthScheme(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class SourceStatus(StrEnum):
    """Lifecycle status of a source plugin."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    DEPRECATED = "deprecated"


class RateLimit(BaseModel):
    """Token-bucket shape. `rps` is the refill rate, `burst` the bucket size."""

    model_config = _STRICT

    rps: float = Field(default=1.0, gt=0, description="Sustained requests per second.")
    burst: int = Field(default=2, ge=1, description="Allowed short-term burst size.")


class Coverage(BaseModel):
    """Free-form description of what a source contains.

    Not machine-filterable — meant for human discovery in the console.
    """

    model_config = _STRICT

    description: str | None = None
    formats: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class Source(BaseModel):
    """Everything Portolan knows about an institution / endpoint.

    Mutable over time: `last_checked` is updated by the health subsystem.
    """

    model_config = _STRICT

    id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description="Stable, kebab-case identifier used in URLs and logs.",
    )
    name: str = Field(min_length=1, description="Human-readable name.")
    protocol: str = Field(
        min_length=1,
        description="iiif-search | oai-pmh | sru | rest-json | custom.",
    )
    maintainer: str | None = None
    status: SourceStatus = SourceStatus.COMMUNITY
    version: str = Field(
        default="0.0.0",
        description="Plugin version (semver). Not the source API version.",
    )
    base_url: str | None = None
    capabilities: list[Capability] = Field(default_factory=list)
    rate_limit: RateLimit = Field(default_factory=RateLimit)
    auth_scheme: AuthScheme = AuthScheme.NONE
    rights_default: RightsStatement = RightsStatement.UNKNOWN
    coverage: Coverage = Field(default_factory=Coverage)
    notes: str | None = None
    last_checked: datetime | None = None

    def has_capability(self, capability: Capability) -> bool:
        return capability in self.capabilities
