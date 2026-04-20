# portolan-api

HTTP API surfacing the Portolan Hub core to consumers (console, SDK, agents).

## Run locally

```bash
make api              # uvicorn auto-reload on :8000
# or
uv run uvicorn portolan_api.main:app --reload
```

## Endpoints (Sprint 0)

- `GET /health` — liveness probe.
- `GET /version` — build metadata.
- `GET /docs` — Swagger UI (OpenAPI 3.1).
- `GET /redoc` — ReDoc.

Sprint 3 adds `/sources`, `/queries`, `/queries/dry-run`.
