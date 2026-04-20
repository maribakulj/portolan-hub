"""Query model: a research intent routed to one or many sources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from portolan_core.models.result import ResultType

_STRICT = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DateFilter(BaseModel):
    """Inclusive date range.

    `start` and `end` are strings because heritage dates are often imprecise
    or expressed in EDTF ("16xx", "circa 1520"). We keep them opaque here
    and let individual connectors translate to their backend's query DSL.
    """

    model_config = _STRICT

    start: str | None = None
    end: str | None = None

    @model_validator(mode="after")
    def _at_least_one_bound(self) -> DateFilter:
        if self.start is None and self.end is None:
            raise ValueError("date filter needs at least a start or an end")
        return self


class QueryFilters(BaseModel):
    """Structured filters that layer on top of the free-text intent."""

    model_config = _STRICT

    dates: DateFilter | None = None
    creators: list[str] = Field(default_factory=list)
    types: list[ResultType] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class Query(BaseModel):
    """A research intent, plus routing and limits.

    `sources` is a list of source ids; empty means "fan out to all
    registered sources" and is resolved at dispatch time.
    """

    model_config = _STRICT

    intent: str = Field(
        default="",
        description=(
            "Free-text search intent. Plugins map it to their native syntax. "
            "Empty is valid when structured filters carry the whole query."
        ),
    )
    filters: QueryFilters = Field(default_factory=QueryFilters)
    sources: list[str] = Field(
        default_factory=list,
        description="Target source ids. Empty = all registered sources.",
    )
    limit: int = Field(default=20, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    timeout_ms: int = Field(default=10_000, ge=100, le=120_000)
