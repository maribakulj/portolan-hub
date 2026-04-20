.PHONY: help install dev api console docs test lint format typecheck clean docker-build docker-up docker-down

# Default target: list available commands.
help:
	@echo "Portolan Hub — developer commands"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install all Python packages in editable mode (uses uv)"
	@echo ""
	@echo "Run:"
	@echo "  dev          Start full stack (API + Redis + console) via docker-compose"
	@echo "  api          Run the API only (uvicorn, auto-reload)"
	@echo "  console      Run the console only (vite dev server)"
	@echo "  docs         Serve docs on http://localhost:8001"
	@echo ""
	@echo "Quality:"
	@echo "  lint         Run ruff + format check"
	@echo "  format       Apply ruff format + autofix"
	@echo "  typecheck    Run mypy across packages"
	@echo "  test         Run pytest with coverage"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build all images"
	@echo "  docker-up    Start stack in background"
	@echo "  docker-down  Stop stack"
	@echo ""
	@echo "  clean        Remove caches and build artifacts"

install:
	uv sync --all-packages

dev: docker-up

api:
	uv run uvicorn portolan_api.main:app --reload --host 0.0.0.0 --port 8000

console:
	cd console && npm install && npm run dev

docs:
	uv run mkdocs serve -f docs/mkdocs.yml -a 0.0.0.0:8001

test:
	uv run pytest --cov --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

docker-build:
	docker compose build

docker-up:
	docker compose up -d
	@echo "API:     http://localhost:8000"
	@echo "Console: http://localhost:3000"
	@echo "Docs:    run 'make docs' on the host"

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
	rm -rf docs/site console/.svelte-kit console/build
