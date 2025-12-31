# Analyse: mef-macro-refresh

## Contexte
**Date:** 2025-12-31
**Demande initiale:** Macro Indicators affiche N/A en prod; ajouter un rafraichissement simple + ajuster le cache, sans complexifier.
**Objectif:** Faciliter le rechargement des donnees MEF et reduire la duree de cache pour limiter les N/A persistants.

## Etat actuel de la codebase

### Fichiers concernes
| Fichier | Type | Role | Lignes |
| --- | --- | --- | --- |
| ui/pages/5_Market_Trends.py | UI | Affiche Macro Indicators MEF | fonctions fetch + display |
| ui/pages/6_Scenario_Analysis.py | UI | Affiche Macro Indicators + macro_context | fonctions fetch + display |

### Points d attention
- Les fonctions MEF sont cachees 1h (st.cache_data ttl=3600).
- Market Trends n a pas de bouton pour purger le cache.
- Scenario Analysis a un clear cache global mais pas cible macro.

## Opportunites identifiees
- Reduire ttl a 10-15 min pour MEF.
- Ajouter bouton "Refresh Macro" pour purger uniquement les caches MEF.
- Afficher un message discret si toutes les valeurs macro sont indisponibles.

## Resume executif
- Le N/A peut provenir d un echec MEF cache 1h.
- Un refresh cible + ttl court reglerait le probleme sans complexifier.
