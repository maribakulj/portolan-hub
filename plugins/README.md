# plugins/

Home of bundled reference plugins. Populated from Sprint 1 onward.

Planned layout (each directory is an installable package or a standalone manifest):

```
plugins/
├── echo/                 # Sprint 1 — fixture-based plugin, used in tests
├── iiif-generic/         # Sprint 1 — IIIF Search API (v1) connector
├── oai-pmh-generic/      # Sprint 2 — generic OAI-PMH connector
├── sru-generic/          # Sprint 2 — generic SRU connector
├── gallica/              # Sprint 2 — official BnF Gallica plugin
├── british-library/      # Sprint 7 — official BL plugin
├── europeana/            # Sprint 7 — official Europeana plugin
└── bodleian/             # Sprint 7 — official Bodleian plugin
```

Authoring guide: `docs/plugins/authoring.md` (written in Sprint 6 when the
low-code DSL is finalized).
