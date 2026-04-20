"""Manifest parsing and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from portolan_core import (
    Capability,
    ManifestError,
    RightsStatement,
    SourceStatus,
    load_manifest,
    manifest_json_schema,
)

VALID = """
manifest_version: "1"
id: demo
name: "Demo"
protocol: iiif-search
base_url: "https://example.org/search"
capabilities: [full_text, pagination]
rights_default: CC0
rate_limit: {rps: 2.0, burst: 5}
entry_point: "connector:DemoConnector"
"""


def test_load_manifest_parses_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(VALID, encoding="utf-8")
    m = load_manifest(path)
    assert m.id == "demo"
    assert m.status == SourceStatus.COMMUNITY
    assert Capability.FULL_TEXT in m.capabilities
    assert m.rights_default == RightsStatement.CC0

    src = m.to_source()
    assert src.id == "demo"
    assert src.has_capability(Capability.PAGINATION)


def test_load_manifest_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="not found"):
        load_manifest(tmp_path / "nope.yaml")


def test_load_manifest_rejects_bad_version(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        """
manifest_version: "99"
id: demo
name: "Demo"
protocol: x
entry_point: "m:C"
""",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError, match="unsupported manifest_version"):
        load_manifest(path)


def test_load_manifest_rejects_missing_entry_point(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        """
manifest_version: "1"
id: demo
name: "Demo"
protocol: x
""",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError, match="validation"):
        load_manifest(path)


def test_load_manifest_rejects_bad_yaml(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text("this: is: not: yaml: [unterminated", encoding="utf-8")
    with pytest.raises(ManifestError, match="invalid YAML"):
        load_manifest(path)


def test_manifest_json_schema_has_expected_fields() -> None:
    schema = manifest_json_schema()
    properties = set(schema.get("properties", {}))
    assert {"id", "name", "protocol", "entry_point", "manifest_version"}.issubset(properties)
