# portolan-core

Core domain models and plugin runtime for Portolan Hub.

This package is intentionally empty during Sprint 0. Sprint 1 populates it with:

- `Source`, `Query`, `Result`, `Provenance` Pydantic models
- The `Connector` abstract base class
- The plugin manifest loader (YAML + JSON Schema validation)
- An in-memory source registry

See [ROADMAP.md](../ROADMAP.md) and [docs/adr/0001-choix-techniques-fondateurs.md](../docs/adr/0001-choix-techniques-fondateurs.md).
