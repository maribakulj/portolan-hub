# Portolan Hub

> Un poste de pilotage unifié pour interroger, harmoniser et exploiter des données patrimoniales distribuées.

**Portolan Hub** est une couche d'interopérabilité patrimoniale scriptable. Elle permet à un utilisateur ou à un script de lancer, depuis une seule interface, des requêtes vers de nombreuses institutions culturelles, malgré l'hétérogénéité de leurs API, formats, protocoles et modèles de données.

Le produit joue quatre rôles :

1. **Annuaire vivant** des sources patrimoniales (capacités, limites, droits, couverture, fraîcheur).
2. **Orchestrateur** de requêtes fédérées (traduction, délais, quotas, pagination, authentification).
3. **Couche de normalisation** vers un modèle pivot commun.
4. **Surface d'exploitation** : console humaine + API unifiée + SDK Python.

La promesse centrale : **chercher partout, comprendre ce qui revient, réutiliser immédiatement**.

---

## Table des matières

- [Positionnement](#positionnement)
- [Architecture d'ensemble](#architecture-densemble)
- [Concepts](#concepts)
- [Modèle pivot](#modèle-pivot)
- [Modèle de plugin](#modèle-de-plugin)
- [Démarrage rapide](#démarrage-rapide)
- [SDK Python](#sdk-python)
- [Console web](#console-web)
- [Créer un connecteur](#créer-un-connecteur)
- [Gouvernance des plugins](#gouvernance-des-plugins)
- [Feuille de route V1](#feuille-de-route-v1)
- [V2 ambitieuse — pistes d'amélioration](#v2-ambitieuse--pistes-damélioration)
- [Non-objectifs](#non-objectifs)
- [Contribuer](#contribuer)
- [Licence](#licence)

---

## Positionnement

Portolan Hub se situe à l'intersection de quatre mondes :

- **API gateway** (abstraction d'API hétérogènes).
- **Federated search** (recherche distribuée, pas d'index central obligatoire).
- **Metadata interoperability layer** (pivot commun, provenance, traçabilité).
- **Research / curation workstation** (console, notebooks, exports, workflows).

Cela le rend différent d'un agrégateur fermé (type portail unique) ou d'un moteur de recherche web généraliste. Il ne copie pas systématiquement les données, n'impose pas une ontologie universelle, et n'essaie pas de remplacer les infrastructures des institutions.

### Ce que Portolan N'EST PAS

- Un agrégateur statique qui moissonne et fige les données.
- Un moteur de recherche web généraliste.
- Un DAM, un SIGB, un CMS d'institution.
- Un entrepôt central qui copie tout.
- Un LLM « magique » qui remplace les métadonnées.

Portolan agit **au-dessus** des systèmes existants, comme une couche de médiation, de traduction et d'exploitation.

---

## Architecture d'ensemble

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
                         │                                │
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
           │              │               │               │             │
           ▼              ▼               ▼               ▼             ▼
        SRU+IIIF       IIIF/SRU        IIIF          OAI-PMH        IIIF v2/v3
```

Le noyau est un **monolithe modulaire** en Python. Les plugins sont chargés dynamiquement via `entry_points`. Aucun microservice n'est introduit avant d'en avoir la preuve du besoin.

---

## Concepts

Trois objets structurent l'ensemble du système.

### Source

Une institution ou un portail avec son protocole, ses capacités, ses limites, ses droits. Enregistrée dans le registre via un plugin.

### Query

Une intention documentaire exprimée de façon structurée (texte, filtres par date, créateur, lieu, type, etc.), cible un ou plusieurs sources, et porte ses propres paramètres (timeout, budget, pagination).

### Result

Une entité documentaire normalisée selon le [modèle pivot](#modèle-pivot), avec sa **provenance** (source, requête envoyée, version du plugin, transformations), ses médias (notamment IIIF), ses droits et son identifiant stable.

---

## Modèle pivot

Le pivot est **volontairement minimal** pour rester stable dans le temps. Chaque connecteur peut ajouter des champs sources via un `extras` typé.

```python
class Result:
    id: str                  # identifiant stable Portolan (URN)
    source_id: str           # plugin source
    native_id: str           # identifiant dans la source d'origine
    type: ResultType         # work | object | manifest | person | place | set
    title: str | None
    creators: list[Agent]
    dates: list[TemporalSpan]
    places: list[Place]
    subjects: list[Concept]
    languages: list[str]
    description: str | None
    media: list[Media]       # images, IIIF manifest, video, audio, 3D
    rights: Rights           # mapping RightsStatements.org + CC
    links: list[Link]        # URL canonique, autres représentations
    provenance: Provenance
    extras: dict[str, Any]   # champs non mappés, propres à la source
```

**Règles de conception** :

- Pas d'ontologie universelle imposée. Le pivot n'essaie pas d'être EDM ni LinkedArt complets.
- `extras` est toléré et encouragé pour préserver la richesse source.
- Tous les champs structurés sont optionnels sauf `id`, `source_id`, `native_id`, `provenance`, `rights`.
- `rights` peut valoir `unknown` mais ne peut pas être absent — c'est un signal explicite.

---

## Modèle de plugin

Un plugin déclare une **source** et sait traduire une `Query` en appels natifs puis mapper les réponses vers le pivot.

### Manifeste YAML

```yaml
manifest_version: "1"
id: gallica
name: "Gallica (BnF)"
maintainer: "portolan-core@example.org"
status: official           # official | community | deprecated
version: "1.3.0"

protocol: sru              # oai-pmh | sru | rest-json | iiif-search | custom
base_url: https://gallica.bnf.fr/SRU
auth:
  scheme: none
rate_limit:
  rps: 2
  burst: 5
rights_default: "InC"
coverage:
  description: "Collections numérisées BnF"
  formats: [text, image, map, sound]

capabilities:
  - full_text
  - facet_date
  - facet_creator
  - iiif_manifest
  - pagination

search:
  query_template: "{{ q }}"
  pagination:
    style: offset
    page_param: startRecord
    size_param: maximumRecords
  response:
    items_path: "$.records.recordData"
    total_path: "$.numberOfRecords"
    mapping:
      native_id: "$.identifier"
      title: "$.title"
      creators: "$.creator"
      dates: "$.date"
      media:
        - kind: iiif_manifest
          url_template: "https://gallica.bnf.fr/iiif/{{ ark }}/manifest.json"
      rights: "$.rights"

hooks:                     # optionnels, Python signé
  post_parse: gallica_plugin.post_parse
```

### Interface Python (pour connecteurs non triviaux)

```python
from portolan.plugin import Connector, Query, Result, Capability

class GallicaConnector(Connector):
    manifest = "manifest.yaml"

    async def search(self, query: Query) -> AsyncIterator[Result]:
        ...

    async def health(self) -> HealthStatus:
        ...
```

Un connecteur peut être **100 % déclaratif** (YAML seul) ou **hybride** (YAML + hooks Python pour les cas non triviaux : resumption tokens, auth OAuth2, parsing MARC XML, etc.).

---

## Démarrage rapide

### Prérequis

- Python 3.12+
- Redis (ou DiskCache pour le dev)
- Docker + Docker Compose (optionnel, mais recommandé)

### Installation locale

```bash
git clone https://github.com/maribakulj/portolan-hub.git
cd portolan-hub
make dev            # lance API + Redis + console
```

### Première requête

```bash
# Via CLI
portolan sources list
portolan query "Gustave Moreau" --sources gallica,bodleian --limit 20

# Via API
curl -X POST http://localhost:8000/queries \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Gustave Moreau",
    "sources": ["gallica", "bodleian"],
    "limit": 20
  }'
```

---

## SDK Python

```python
from portolan import Client

client = Client(base_url="http://localhost:8000", token="dev-token")

# Exploration des sources
for source in client.sources.list():
    print(source.id, source.capabilities)

# Requête fédérée streamée
results = client.query(
    intent="saint Sébastien",
    sources=["gallica", "bodleian", "europeana"],
    filters={"date_range": ("1400", "1700")},
).stream()

for r in results:
    print(r.title, r.creators, r.media[0].url if r.media else None)

# Vers Pandas
df = client.query("orfèvrerie art déco").to_dataframe()
```

### Intégration Jupyter

Un widget léger affiche les miniatures IIIF dans un notebook :

```python
from portolan.jupyter import grid
grid(client.query("portraits flamands").first(50))
```

---

## Console web

La console expose :

- **Explorateur de sources** : capabilities, santé en direct, fiche licence.
- **Composeur de requêtes** : formulaire guidé + preview JSON + dry-run.
- **Résultats** : liste, grille images, viewer IIIF (Mirador intégré).
- **Historique** des requêtes par utilisateur.
- **Tableau de bord** : erreurs par source, temps de réponse, quotas consommés.
- **Exports** : JSON, CSV, collection IIIF.

---

## Créer un connecteur

Deux voies selon la complexité de la source.

### Voie 1 — Déclarative (YAML)

Pour une API REST/JSON ou un endpoint OAI-PMH/SRU standard, aucune ligne de Python n'est nécessaire. Le DSL YAML couvre :

- mapping des paramètres de requête (Jinja2 sur `query`) ;
- mapping des réponses (JSONPath ou XPath selon format) ;
- pagination (offset, cursor, resumption token) ;
- gestion des erreurs standard.

Un éditeur dans la console permet de tester en direct la réponse brute face au mapping appliqué.

### Voie 2 — Hybride (YAML + hooks Python)

Pour les cas non standards :

```python
# mon_plugin.py
from portolan.plugin import hook

@hook("post_parse")
def enrich(raw_item, result, context):
    if "marcxml" in raw_item:
        result.subjects = parse_marc_subjects(raw_item["marcxml"])
    return result
```

Les hooks tournent dans un **sandbox restreint** : pas d'accès fichier, pas de `socket` direct, httpx client fourni par le runtime.

### Packager et publier

```bash
portolan plugin package ./mon-plugin/
portolan plugin test ./mon-plugin.zip --fixtures ./fixtures/
portolan plugin publish ./mon-plugin.zip
```

---

## Gouvernance des plugins

Trois statuts :

- **Officiel** : maintenu par l'équipe cœur, testé quotidiennement, SLA.
- **Communautaire** : publié par un tiers, vérifié lors de la soumission, tests nocturnes agrégés mais pas de SLA.
- **Déprécié** : plus maintenu, désactivé par défaut, possibilité de le réactiver explicitement.

Chaque plugin porte :

- Un mainteneur désigné.
- Une version sémantique.
- Un fichier de fixtures (réponses capturées) pour les tests de régression.
- Un statut de santé affiché en direct dans la console.

Ce modèle s'inspire de `dbt packages`, `VS Code extensions` et `Home Assistant integrations`.

---

## Feuille de route V1

Livraison en 8 sprints de 2 semaines (≈ 4 mois). Détails complets dans [ROADMAP.md](./ROADMAP.md).

| Sprint | Thème | Livrable clé |
|--|--|--|
| S0 | Fondations | Repo, CI, docker-compose, ADR |
| S1 | Noyau | Pivot, plugin contract, loader, plugin IIIF générique |
| S2 | Connecteurs + fédération | OAI-PMH, SRU, Gallica, dispatch parallèle |
| S3 | API + cache + politesse | FastAPI, Redis, rate limit, dry-run |
| S4 | SDK + CLI | PyPI, Jupyter, Pandas, typer CLI |
| S5 | Console web | Explorer, composer, viewer IIIF |
| S6 | Low-code connecteurs | DSL YAML + éditeur visuel + sandbox Python |
| S7 | Observabilité, droits, hardening | Métriques, OpenTelemetry, RightsStatements, release `v1.0.0` |

**Critères de sortie V1** : 5 connecteurs officiels, 3 utilisateurs pilotes externes, SDK sur PyPI, couverture de tests ≥ 80 %.

---

## V2 ambitieuse — pistes d'amélioration

La V1 vise la robustesse et l'utilité immédiate. La V2 vise la différenciation et l'ambition intellectuelle. Les pistes ci-dessous sont organisées par axe et par degré d'ambition.

### Axe 1 — Sémantique et alignement d'entités

- **Alignement automatique vers Wikidata, VIAF, Getty ULAN/AAT/TGN**. Chaque résultat se voit proposer des liens vers des identifiants d'autorité.
- **Déduplication cross-source** basée sur les entités alignées (ex. "le Louvre" = Q19675 = aat/300312281).
- **Graphe des entités** navigable (personne → œuvres → lieux → périodes).
- **Import/export JSON-LD / LinkedArt** pour les institutions qui publient déjà en ce format.
- **Inférences légères** : période calculée à partir de dates de création + dates de vie du créateur.

### Axe 2 — Recherche sémantique et similarité

- **Embeddings textuels** (titres, descriptions, sujets) indexés dans un vector store (Qdrant, pgvector).
- **Requêtes en langage naturel** converties en requêtes structurées via un LLM contrôlé (avec schéma de sortie strict).
- **Similarité visuelle** entre objets et images (CLIP ou DINOv2) pour "trouver des œuvres visuellement proches".
- **Classification automatique** des sujets iconographiques (compléter Iconclass via un modèle).
- **Suggestion de requêtes** en fonction de l'historique et des résultats faibles ("tu cherches peut-être…").

### Axe 3 — Agents et intégrations IA

- **Serveur MCP (Model Context Protocol)** exposant les outils `search_heritage`, `get_iiif_manifest`, `list_sources`, `align_entity`. Permet à un agent Claude ou autre d'opérer Portolan proprement.
- **Mode "agent curatorial"** : l'utilisateur décrit une intention, un agent orchestre plusieurs requêtes, propose un plan, justifie ses choix, et livre un dossier documenté.
- **Garde-fous explicables** : chaque action de l'agent est tracée, annulable, et auditée.
- **Export de conversations** vers un notebook reproductible.

### Axe 4 — Workflows et composition

- **Éditeur de workflows visuels** (DAG) : requête → filtre → enrichissement → export. Alternative au DSL YAML pour publics non techniques.
- **Workflows déclenchés** : webhook, cron, événement de changement de source.
- **Abonnement à une requête** : "préviens-moi quand une nouvelle œuvre de Moreau est publiée par une des sources".
- **Notebooks serveur** intégrés (JupyterHub ou VSCode.dev) avec kernel pré-configuré.
- **Collaboration temps réel** sur une requête partagée (type Figma) — probablement en V2.5.

### Axe 5 — Droits, licences, éthique

- **Moteur de droits complet** avec règles composables (CC, RightsStatements, licences institutionnelles).
- **Détection de sensibilités culturelles** (CARE principles, Labels for Indigenous Heritage Items) — opt-in par source.
- **Politique d'usage configurable** par organisation utilisatrice (filtre automatique selon droits commerciaux).
- **Registre de consentement** pour les institutions souhaitant limiter certaines réutilisations.

### Axe 6 — Écosystème plugins

- **Marketplace public** avec notation, tests agrégés, statistiques d'usage.
- **Plugins signés** cryptographiquement (sigstore) pour vérification de provenance.
- **Partage de fixtures** entre institutions pour améliorer la couverture de test.
- **Générateur de connecteur assisté par IA** : on pointe un Swagger/OpenAPI, le système propose un plugin YAML à valider.
- **Programme de certification** pour les institutions qui veulent un plugin officiel.

### Axe 7 — Performance et échelle

- **Index pivot optionnel** (OpenSearch/Meilisearch) pour les requêtes sur sous-ensembles fréquemment interrogés, avec invalidation contrôlée.
- **Moissonnage incrémental** OAI-PMH en arrière-plan pour les sources qui le supportent (cache chaud).
- **Sharding** par domaine (cartes, peinture, sonore) si le trafic le justifie.
- **Mode multi-tenant hébergé** (SaaS) avec isolation stricte par organisation.
- **Edge caching** IIIF via un CDN pour réduire la charge sur les serveurs institutionnels.

### Axe 8 — Expérience utilisateur avancée

- **Viewer comparatif** (deux manuscrits côte à côte, annotations partagées).
- **Timeline et cartographie** automatiques des résultats d'une requête.
- **Parcours narratifs** : composition d'expositions virtuelles à partir des résultats (export en collection IIIF + StoryMap).
- **Accessibilité renforcée** : lecture d'écran, sous-titres auto pour contenus vidéo patrimoniaux.
- **Mode offline** pour la consultation de résultats préalablement exportés.

### Axe 9 — Gouvernance et communauté

- **Conseil scientifique** mêlant institutions, chercheurs, développeurs.
- **Programme "partenaire institutionnel"** avec engagement réciproque (API stable d'un côté, plugin maintenu de l'autre).
- **Financement hybride** : base open source, services managés payants, sponsors institutionnels.
- **Certification RGPD / conformité** pour les usages européens.
- **Documentation multi-langue** (FR, EN, DE, IT, ES au minimum).

### Axe 10 — Données dérivées et recherche

- **Jeux de données publiés** (via Zenodo / DataCite) à partir de requêtes notables, avec DOI.
- **Citabilité académique** : chaque requête fédérée produit un identifiant persistant et une note méthodologique.
- **Intégration HAL / OpenAlex** pour lier corpus patrimonial et publication scientifique.
- **Reproductibilité** : une requête exportée peut être rejouée, la provenance garantit l'identification des changements.

---

## Non-objectifs

Pour rester concentré, Portolan Hub **ne cherchera pas** à :

- Remplacer les systèmes internes des institutions (SIGB, DAM, CMS).
- Stocker durablement une copie des données source (sauf cache explicite, borné, révocable).
- Produire des transcriptions OCR/HTR (on intègre les transcriptions existantes, on ne les calcule pas).
- Devenir un portail public grand public (le produit cible des professionnels et des développeurs).
- Imposer une ontologie universelle à toutes les institutions.
- Générer des métadonnées par LLM sans supervision (l'IA enrichit, n'invente pas).

---

## Contribuer

Voir [CONTRIBUTING.md](./CONTRIBUTING.md).

Les contributions les plus utiles au début du projet :

- Nouveaux connecteurs (suivre le guide dans `docs/plugin-authoring.md`).
- Fixtures VCR pour les sources déjà couvertes.
- Traductions de la console.
- Retours d'usage sur des requêtes réelles.

Code de conduite : [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

---

## Licence

Voir [LICENSE](./LICENSE).
