# Portolan Hub — Plan de sprints V1

Ce document décrit l'enchaînement complet des sprints pour livrer une V1 solide, démontrable et opérable en production par des équipes pilotes. Il suppose une équipe cœur de 2 à 4 personnes (un·e backend, un·e fullstack, un·e data/DH, un·e PM à temps partiel suffisent).

- **Cadence** : sprints de 2 semaines.
- **Durée totale V1** : 8 sprints, soit ≈ 4 mois.
- **Principe** : chaque sprint produit un livrable démontrable de bout en bout. Pas de "sprint infra pur" qui ne montre rien.
- **Critère de sortie V1** : 5 connecteurs officiels, API stable, SDK Python publié, console utilisable, 3 utilisateurs pilotes externes qui tournent des requêtes réelles.

---

## Sprint 0 — Fondations (semaine 1-2)

**Objectif** : un squelette de projet qui tourne, pas de logique métier.

Livrables :
- Mono-repo structuré (`core/`, `plugins/`, `api/`, `sdk/`, `console/`, `docs/`).
- Choix techniques actés et documentés :
  - Backend : Python 3.12 + FastAPI + Pydantic v2.
  - Runtime async : `httpx` + `anyio`.
  - Persistance V1 : SQLite (Litestream pour la réplication) → Postgres en V1.1 si besoin.
  - Cache : Redis (ou DiskCache en dev).
  - Frontend console : SvelteKit ou Next.js (choix selon équipe).
  - Packaging plugins : wheel Python + manifeste YAML.
- `docker-compose.yml` pour dev local (API + Redis + console).
- CI GitHub Actions : lint (`ruff`), type-check (`mypy` ou `pyright`), tests (`pytest`).
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, template d'issue/PR.
- ADR 0001 (Architecture Decision Record) : "Pourquoi Python, pourquoi un pivot minimal, pourquoi plugins déclaratifs".

**Démo de fin de sprint** : `make dev` lance la stack, un endpoint `/health` répond, la CI est verte.

**Risques** : sur-ingénierie prématurée. Contre-mesure : pas de k8s, pas de microservices, pas d'event bus. Un monolithe modulaire.

---

## Sprint 1 — Noyau Source / Query / Result (semaine 3-4)

**Objectif** : poser les trois objets-pivots et le contrat de plugin.

Livrables :
- Modèles Pydantic :
  - `Source` (id, nom, protocole, capabilities, rate_limit, auth_scheme, rights_default, last_checked).
  - `Query` (intent, filtres structurés, pagination, timeout, sources_cible).
  - `Result` (pivot model — cf. § Modèle pivot).
  - `Provenance` (source_id, plugin_version, query_sent, timestamp, transformations[]).
- Interface `Connector` (Python ABC) + spec du manifeste YAML.
- Loader de plugins (découverte via entry points `portolan.plugins`).
- Registry in-memory des sources enregistrées.
- **Un plugin de référence "echo"** (fixtures statiques, utilisé pour tests) + **un plugin IIIF Search API générique** comme premier cas réel.
- Tests unitaires sur le loader et le pivot.

**Démo** : `portolan sources list` affiche les 2 plugins, `portolan query "Gustave Moreau"` interroge le plugin IIIF et renvoie des résultats normalisés avec provenance.

**Points d'attention** :
- Ne PAS figer le pivot trop tôt. Commencer avec 10 champs durs et un `extras: dict`.
- Versionner le contrat de plugin dès le départ (`manifest_version: "1"`).

---

## Sprint 2 — Premiers connecteurs réels + moteur de fédération (semaine 5-6)

**Objectif** : prouver que l'abstraction tient face à trois protocoles très différents.

Livrables :
- **Connecteur OAI-PMH générique** (paramétrable via YAML : endpoint, metadataPrefix, sets).
- **Connecteur SRU générique** (Z39.50 moderne).
- **Connecteur Gallica (BnF)** : bâti sur SRU + IIIF, mais packagé comme plugin officiel.
- Moteur de fédération :
  - Dispatch parallèle avec `asyncio.gather`.
  - Timeout par source, budget global.
  - Gestion des erreurs isolée (une source qui plante ne casse pas la requête).
  - Agrégation + dédoublonnage naïf (par `identifier` ou hash de `title+creator+date`).
- Normalisation : chaque plugin produit des `Result` conformes au pivot.
- Trace de provenance complète sur chaque résultat.
- Fixtures VCR (`pytest-vcr`) capturant les réponses réelles pour tests reproductibles.

**Démo** : une requête unique renvoie des résultats fusionnés des 3 sources, avec provenance visible.

**Risques** : Gallica/OAI-PMH ont des quirks (resumption tokens, encodage Marc XML). Prévoir 20 % de buffer.

---

## Sprint 3 — API unifiée + cache + politesse (semaine 7-8)

