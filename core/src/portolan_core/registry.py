"""In-memory registry of loaded connectors.

Swappable with a persistent backend later (if the "living directory of
sources" in the README's axis 9 pushes us that way), but not in V1.
"""

from __future__ import annotations

from portolan_core.connector import Connector
from portolan_core.models import Capability, Source


class SourceRegistry:
    """Holds the active set of connectors keyed by source id."""

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        """Register or replace a connector by its source id."""
        self._connectors[connector.source.id] = connector

    def unregister(self, source_id: str) -> None:
        self._connectors.pop(source_id, None)

    def get(self, source_id: str) -> Connector | None:
        return self._connectors.get(source_id)

    def require(self, source_id: str) -> Connector:
        """Like `get` but raises `KeyError` when missing.

        Use from API handlers where a missing source should 404, not 500.
        """
        try:
            return self._connectors[source_id]
        except KeyError:
            raise KeyError(f"no source registered with id {source_id!r}") from None

    def list_sources(self) -> list[Source]:
        """Return every registered `Source` sorted by id (stable ordering)."""
        return sorted((c.source for c in self._connectors.values()), key=lambda s: s.id)

    def filter_by_capability(self, capability: Capability) -> list[Source]:
        return [s for s in self.list_sources() if s.has_capability(capability)]

    def __len__(self) -> int:
        return len(self._connectors)

    def __contains__(self, source_id: object) -> bool:
        return isinstance(source_id, str) and source_id in self._connectors
