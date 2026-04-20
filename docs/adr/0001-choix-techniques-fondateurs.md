# ADR 0001 — Choix techniques fondateurs

- **Status**: accepted
- **Date**: 2026-04-20
- **Deciders**: équipe cœur Portolan Hub

## Context

Portolan Hub est une couche d'interopérabilité pour données patrimoniales
distribuées. Les contraintes initiales :

- Équipe petite (2–4 personnes en V1).
- Public cible technique (chercheurs DH, développeurs institutionnels) → Python est la lingua franca.
- Protocoles hétérogènes à absorber (OAI-PMH, SRU, IIIF, REST, parfois SPARQL).
- Exigence de traçabilité (provenance W3C PROV-like, citabilité académique).
- Besoin d'un modèle de plugin qui soit à la fois **accessible** (manifeste déclaratif) et **extensible** (échappatoire Python pour les cas tordus).
- Timeline V1 serrée : 8 sprints de 2 semaines.

## Decision

Nous adoptons les choix suivants pour toute la V1 :

1. **Langage backend : Python 3.12+**. Ecosystème patrimonial (pyoai, rdflib, IIIF tools, pandas, Jupyter) déjà en Python. Coût de recrutement minimal dans le public cible.
2. **Framework HTTP : FastAPI + Pydantic v2**. Génération OpenAPI automatique, validation typée, async natif.
3. **Runtime async : httpx + anyio**. Parallélisation du fan-out vers les sources sans threads.
4. **Packaging : uv workspace**. Mono-repo avec `core`, `api`, `sdk` comme paquets distincts, versions indépendantes.
5. **Frontend console : SvelteKit**. Bundle léger, DX correcte, suffisant pour les vues V1. Next.js/React réévalué si besoin d'un écosystème de composants en V2.
6. **Persistance V1 : SQLite (+ Litestream si déploiement continu)**. Postgres réservé à V1.1 si le volume ou la concurrence l'exigent.
7. **Cache : Redis**. Standard, token-bucket natif, survit aux redémarrages.
8. **Plugins : manifeste YAML déclaratif + hooks Python optionnels**. Chargement via `entry_points`, sandbox d'exécution pour les hooks (S6).
9. **Modèle pivot minimal + `extras` typé**. Pas d'ontologie universelle (ni EDM, ni LinkedArt complet) en V1.
10. **Architecture : monolithe modulaire**. Pas de microservices tant que la preuve du besoin n'est pas faite.
11. **Observabilité : Prometheus + OpenTelemetry**. Standards, non verrouillés.
12. **Licence et gouvernance : open source, plugins versionnés, mainteneurs déclarés**.

## Alternatives considered

- **Go** pour le backend : performance, binaire unique. Rejeté : faible adoption dans le public DH, peu de libs patrimoniales.
- **Node/TypeScript** de bout en bout : cohérence front/back. Rejeté : SDK Python est demandé par le public cible, l'écosystème data Python est supérieur.
- **Django** : batteries-included mais ORM synchrone, overkill pour une API stateless.
- **Microservices dès le départ** (query-service, plugin-runtime, normalizer) : rejeté, trop de surface opérationnelle pour une équipe de 4.
- **EDM ou LinkedArt complet comme pivot** : rejeté en V1. Couverture complète = 18 mois. On commence par un noyau de 10 champs + `extras`.
- **Elasticsearch comme couche de requêtage** : rejeté en V1. Notre valeur est la **fédération live**, pas l'index. L'index devient optionnel en V2 (axe 7 du README).
- **LLM en cœur de produit** (requêtes en langage naturel par défaut) : rejeté en V1. Non déterministe, coûteux, détourne l'attention du vrai problème (la fédération). Revient en V2 comme option.

## Consequences

### Positive

- L'équipe peut recruter facilement (Python + FastAPI + SvelteKit sont mainstream).
- Le fan-out async est naturel et performant.
- Le SDK Python attire immédiatement le public DH.
- Le pivot minimal + `extras` garantit une compatibilité ascendante confortable.
- La CI reste rapide (pas de builds lourds).

### Negative

- Python async est moins performant que Go/Rust sur des fan-outs massifs (100+ sources en parallèle). Accepté : V1 cible 10–20 sources max en simultané. Réévalué en V2.
- Pas de SDK JS/TS en V1 — les dévs frontend devront consommer l'API REST directement. Prévu en V2.
- Le pivot minimal déçoit les institutions qui veulent pousser du LinkedArt complet. Mitigation : `extras` typé par source + ADR de politique d'évolution du pivot (à rédiger en S1).

### Follow-ups

- ADR 0002 (S1) : politique d'évolution du pivot.
- ADR 0003 (S2) : stratégie de dédoublonnage.
- ADR 0004 (S3) : politique de cache et d'invalidation.
- ADR 0005 (S6) : sandbox pour hooks Python de plugins.
- ADR 0006 (V1.1) : migration SQLite → Postgres, si nécessaire.