**Objectif** : exposer le noyau via une API propre, et ne pas se faire bannir par les institutions.

Livrables :
- API REST FastAPI :
  - `GET /sources` (liste + capabilities).
  - `GET /sources/{id}` (détails, santé, dernière erreur).
  - `POST /queries` (lance une requête fédérée ; async ou sync selon taille).
  - `GET /queries/{id}` (résultats, statut, provenance).
  - `GET /queries/{id}/results?page=…` (pagination cursor-based).
  - `POST /queries/dry-run` → **plan d'exécution** (sources qui seront interrogées, estimation, auth manquante).
- OpenAPI 3.1 générée + Swagger UI.
- Cache Redis à deux niveaux :
  - Cache "réponse brute par source" (clé = hash de la requête sortante).
  - Cache "résultat normalisé" (invalidation par version de plugin).
- **Politesse envers les sources** :
  - `User-Agent: PortolanHub/1.0 (+contact)`.
  - Rate limit par source (token bucket, lu depuis le manifeste).
  - Backoff exponentiel sur 429 / 503.
  - Respect optionnel de `robots.txt` si pertinent.
- Auth basique : token porteur statique pour le MVP (OAuth2 en V1.1).
- Journalisation structurée (JSON logs) + `X-Portolan-Query-Id` sur toutes les requêtes.

**Démo** : `curl` vers l'API renvoie des résultats ; la doc Swagger est accessible ; le cache est visible dans les métriques.

---

## Sprint 4 — SDK Python + CLI (semaine 9-10)

**Objectif** : donner aux chercheurs et développeurs l'outil qu'ils attendent réellement.

Livrables :
- Paquet `portolan-sdk` publié sur PyPI (au moins en TestPyPI) :
  ```python
  from portolan import Client
  client = Client(base_url="…", token="…")
  results = client.query("saint Sébastien", sources=["gallica", "bl"]).stream()
  for r in results:
      print(r.title, r.iiif_manifest)
  ```
- Streaming itérable (ne charge pas tout en mémoire).
- Intégration Pandas/Polars : `results.to_dataframe()`.
- Intégration Jupyter : widget simple pour afficher un résultat avec miniature IIIF.
- CLI `portolan` (via `typer`) :
  - `portolan sources list|show|health`.
  - `portolan query "…" --sources gallica,bl --output csv`.
  - `portolan plugin install|list|test`.
- Documentation générée (MkDocs Material) avec tutoriels chercheur et développeur.

**Démo** : un notebook Jupyter fait 3 requêtes sur 3 sources et affiche une grille d'images IIIF.

---

## Sprint 5 — Console web V1 (semaine 11-12)

**Objectif** : permettre à un non-développeur de découvrir, tester et exporter.

Livrables :
- Pages :
  - **Explorateur de sources** : liste, filtres, fiche détaillée (capabilities, santé, licence, couverture).
  - **Composeur de requêtes** : formulaire avec complétion, preview JSON, bouton dry-run.
  - **Résultats** : liste + grille d'images + fiche détail.
  - **Viewer IIIF** intégré (Mirador ou Clover).
  - **Tableau de bord santé** : dernière exécution, taux d'erreur, temps de réponse par source.
- Export : JSON, CSV, collection IIIF (Presentation API).
- Historique des requêtes par utilisateur (local storage + backend).
- Authentification simple (magic link ou token collé).
- Mode sombre, i18n FR/EN dès le départ.

**Démo** : un curateur non-développeur lance une requête, consulte les images, exporte un CSV.

---

## Sprint 6 — Créateur de connecteurs low-code (semaine 13-14)

**Objectif** : démontrer que rajouter un nouveau connecteur ne demande pas de coder Python.

Livrables :
- **DSL YAML déclaratif** pour connecteurs simples (REST JSON ou OAI/SRU standards) :
  ```yaml
  id: example-museum
  name: "Example Museum Open API"
  protocol: rest-json
  base_url: https://api.example.org/v2
  auth: none
  rate_limit: { rps: 2, burst: 5 }
  search:
    endpoint: /search
    method: GET
    params:
      q: "{{ query.text }}"
      page: "{{ query.page }}"
    response:
      items_path: "$.data.items"
      total_path: "$.data.total"
      mapping:
        id: "$.id"
        title: "$.attributes.title"
        creator: "$.attributes.author"
        date: "$.attributes.date"
        iiif_manifest: "$.attributes.iiif.manifest"
        rights: "$.attributes.license"
  capabilities: [full_text, pagination]
  ```
- UI dans la console :
  - Éditeur YAML avec validation schéma en direct.
  - Test endpoint ("essayer cette requête") avec réponse brute + mapping appliqué côte-à-côte.
  - Export en plugin packagé.
- Échappatoire Python : si un connecteur nécessite du code, un hook `pre_request` / `post_parse` peut pointer vers une fonction Python signalée dans le manifeste.
- **Sandbox** pour l'exécution des hooks Python (restriction des imports, pas d'accès fichier/réseau hors httpx client fourni).

