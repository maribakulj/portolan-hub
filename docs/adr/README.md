# Architecture Decision Records

ADRs capture decisions that are hard to reverse or that shape the project
for a long time. The format here is lightweight — inspired by Michael
Nygard's original template.

## Index

- [0001 — Choix techniques fondateurs](0001-choix-techniques-fondateurs.md)
- [Template](template.md)

## Lifecycle

- `proposed` — open for discussion.
- `accepted` — merged, in effect.
- `deprecated` — superseded (link to replacement).
- `rejected` — considered, not adopted (keep for memory).

## When to write an ADR

- Adding a language, framework, or runtime.
- Choosing a persistence layer or cache.
- Changing the plugin contract.
- Changing the pivot model in ways that affect clients.
- Introducing an external service or third-party dependency with ongoing cost.

Small local refactors do not warrant an ADR.
