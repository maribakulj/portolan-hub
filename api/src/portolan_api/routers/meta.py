"""Meta endpoints: health and version.

These are the only endpoints exposed in Sprint 0. They exist so the
docker-compose healthcheck, CI smoke tests, and the console placeholder
have something stable to hit.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from portolan_api import __version__

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str = Field(description="`ok` when the process is alive.")
    timestamp: datetime = Field(description="Server time in UTC.")


class VersionResponse(BaseModel):
    name: str = Field(description="Product name.")
    version: str = Field(description="API package version.")
    api: str = Field(description="API contract version (semver of the HTTP surface).")


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(UTC))


@router.get("/version", response_model=VersionResponse, summary="Build metadata")
async def version() -> VersionResponse:
    return VersionResponse(
        name="portolan-hub",
        version=__version__,
        api="0",
    )
