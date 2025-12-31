# Plan d Implementation: mef-macro-refresh

## Informations
**Date:** 2025-12-31
**Base sur:** tasks/mef-macro-refresh/01_analysis.md
**Approche:** Ajuster ttl et ajouter un refresh cible pour les caches MEF, plus un fallback visuel simple.

## Objectif final
Pouvoir rafraichir les indicateurs macro sans vider tout le cache, et limiter la persistance des N/A.

## Checklist technique (step-by-step)

### Phase 1: TTL MEF
- [ ] **1.1** Reduire le ttl des caches MEF (ex: 600-900s)
  - Fichiers: `ui/pages/5_Market_Trends.py`, `ui/pages/6_Scenario_Analysis.py`

### Phase 2: Refresh Macro (UI)
- [ ] **2.1** Ajouter un bouton "Refresh Macro" qui purge uniquement les caches MEF
  - Cible: fetch_exchange_rate.clear(), fetch_csx_summary.clear(), fetch_csx_index.clear()
  - Fichiers: `ui/pages/5_Market_Trends.py`, `ui/pages/6_Scenario_Analysis.py`

### Phase 3: Feedback visuel
- [ ] **3.1** Ajouter un message discret si toutes les valeurs macro sont indisponibles
  - Fichiers: `ui/pages/5_Market_Trends.py`, `ui/pages/6_Scenario_Analysis.py`

### Phase 4: Memoire
- [ ] **4.1** Documenter dans `claudememoire` et `MEMOIRE_CLAUDE.md`

## Points de validation
- [ ] Le bouton "Refresh Macro" recharge les donnees MEF
- [ ] Les N/A ne persistent pas plus que le ttl

## Pret pour implementation
- [x] Analyse complete (01_analysis.md ok)
- [x] Plan valide par l utilisateur
