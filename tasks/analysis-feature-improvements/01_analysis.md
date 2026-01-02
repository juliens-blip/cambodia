# Analyse: Feature Analyse - Harmonisation Cashew/Rubber

## Contexte
Date: 2026-01-02
Demande: améliorer la feature d'analyse (Market Trends + Scenario Analysis) en harmonisant les prix cashew, les labels de tendance, le sentiment Twitter, et les blocs Cambodge.
Objectif: cohérence des ranges RCN/kernels, tendances plus prudentes, et métriques Cambodge uniformes.

## État actuel (résumé)
- Prix cashew: ranges 1,500-2,500 (RCN) et 6,000-7,000 (kernels) dispersés dans `perplexity_service.py`, `market_trends_service.py`, `trends.py`.
- Market Trends UI applique une validation locale du label de tendance (fonction `validate_trend_label` côté UI) et n’utilise pas de label “slightly”.
- Sentiment Twitter: détection naïve via mots-clés; pas de score ni seuil “unknown”.
- Scenario Analysis: bloc Cambodia Impact uniquement pour rubber; cashew absent.
- Farmgate rubber: facteur 0.70 codé en dur dans `market_trends_service.py` et `6_Scenario_Analysis.py`.
- Public Price Data: price_basis/price_type existent côté service mais l’affichage UI reste minimal; cashew static prices à 8,500.

## Fichiers concernés (principaux)
- `app/services/perplexity_service.py` (prompts cashew/rubber)
- `app/services/market_trends_service.py` (parsing, validation prix, labels trend/sentiment)
- `app/services/public_prices_service.py` (ranges cashew, price_basis/price_type)
- `app/api/routes/trends.py` (prompt scenarios + price reference guide)
- `ui/pages/5_Market_Trends.py` (labels/emoji trend + sentiment UI + Cambodia Snapshot rubber)
- `ui/pages/6_Scenario_Analysis.py` (bloc Cambodia Metrics cashew + farmgate factor rubber)
- `ui/i18n/translations.py` (nouveaux labels tendance + texte tweet volume)
- `app/config.py`, `.env.example`, `ui/config.py` (RUBBER_FARMGATE_FACTOR)

## Points d’attention
- Éviter d’ajouter des colonnes Supabase non existantes; réutiliser `overall_trend` pour stocker le label résolu.
- Conserver la compatibilité UI avec les anciens enregistrements (fallback si label inconnu).
- Maintenir les ranges cashew cohérents partout (RCN 1,800–2,200 / Kernels 6,200–6,800).

## Addendum - UX/texte (2026-01-02)
- Postprocess sur tous les textes IA avant affichage (ranges, "by2030", doublons, sequences "??").
- Unites uniformes: cashew (USD/ton + USD/kg + KHR/kg), rubber (cents/kg + USD/ton + KHR/kg farmgate).
- Tendances: supprimer "?? Neutral"; emojis coherents et labels compacts.
- Sentiment: afficher "Not enough data" si tweets < 10, sinon montrer Score + Tweets.
- Ajouter un bloc "Cambodia Snapshot" cashew sur Market Trends.
- Compacter Twitter/News/Market Data/Synthesis (2-3 phrases, 3-5 bullets).
