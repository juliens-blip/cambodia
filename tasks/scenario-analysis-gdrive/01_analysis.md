# Analyse: scenario-analysis-gdrive

## Contexte
**Date:** 2025-12-30
**Demande initiale:** Utiliser la documentation Google Drive pour l'analyse (Scenario Analysis). Les tweets sont bien pris en compte, mais les docs Drive ne sont pas utilises.
**Objectif:** Injecter les documents GDrive dans l'analyse (RAG/semantic search) et stabiliser l'indexation des embeddings.

## Etat actuel de la codebase

### Fichiers concernes
| Fichier | Type | Role | Lignes |
| --- | --- | --- | --- |
| ui/pages/6_Scenario_Analysis.py | UI | Appelle /api/v1/search + lance scenario analysis | L81, L141, L308 |
| app/api/routes/trends.py | API | /api/v1/trends/scenario (Perplexity) | L274 |
| app/api/routes/semantic.py | API | /api/v1/search, init embedding | L35, L89 |
| app/api/routes/admin.py | API | Indexation embeddings (background task) | L40 |
| app/api/routes/admin_v2.py | API | Indexation V2 (thread pool, progress) | L1-120 |
| app/services/semantic_search_service.py | Service | match_documents RPC + filter source | L119-141 |
| app/services/embedding_service.py | Service | EMBEDDING_MODEL, dimension, prefixes | L37-59 |
| app/collectors/gdrive_collector.py | Collector | Context docs GDrive (document_type=context) | L313-357 |
| scripts/index_existing_documents.py | Script | Indexation locale (bug embed_document) | L106 |
| docs/SEMANTIC_SEARCH_DEBUG_HISTORY.md | Doc | Historique des 10 tentatives | - |
| docs/phase3-semantic-search/README.md | Doc | Specs semantic search (1024D, outdated) | - |
| docs/phase3-semantic-search/USER_GUIDE.md | Doc | Filtre source=GDrive, exemples | - |
| docs/phase3-semantic-search/TROUBLESHOOTING.md | Doc | OOM + no results | - |

### Architecture actuelle
```
GDriveCollector
  -> context_documents (Supabase)
     -> admin indexation (admin.py)
        -> document_embeddings (pgvector)
           -> match_documents RPC
              -> /api/v1/search (semantic.py)
                 -> UI Scenario Analysis (docs count)

Scenario Analysis (trends.py)
  -> Perplexity prompt (price_data + twitter_data)
  -> NO use of docs_data / semantic search
```

### Code snippets cles
#### ui/pages/6_Scenario_Analysis.py
```python
json_data = {}
if market_data:
    json_data["price_data"] = market_data
if twitter_data:
    json_data["twitter_data"] = twitter_data
# docs_data is never sent to the API
```

#### app/api/routes/trends.py
```python
@router.post("/scenario/{commodity}")
async def generate_scenario_analysis(..., price_data=None, twitter_data=None):
    # prompt uses price + twitter only
    result = await perplexity._query(prompt, commodity, f"scenario_{scenario_type}")
```

#### app/api/routes/admin.py
```python
embedding_service = get_embedding_service()  # singleton
# chunk -> embed -> insert into document_embeddings
```

## Documentation externe (Context7)
- Context7 non disponible dans cet environnement.
- Documentation locale utilisee:
  - docs/phase3-semantic-search/README.md
  - docs/phase3-semantic-search/USER_GUIDE.md
  - docs/phase3-semantic-search/TROUBLESHOOTING.md
  - docs/SEMANTIC_SEARCH_DEBUG_HISTORY.md

## Dependances

### Internes
- GDriveCollector -> context_documents (gdrive_collector.py)
- admin indexation -> document_embeddings (admin.py)
- semantic search -> match_documents RPC (semantic_search_service.py)
- Scenario Analysis UI -> trends/scenario API (6_Scenario_Analysis.py -> trends.py)

### Externes
- sentence-transformers (embeddings)
- Supabase pgvector (document_embeddings + match_documents)
- Perplexity API (scenario analysis, RAG)
- Streamlit + FastAPI + httpx

## Points d'attention
- Scenario Analysis ne consomme pas docs_data: l'analyse utilise seulement prix + tweets (trends.py + UI).
- Indexation GDrive est fragile (OOM historique). admin.py utilise le singleton, mais admin_v2 (plus robuste) n'est pas connecte.
- scripts/index_existing_documents.py appelle embed_document (method inexistante) -> script casse si utilise.
- Docs semantic search mentionnent 1024D (e5-large) alors que le code charge e5-small 384D.
- /api/v1/search n'existe que si sentence-transformers est dispo (SEMANTIC_AVAILABLE).

## Opportunites identifiees
- Integrer RAG dans /trends/scenario: recuperer contexte via semantic search et l'injecter dans le prompt.
- Reutiliser admin_v2 (thread pool + progress) pour stabiliser l'indexation Railway.
- Aligner la documentation (dimensions 384, modele e5-small, chunking).
- Unifier le chunking (ChunkingService vs chunk_text local) pour coherence.

## Resume executif
- Le pipeline d'indexation GDrive existe mais reste fragile; embeddings vides = zero docs.
- Meme avec embeddings, Scenario Analysis ignore les docs: aucune injection de contexte.
- admin_v2 propose une indexation plus stable mais n'est pas branche.
- La doc locale est incoherente sur la dimension (1024 vs 384).
- Prochaine etape: plan d'integration RAG + stabilisation indexation.
