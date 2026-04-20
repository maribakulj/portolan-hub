"""Error taxonomy shared across the core.

Plugins raise these so the federation engine can classify failures
uniformly. Each error carries a stable `code` usable in logs and in the
uniform API error response.
"""

from __future__ import annotations


class PortolanError(Exception):
    """Base class for all Portolan-raised errors."""

    code: str = "portolan_error"


class ManifestError(PortolanError):
    """The plugin manifest is missing, malformed, or incompatible."""

    code = "manifest_error"


class PluginLoadError(PortolanError):
    """A plugin was discovered but could not be loaded (import error, bad entry point…)."""

    code = "plugin_load_error"


class SourceUnavailable(PortolanError):
    """A source did not respond or timed out."""

    code = "source_unavailable"


class AuthRequired(PortolanError):
    """A source requires credentials we don't have."""

    code = "auth_required"


class QuotaExceeded(PortolanError):
    """A source signaled rate limiting or quota exhaustion."""

    code = "quota_exceeded"


class InvalidQuery(PortolanError):
    """The query cannot be expressed against this source."""

    code = "invalid_query"


class ParseError(PortolanError):
    """The source responded but the payload could not be parsed into the pivot."""

    code = "parse_error"
