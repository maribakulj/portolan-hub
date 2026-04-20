"""Connector abstract base class.

A Connector is the runtime object that the loader instantiates from a
plugin manifest. Connectors are async-first; their `search` method yields
Results lazily so callers can stream.

Connectors MUST NOT import HTTP libraries at module level without a
fallback path — the loader may refuse to activate a plugin whose runtime
dependencies are missing, but it does so on instantiation, not on import.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

from portolan_core.models import Query, Result, Source


@dataclass
class HealthStatus:
    """Lightweight health check payload.

    Sprint 7 extends this with quota info and last-error details.
    """

    ok: bool
    message: str | None = None
    checked_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.checked_at is None:
            self.checked_at = datetime.now(UTC)


class Connector(ABC):
    """Async interface every plugin implements.

    `source` is populated by the loader from the plugin manifest before
    the connector is first used. Subclasses should not mutate it.
    """

    source: Source

    def __init__(self, source: Source) -> None:
        self.source = source

    @abstractmethod
    def search(self, query: Query) -> AsyncIterator[Result]:
        """Translate `query` to the source's native format and yield Results.

        Must complete within `query.timeout_ms`. Must not raise on an empty
        result set — return an empty iterator instead. Must raise one of
        the typed errors from `portolan_core.errors` on failure.

        Typed as returning an ``AsyncIterator`` (not ``AsyncIterable``) so
        implementations can be plain ``async def`` generators.
        """
        raise NotImplementedError

    async def health(self) -> HealthStatus:
        """Return the source's current health.

        Default implementation assumes the source is healthy; plugins may
        override to issue a cheap probe (HEAD request, metadata query…).
        """
        return HealthStatus(ok=True, message="default health check")
