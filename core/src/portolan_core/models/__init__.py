"""Pivot domain models.

The pivot is deliberately minimal: 10 hard fields on `Result` plus an
`extras` bag that lets plugins preserve source-specific richness. See
ADR 0001 and the README's "Modèle pivot" section for the rationale.
"""

from portolan_core.models.primitives import (
    Agent,
    AgentRole,
    Concept,
    Link,
    Media,
    MediaKind,
    Place,
    Rights,
    RightsStatement,
    TemporalSpan,
)
from portolan_core.models.query import (
    DateFilter,
    Query,
    QueryFilters,
)
from portolan_core.models.result import (
    Provenance,
    Result,
    ResultType,
    Transformation,
)
from portolan_core.models.source import (
    AuthScheme,
    Capability,
    Coverage,
    RateLimit,
    Source,
    SourceStatus,
)

__all__ = [
    # primitives
    "Agent",
    "AgentRole",
    "Concept",
    "Link",
    "Media",
    "MediaKind",
    "Place",
    "Rights",
    "RightsStatement",
    "TemporalSpan",
    # query
    "DateFilter",
    "Query",
    "QueryFilters",
    # result
    "Provenance",
    "Result",
    "ResultType",
    "Transformation",
    # source
    "AuthScheme",
    "Capability",
    "Coverage",
    "RateLimit",
    "Source",
    "SourceStatus",
]
