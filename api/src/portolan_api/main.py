"""FastAPI application factory.

Kept minimal in Sprint 0. Sprint 3 adds source and query routers, auth
dependency, rate limiting and cache wiring.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from portolan_api import __version__
from portolan_api.errors import register_error_handlers
from portolan_api.logging_config import configure_logging
from portolan_api.routers import meta
from portolan_api.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger(__name__)
    log.info("api_start", version=__version__, contact=str(settings.contact_email))
    try:
        yield
    finally:
        log.info("api_stop")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Portolan Hub API",
        description=(
            "Unified query layer for distributed heritage data sources.\n\n"
            "See https://github.com/maribakulj/portolan-hub for docs."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(meta.router)

    return app


app = create_app()