**Démo** : en séance, créer un nouveau connecteur pour une API ouverte (ex. Rijksmuseum, Smithsonian Open Access) en moins de 30 minutes, sans quitter la console.

**Note** : éviter d'appeler ça "no-code" dans la doc publique. On vend "low-code" ou "declarative connectors". C'est plus honnête et plus vendeur auprès du public technique.

---

## Sprint 7 — Observabilité, droits, hardening (semaine 15-16)

**Objectif** : passer de "ça marche en démo" à "on peut brancher des utilisateurs pilotes".

Livrables :
- **Observabilité** :
  - Métriques Prometheus (`portolan_query_duration_seconds`, `portolan_source_errors_total`, etc.).
  - Traces OpenTelemetry (une requête fédérée = un trace, une span par source).
  - Dashboard Grafana d'exemple livré.
- **Droits et licences** :
  - Mapping vers RightsStatements.org + Creative Commons.
  - Champ `rights` obligatoire dans le pivot (avec valeur `unknown` autorisée mais signalée).
  - Filtre "réutilisable commercialement" dans la console.
- **Sécurité** :
  - Revue des entrées (injection sur les params YAML, SSRF sur les URLs de plugins).
  - Rate limit côté API (par token).
  - Secrets plugins chiffrés au repos.
  - `security-review` effectuée et consignée.
- **Registre des plugins officiels** :
  - 5 connecteurs validés : Gallica (BnF), British Library (via IIIF/SRU), Bodleian (IIIF), Europeana, un IIIF générique.
  - Chaque plugin a un mainteneur désigné et un test de bout en bout nocturne.
- **Documentation finale** : guide chercheur, guide développeur, guide auteur de plugin, guide opérations.
- **Tag `v1.0.0`** + release notes + annonce.

**Démo** : un dashboard Grafana montre 48 h de trafic pilote ; une requête est tracée de bout en bout ; un filtre par licence change les résultats.

---

## Vue d'ensemble des dépendances

```
S0 ──► S1 ──► S2 ──► S3 ──► S4 ──► S5 ──► S6 ──► S7
              │              │              │
              └─ plugins ──┬─┘              │
                          parallèle         │
              fixtures VCR stabilisées      │
                                            │
                    (droits & observabilité en fin de course
                     car ils dépendent d'un système qui tourne)
```

Sprints 4 et 5 peuvent être partiellement parallélisés si l'équipe a un profil backend + un profil frontend dédié.

---

## Jalons externes

- **Fin S2** : première démo publique courte (conférence DH, mailing-list IIIF).
- **Fin S4** : SDK sur PyPI → recruter 3 utilisateurs pilotes chercheurs.
- **Fin S6** : invitation d'une institution à créer son propre connecteur en live.
- **Fin S7** : release V1 publique, billet de blog, démo enregistrée.

---

## Ce qui n'est délibérément PAS dans la V1

Pour tenir 4 mois, on reporte explicitement :

- Alignement d'entités (Wikidata/VIAF/Getty).
- Recherche sémantique / embeddings.
- Marketplace de plugins avec notation communautaire.
- Mode multi-tenant hébergé.
- Collaboration temps réel.
- Serveur MCP / mode agent.
- Similarité visuelle.
- Enrichissement automatique.
- Webhooks / abonnements à des requêtes.
- UI de workflow drag-and-drop (on se limite au DSL YAML côté connecteur).

Tout ceci est décrit dans la section "V2 ambitieuse" du README.

---

## Critères de succès V1

| Critère | Cible |
|--|--|
| Connecteurs officiels | ≥ 5 |
| Connecteurs communautaires | ≥ 2 |
| Temps pour créer un connecteur simple | ≤ 30 min |
| Temps de réponse médian (1 source) | < 800 ms hors source |
| Taux de réussite requête fédérée (5 sources) | ≥ 95 % |
| Utilisateurs pilotes actifs | ≥ 3 équipes externes |
| Requêtes exécutées / semaine après lancement | ≥ 500 |
| Couverture de tests | ≥ 80 % sur le noyau |

---

## Principaux risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|--|--|--|--|
| Une API institutionnelle change et casse un connecteur | Élevée | Moyen | Tests nocturnes VCR + monitoring + plugin versionné |
| Le pivot commun trop pauvre | Moyenne | Élevé | `extras` typé par source dès le départ + revue à S3 |
| Le DSL YAML ne couvre pas assez de cas | Moyenne | Moyen | Échappatoire Python signée dès S6 |
| Institution nous bannit (trafic) | Faible | Élevé | Politesse, contact préalable, cache agressif |
| Scope creep vers V2 pendant la V1 | Élevée | Élevé | Ce document, relu en début de chaque sprint |
