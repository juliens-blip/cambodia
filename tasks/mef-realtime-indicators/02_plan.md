# Plan d Implementation: mef-realtime-indicators

## Informations
**Date:** 2025-12-31
**Base sur:** tasks/mef-realtime-indicators/01_analysis.md
**Approche:** Ajouter un bloc "macro indicateurs" via appels MEF en UI et injecter un contexte macro simple dans /trends/scenario, sans nouvelles dependances.

## Objectif final
Afficher les indicateurs MEF (taux USD/KHR, CSX summary, CSX index) dans l UI et les utiliser comme contexte additionnel pour l analyse Scenario.

## Gap Analysis
| Etat actuel | Etat cible | Action requise |
| --- | --- | --- |
| Aucune conso MEF realtime | Donnees macro visibles | Ajouter fetch + affichage UI |
| Prompt scenario sans macro | Prompt avec bloc macro | Ajouter macro_context API |
| Labels manquants | Labels EN/FR | Mettre a jour translations |

## Architecture proposee
```
UI (Market Trends / Scenario Analysis)
  -> fetch MEF realtime (exchange-rate, csx-summary, csx-index)
  -> affichage "Macro indicateurs"
  -> macro_context (string compact)
  -> /api/v1/trends/scenario (macro_context)
API /trends/scenario
  -> ajoute bloc "MACRO INDICATORS" au prompt
```

## Checklist technique (step-by-step)

### Phase 1: Preparation
- [x] **1.1** Definir constantes MEF + fonctions fetch
  - Fichiers: `ui/pages/5_Market_Trends.py`, `ui/pages/6_Scenario_Analysis.py`
  - Ajouter: MEF_REALTIME_BASE + fetch_exchange_rate + fetch_csx_summary + fetch_csx_index
  - Cache: st.cache_data ttl 3600

### Phase 2: UI Scenario Analysis
- [x] **2.1** Construire macro_context (string compact)
  - Source: exchange rate + CSX summary + CSX index
  - Fichier: `ui/pages/6_Scenario_Analysis.py`

- [x] **2.2** Ajouter section "Macro indicateurs" + fallback N/A
  - Fichier: `ui/pages/6_Scenario_Analysis.py`

- [x] **2.3** Passer macro_context a generate_scenario_analysis
  - Fichier: `ui/pages/6_Scenario_Analysis.py`

### Phase 3: UI Market Trends
- [x] **3.1** Ajouter section "Macro indicateurs" (MEF/NBC/CSX)
  - Fichier: `ui/pages/5_Market_Trends.py`

### Phase 4: API Scenario
- [x] **4.1** Ajouter parametre macro_context a /trends/scenario
  - Fichier: `app/api/routes/trends.py`

- [x] **4.2** Injecter bloc macro dans le prompt
  - Fichier: `app/api/routes/trends.py`

### Phase 5: i18n
- [x] **5.1** Ajouter labels EN/FR
  - Fichier: `ui/i18n/translations.py`
  - Keys: scenario_macro_indicators, trends_macro_indicators, macro_exchange_rate, macro_csx_index, macro_csx_summary

### Phase 6: Memoire
- [x] **6.1** Documenter dans `claudememoire` et `MEMOIRE_CLAUDE.md`

## Points de validation
- [ ] Les indicateurs MEF s affichent sans erreur (N/A si indisponible)
- [ ] Scenario Analysis envoie macro_context et l API l integre au prompt
- [ ] Pas d impact sur les endpoints existants

## Estimation
- **Complexite:** Moyenne
- **Fichiers modifies:** 4-5
- **Fichiers crees:** 0
- **Dependances:** Aucune

## Pret pour implementation
- [x] Analyse complete (01_analysis.md ok)
- [x] Plan valide par l utilisateur
