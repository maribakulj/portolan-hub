"""Plugin manifest: the YAML contract between a plugin and the runtime.

A manifest describes a single source + how to instantiate its connector.
The loader reads the YAML, validates it against this schema, derives a
`Source` object, and dynamically imports the connector class pointed at
by `entry_point`.

Declarative plugins (Sprint 6) will add optional `search` and `response`
sub-sections. For Sprint 1 every plugin is code-backed and the `entry_point`
is mandatory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from portolan_core.errors import ManifestError
from portolan_core.models.primitives import RightsStatement
from portolan_core.models.source import (
    AuthScheme,
    Capability,
    Coverage,
    RateLimit,
    Source,
    SourceStatus,
)

SUPPORTED_MANIFEST_VERSIONS = {"1"}

_STRICT = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Manifest(BaseModel):
    """The YAML-backed plugin manifest.

    Mirrors `Source` but adds runtime-only fields (`manifest_version`,
    `entry_point`) and forbids `last_checked` (which is populated at
    runtime, not declared).
    """

    model_config = _STRICT

    manifest_version: Literal["1"] = Field(description="Manifest schema version.")

    id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    protocol: str = Field(min_length=1)
    maintainer: str | None = None
    status: SourceStatus = SourceStatus.COMMUNITY
    version: str = Field(default="0.0.0")
    base_url: str | None = None

    capabilities: list[Capability] = Field(default_factory=list)
    rate_limit: RateLimit = Field(default_factory=RateLimit)
    auth_scheme: AuthScheme = AuthScheme.NONE
    rights_default: RightsStatement = RightsStatement.UNKNOWN
    coverage: Coverage = Field(default_factory=Coverage)
    notes: str | None = None

    entry_point: str = Field(
        min_length=1,
        description=(
            "Python dotted path to the Connector class, e.g. "
            "`my_plugin.connector:MyConnector`. Required in Sprint 1 — the "
            "Sprint 6 declarative DSL will make this optional."
        ),
        pattern=r"^[A-Za-z_][\w\.]*:[A-Za-z_]\w*$",
    )

    def to_source(self) -> Source:
        """Project the manifest onto the runtime Source model."""
        return Source(
            id=self.id,
            name=self.name,
            protocol=self.protocol,
            maintainer=self.maintainer,
            status=self.status,
            version=self.version,
            base_url=self.base_url,
            capabilities=self.capabilities,
            rate_limit=self.rate_limit,
            auth_scheme=self.auth_scheme,
            rights_default=self.rights_default,
            coverage=self.coverage,
            notes=self.notes,
        )


def load_manifest(path: Path) -> Manifest:
    """Read and validate a manifest file.

    Raises `ManifestError` with a human-friendly message on any failure
    (missing file, bad YAML, schema violation).
    """
    if not path.is_file():
        raise ManifestError(f"manifest not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ManifestError(f"manifest {path} must be a YAML mapping, got {type(raw).__name__}")

    version = raw.get("manifest_version")
    if version not in SUPPORTED_MANIFEST_VERSIONS:
        raise ManifestError(
            f"unsupported manifest_version {version!r} in {path}; "
            f"supported: {sorted(SUPPORTED_MANIFEST_VERSIONS)}"
        )

    try:
        return Manifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestError(f"manifest {path} failed validation:\n{exc}") from exc


def manifest_json_schema() -> dict[str, object]:
    """Return the JSON Schema for the manifest, for editor tooling."""
    return Manifest.model_json_schema()
