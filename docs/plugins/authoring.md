# Plugin authoring

**Status**: placeholder. This guide is finalized in Sprint 6 once the
low-code DSL is stable.

The intent — from [ADR 0001](../adr/0001-choix-techniques-fondateurs.md):

- **Two paths** to ship a connector:
    1. **Declarative** — a YAML manifest is sufficient for REST/JSON,
       OAI-PMH and SRU-conformant sources.
    2. **Hybrid** — the manifest points to small Python hooks
       (`pre_request`, `post_parse`) that run in a restricted sandbox.
- **Versioned contract** — each plugin declares its `manifest_version` so
  the runtime can refuse incompatible plugins gracefully.
- **Test fixtures** — every plugin ships a set of VCR cassettes that CI
  replays, so schema drift is caught the morning it happens.

Example skeleton (will evolve):

```yaml
manifest_version: "1"
id: example-museum
name: "Example Museum Open API"
status: community
protocol: rest-json
base_url: https://api.example.org/v2
rate_limit: { rps: 2, burst: 5 }
capabilities: [full_text, pagination]
search:
  endpoint: /search
  method: GET
  params:
    q: "{{ query.text }}"
  response:
    items_path: "$.data.items"
    mapping:
      native_id: "$.id"
      title: "$.attributes.title"
      rights: "$.attributes.license"
```
