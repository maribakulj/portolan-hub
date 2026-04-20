"""Unit tests for pivot and query models.

Property-based tests (hypothesis) exercise the invariants we care about:
the pivot must round-trip through JSON without loss, and filters must
refuse obviously invalid inputs.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from portolan_core import (
    Agent,
    AgentRole,
    Capability,
    DateFilter,
    Media,
    MediaKind,
    Place,
    Provenance,
    Query,
    QueryFilters,
    Result,
    ResultType,
    Rights,
    RightsStatement,
    Source,
)

# ---------- Source ----------


def test_source_id_must_be_kebab() -> None:
    with pytest.raises(ValidationError):
        Source(id="Bad Id", name="x", protocol="rest-json")


def test_source_has_capability_matches_registered() -> None:
    s = Source(
        id="demo",
        name="Demo",
        protocol="iiif-search",
        capabilities=[Capability.FULL_TEXT, Capability.IIIF_MANIFEST],
    )
    assert s.has_capability(Capability.FULL_TEXT)
    assert not s.has_capability(Capability.FACET_DATE)


# ---------- Query ----------


def test_date_filter_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        DateFilter()


def test_date_filter_accepts_single_bound() -> None:
    DateFilter(start="1500")
    DateFilter(end="1800")


def test_query_defaults_are_sensible() -> None:
    q = Query(intent="Moreau")
    assert q.limit == 20
    assert q.offset == 0
    assert q.timeout_ms == 10_000
    assert q.sources == []
    assert isinstance(q.filters, QueryFilters)


def test_query_rejects_huge_limit() -> None:
    with pytest.raises(ValidationError):
        Query(intent="x", limit=10_000)


# ---------- Pivot round-trip ----------


def _make_minimal_result() -> Result:
    return Result(
        id="urn:portolan:demo:1",
        source_id="demo",
        native_id="1",
        rights=Rights(),
        provenance=Provenance(source_id="demo", plugin_version="0.1.0"),
    )


def test_result_minimal_is_valid() -> None:
    r = _make_minimal_result()
    assert r.title is None
    assert r.rights.statement == RightsStatement.UNKNOWN


def test_result_rejects_missing_rights() -> None:
    with pytest.raises(ValidationError):
        Result(  # type: ignore[call-arg]
            id="urn:portolan:demo:1",
            source_id="demo",
            native_id="1",
            provenance=Provenance(source_id="demo", plugin_version="0.1.0"),
        )


def test_result_round_trips_via_json() -> None:
    original = Result(
        id="urn:portolan:demo:1",
        source_id="demo",
        native_id="1",
        type=ResultType.WORK,
        title="Portrait",
        creators=[Agent(name="Someone", role=AgentRole.CREATOR)],
        places=[Place(name="Paris", lat=48.85, lon=2.35)],
        media=[Media(kind=MediaKind.IIIF_MANIFEST, url="https://x/manifest")],
        rights=Rights(statement=RightsStatement.CC_BY),
        provenance=Provenance(
            source_id="demo",
            plugin_version="0.1.0",
            latency_ms=12,
            timestamp=datetime.now(UTC),
        ),
        extras={"source_specific": "value"},
    )
    dumped = original.model_dump_json()
    restored = Result.model_validate_json(dumped)
    assert restored == original


# ---------- Property-based: pivot accepts any reasonable title ----------


@given(title=st.text(min_size=1, max_size=200))
def test_result_accepts_arbitrary_titles(title: str) -> None:
    r = Result(
        id="urn:portolan:demo:1",
        source_id="demo",
        native_id="1",
        title=title.strip() or None,
        rights=Rights(),
        provenance=Provenance(source_id="demo", plugin_version="0.1.0"),
    )
    # We just need to confirm the model does not raise.
    assert r.source_id == "demo"


@given(
    lat=st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
    lon=st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
)
def test_place_accepts_any_valid_coordinate(lat: float, lon: float) -> None:
    p = Place(name="anywhere", lat=lat, lon=lon)
    assert p.lat == lat
    assert p.lon == lon


def test_place_rejects_out_of_range_coordinate() -> None:
    with pytest.raises(ValidationError):
        Place(name="x", lat=91.0, lon=0.0)
