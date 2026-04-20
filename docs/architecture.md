# Architecture overview

Portolan Hub is a **monolithic modular** Python application that exposes
a stable REST API, loads heritage connectors as plugins, and fans out
queries in parallel. See [ADR 0001](adr/0001-choix-techniques-fondateurs.md)
for why this shape was chosen over microservices.

## High-level diagram

```
                         ┌──────────────────────────────┐
                         │        Console web           │
                         │ (explorer, composer, viewer) │
                         └──────────────┬───────────────┘
                                        │ HTTPS
                         ┌──────────────▼───────────────┐
   SDK Python ───────────►                              │
   CLI        ───────────►      API unifiée (REST)      │
   Agents MCP ───────────►                              │
   (V2)                   └──────────────┬───────────────┘
                                         │
                         ┌───────────────▼────────────────┐
                         │    Noyau Portolan              │
                         │  • Registry des sources        │
                         │  • Fédérateur (async)          │
                         │  • Normaliseur vers pivot      │
                         │  • Traçabilité (provenance)    │
                         │  • Cache + politesse           │
                         └───────────────┬────────────────┘
                                         │
           ┌──────────────┬───────────────┼───────────────┬─────────────┐
           ▼              ▼               ▼               ▼             ▼
      [Plugin          [Plugin         [Plugin         [Plugin      [Plugin
       Gallica]        British Lib]   Bodleian]       Europeana]    IIIF gen.]
```

## Packages

| Path | Purpose | Sprint |
|--|--|--|
| `core/` | Domain models (`Source`, `Query`, `Result`, `Provenance`), plugin runtime, federation engine, normalization. | S1–S2 |
| `api/` | FastAPI surface exposing the core over HTTP. | S0–S3 |
| `sdk/` | Python client + `portolan` CLI. | S4 |
| `plugins/` | Reference connectors (echo, IIIF, OAI-PMH, SRU, Gallica, …). | S1 onward |
| `console/` | SvelteKit web UI. | S0 (placeholder) → S5 |
| `docs/` | MkDocs site (this site). | S0 |
| `ops/` | Dashboards, Prometheus rules, runbooks. | S7 |

## Three objects

- **Source** — an institution or portal, its protocol, its capabilities, its limits, its rights, its coverage. Registered via a plugin.
- **Query** — a structured research intent (text, date range, creator, type…), targeting one or many sources.
- **Result** — a normalized entity with a minimal pivot model, its provenance, its media (notably IIIF), its rights, and an `extras` bag that preserves source richness.

The [project README](../README.md) details each field of the pivot and
the plugin manifest.
