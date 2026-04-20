"""Core domain models and plugin runtime for Portolan Hub."""

from portolan_core.connector import Connector, HealthStatus
from portolan_core.errors import (
    AuthRequired,
    InvalidQuery,
    ManifestError,
    ParseError,
    PluginLoadError,
    PortolanError,
    QuotaExceeded,
    SourceUnavailable,
)
from portolan_core.manifest import Manifest, load_manifest, manifest_json_schema
from portolan_core.models import (
    Agent,
    AgentRole,
    AuthScheme,
    Capability,
    Concept,
    Coverage,
    DateFilter,
    Link,
    Media,
    MediaKind,
    Place,
    Provenance,
    Query,
    QueryFilters,
    RateLimit,
    Result,
    ResultType,
    Rights,
    RightsStatement,
    Source,
    SourceStatus,
    TemporalSpan,
    Transformation,
)
from portolan_core.plugins import (
    PluginLoader,
    load_plugins_from_directory,
    load_plugins_from_entry_points,
)
from portolan_core.registry import SourceRegistry

__version__ = "0.0.0"

__all__ = [
    "__version__",
    # connector
    "Connector",
    "HealthStatus",
    # errors
    "AuthRequired",
    "InvalidQuery",
    "ManifestError",
    "ParseError",
    "PluginLoadError",
    "PortolanError",
    "QuotaExceeded",
    "SourceUnavailable",
    # manifest
    "Manifest",
    "load_manifest",
    "manifest_json_schema",
    # models
    "Agent",
    "AgentRole",
    "AuthScheme",
    "Capability",
    "Concept",
    "Coverage",
    "DateFilter",
    "Link",
    "Media",
    "MediaKind",
    "Place",
    "Provenance",
    "Query",
    "QueryFilters",
    "RateLimit",
    "Result",
    "ResultType",
    "Rights",
    "RightsStatement",
    "Source",
    "SourceStatus",
    "TemporalSpan",
    "Transformation",
    # plugins
    "PluginLoader",
    "load_plugins_from_directory",
    "load_plugins_from_entry_points",
    # registry
    "SourceRegistry",
]
