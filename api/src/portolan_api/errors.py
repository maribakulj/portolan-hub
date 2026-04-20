"""Uniform error responses.

FastAPI's default error shape mixes string details and validation errors;
we normalize it so every failure looks the same to clients and is easy to
log and test against.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger(__name__)


class ErrorDetail(BaseModel):
    code: str = Field(description="Stable machine-readable error code.")
    message: str = Field(description="Human-readable summary.")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured context (field names, offending value, etc.).",
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=f"http_{exc.status_code}",
                    message=str(exc.detail) if exc.detail else "HTTP error.",
                )
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="validation_error",
                    message="Request payload failed validation.",
                    details={"errors": exc.errors()},
                )
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="internal_error",
                    message="Unexpected server error.",
                )
            ).model_dump(),
        )
