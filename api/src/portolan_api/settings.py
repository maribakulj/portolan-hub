"""Runtime configuration, loaded from environment variables.

See `.env.example` at the repo root for the full list of variables and
their intent. Each field below is prefixed `PORTOLAN_` in the environment.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PORTOLAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(
        default="INFO",
        description="Log verbosity. DEBUG | INFO | WARNING | ERROR.",
    )

    api_host: str = Field(
        default="127.0.0.1",
        description="Interface the API binds to. Use 0.0.0.0 inside containers.",
    )
    api_port: int = Field(
        default=8000,
        description="TCP port the API listens on.",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        description="Origins allowed to call the API from a browser.",
    )

    api_token: str = Field(
        default="dev-token-change-me",
        description=(
            "Static bearer token for MVP auth. Replace in production; OAuth2 arrives in V1.1."
        ),
    )

    contact_email: str = Field(
        default="contact@example.org",
        description=(
            "Contact address exposed in the User-Agent header so institutions "
            "can reach the operator if traffic becomes a concern."
        ),
    )

    redis_url: str | None = Field(
        default=None,
        description="Redis connection URL. Falls back to in-memory cache if unset.",
    )

    plugins_dir: str | None = Field(
        default=None,
        description="Optional directory scanned for local plugin manifests, in addition to entry points.",
    )


def get_settings() -> Settings:
    """Lazy-built settings instance.

    Kept as a function rather than a module-level singleton so tests can
    override via `app.dependency_overrides`.
    """
    return Settings()
