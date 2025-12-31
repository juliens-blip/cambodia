# Analyse: mef-realtime-indicators

## Contexte
**Date:** 2025-12-31
**Demande initiale:** Integrer 3 endpoints MEF (exchange-rate USD, CSX summary, CSX index) pour etayer l'analyse et les points de vue sur le marche cambodgien, sans complexifier l'app.
**Objectif:** Ajouter une couche macro simple (taux de change KHR, resume CSX, index CSX) visible dans l'UI et, si possible, integree au prompt d'analyse Scenario.

## Etat actuel de la codebase

### Fichiers concernes
| Fichier | Type | Role | Lignes |
| --- | --- | --- | --- |
| ui/pages/5_Market_Trends.py | UI | Page tendances marche + prix publics | Sections principales |
| ui/pages/6_Scenario_Analysis.py | UI | Scenario analysis (prix + docs + tweets) | generate_scenario_analysis |
| app/api/routes/trends.py | API | Endpoint /trends/scenario + prompt | L274+ |
| ui/i18n/translations.py | i18n | Labels UI EN/FR | scenario/trends keys |
| ui/config.py | Config | API base URLs | - |

### Architecture actuelle
```
UI Market Trends -> /api/v1/trends/latest + /api/v1/trends/public/prices
UI Scenario Analysis -> /api/v1/search + /api/v1/trends/scenario
API /trends/scenario -> prompt (prix + sentiment + docs_context)
```

### Endpoints externes a integrer (MEF)
- Exchange rate (USD): https://data.mef.gov.kh/api/v1/realtime-api/exchange-rate?currency_id=USD
- CSX summary: https://data.mef.gov.kh/api/v1/realtime-api/csx-summary
- CSX index: https://data.mef.gov.kh/api/v1/realtime-api/csx-index

### Code snippets cles
#### ui/pages/6_Scenario_Analysis.py
```python
response = client.post(url, params=params, json=json_data, timeout=120.0)
# json_data contient price_data, twitter_data, docs_context
```

#### app/api/routes/trends.py
```python
@router.post("/scenario/{commodity}")
async def generate_scenario_analysis(..., price_data, twitter_data, docs_context):
    prompt = scenario_prompts[scenario_type]
    result = await perplexity._query(prompt, commodity, f"scenario_{scenario_type}")
```

## Documentation externe (Context7)
- Context7 est configure dans .mcp.json, mais l outil n est pas expose dans cette session.
- Aucune nouvelle lib externe requise (httpx deja utilise).

## Points d attention
- Eviter de complexifier l application: rester sur des appels HTTP simples + cache.
- L endpoint /trends/scenario n accepte pas encore de contexte macro.
- Les labels UI pour nouvelles sections doivent etre ajoutes en EN/FR.

## Opportunites identifiees
- Ajouter une section "Indicateurs macro" dans Market Trends et Scenario Analysis.
- Construire un macro_context compact (taux KHR, CSX summary/index) et l injecter dans le prompt scenario.
- Cache court (30-60 min) pour limiter la charge sur l API MEF.

## Resume executif
- Les nouvelles sources MEF ne sont pas consommees aujourd hui.
- L integration la plus simple: fetch direct en UI + affichage, et optionnellement injection dans le prompt Scenario.
- Une modification minimale de /trends/scenario permet d ajouter le contexte macro sans impacter le reste.
