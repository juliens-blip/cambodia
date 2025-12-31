# Analyse: scenario-doc-filtering

## Contexte
**Date:** 2025-12-30
**Demande initiale:** Ameliorer la selection des documents pour Scenario Analysis (choisir les documents essentiels). La selection doit tenir compte des tweets, des docs en ligne, et des tendances de marche.
**Objectif:** Rendre la selection des documents plus pertinente (qualite + thematique) pour nourrir l analyse Perplexity.

## Etat actuel de la codebase

### Fichiers concernes
| Fichier | Type | Role | Lignes |
| --- | --- | --- | --- |
| ui/pages/6_Scenario_Analysis.py | UI | Selection docs (query + top_k) + docs_context | DOCS_* + build_docs_context |
| app/services/semantic_search_service.py | Service | Recherche vectorielle + filtre source | search() |
| app/api/routes/semantic.py | API | /api/v1/search (embedding + pgvector) | semantic_search() |
| app/services/market_trends_service.py | Service | twitter_summary, news_summary, key_factors, top_tweets | _parse_analysis() |
| app/api/routes/trends.py | API | Scenario prompt utilise docs_context | /trends/scenario |
| scripts/apply_context_migration.py | Doc/Schema | context_documents metadata (title, url, scraped_at, char_count) | MIGRATION_SQL |

### Architecture actuelle
```
UI Scenario Analysis
  -> /api/v1/search (query fixe, top_k=5, threshold=0.3, source=GDrive)
  -> build_docs_context (top 5 chunks brut)
  -> /api/v1/trends/scenario (docs_context + tweets + market)
```

### Code snippets cles
#### ui/pages/6_Scenario_Analysis.py
```python
search_query = f"{commodity} market trends prices analysis"
docs_data = fetch_historical_docs(commodity, search_query, limit=DOCS_TOP_K)
# build_docs_context prend les chunks top_k sans filtrage qualitatif
```

#### app/services/market_trends_service.py
```python
parsed['top_tweets'] = tweets[:5]
parsed['news_summary'] = self._extract_section(response_text, 'NEWS', 'MARKET DATA')
parsed['market_summary'] = self._extract_section(response_text, 'MARKET DATA', 'INTEGRATED')
parsed['key_factors'] = factors[:5]
```

#### app/services/semantic_search_service.py
```python
result = supabase.client.rpc("match_documents", {
    "query_embedding": query_vector,
    "match_count": top_k,
    "match_threshold": similarity_threshold,
    "filter_commodity": commodity
}).execute()
# filtre source post-search uniquement
```

## Documentation externe (Context7)
- Context7 est configure dans .mcp.json, mais l outil n est pas expose dans cette session.
- Pas de dependances externes requises pour la selection (heuristiques locales).

## Points d attention
- La requete est statique et ignore le contexte (tweets, tendances, news).
- Aucun filtrage qualitatif (OCR bruit, titres non pertinents) n est applique.
- Les chunks sont pris tels quels (pas de selection par document_id ni dedup).
- Les documents essentiels peuvent etre noyes par des docs generiques (ex: abbreviation.pdf).

## Opportunites identifiees
- Enrichir la requete avec mots-cles extraits de twitter_summary, news_summary, market_summary, key_factors, top_tweets.
- Recuperer plus de candidats (top_k 10-15), puis filtrer/ranker localement.
- Regrouper par document_id et choisir le meilleur chunk par document.
- Filtrer les docs a faible qualite (ratio alphabetique, longueur, titres non pertinents).
- Expliquer le filtrage de maniere generale (top_k, seuil, filtres, qualite).

## Resume executif
- La selection actuelle se base sur une requete fixe et un top_k brut.
- Le contexte tweet/market n est pas utilise pour guider la recherche.
- L absence de filtrage qualitatif laisse passer des docs peu utiles.
- Prochaine etape: ajouter un pipeline de selection (keywords + ranking + qualite).
