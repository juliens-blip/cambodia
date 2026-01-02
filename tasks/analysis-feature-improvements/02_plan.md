# Plan: Feature Analyse - Harmonisation Cashew/Rubber

## Objectif
Uniformiser les prix cashew, rendre les tendances/sentiments prudents, et harmoniser les blocs Cambodge sur cashew et rubber.

## Délégation (APEX)
- Agent Data/Logic: ranges prix + resolve_trend_label + resolve_sentiment_label (backend).
- Agent UI: Market Trends labels/emoji/sentiment + Cambodia Snapshot rubber.
- Agent Scenario: bloc Cambodia Metrics cashew + farmgate factor paramétrable.

## Étapes
1. Backend — Ranges & prompts
   - Mettre à jour ranges cashew (1,800–2,200 / 6,200–6,800) dans `perplexity_service.py`, `market_trends_service.py`, `trends.py`.
   - Ajuster `public_prices_service.py` (cashew price series) vers 6,200–6,800.

2. Backend — Tendance & sentiment
   - Ajouter `resolve_trend_label()` + `resolve_trend_label_cashew()` et appliquer lors du stockage (`overall_trend`).
   - Extraire 24h/7d/30d si présents; fallback à 24h/0 si absent.
   - Ajouter `resolve_sentiment_label()` avec seuil tweet_count_30d < 10.

3. UI — Market Trends
   - Utiliser `overall_trend` résolu sans sur-correction UI; ajouter mapping `slightly_bullish/bearish`.
   - Afficher sentiment “Not enough data (X tweets in 30 days)” si label unknown.
   - Ajouter bloc Cambodia Snapshot pour rubber.
   - Afficher price_basis/price_type dans Public Price Data.

4. Scenario Analysis — Cashew & Farmgate rubber
   - Ajouter bloc standard Cambodia Metrics pour cashew (RCN range, farmgate range, export revenue range, families affected, status).
   - Paramétrer farmgate rubber via `RUBBER_FARMGATE_FACTOR` (backend + UI).

5. Traductions & config
   - Ajouter labels “slightly” + ajuster texte Tweet Volume 30d.
   - Ajouter variable `RUBBER_FARMGATE_FACTOR` dans `app/config.py`, `.env.example`, `ui/config.py`.

6. Finalisation
   - Mettre à jour `tasks/analysis-feature-improvements/03_implementation_log.md`.
   - Commit + push.
