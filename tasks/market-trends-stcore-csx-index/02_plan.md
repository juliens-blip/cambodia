# Plan d'Implementation: Market Trends - _stcore routing + CSX index fallback

## Informations
**Date:** 2025-12-31 20:23
**Base sur:** tasks/market-trends-stcore-csx-index/01_analysis.md
**Approche:** Corriger la base URI Streamlit via injection HTML (BACKEND_BASE_URL) avant le bundle JS; ajouter un fallback simple pour CSX Index et message explicite.

## Objectif Final
- Auto-refresh Streamlit stable (plus de 404 sur /Market_Trends/_stcore/*).
- CSX Index affiche une valeur quand disponible, sinon message clair + fallback "dernier index valide" si present.

## Gap Analysis
| Etat Actuel | Etat Cible | Action Requise |
|---|---|---|
| JS Streamlit derive la base sur /Market_Trends | Base fixe sur la racine | Injecter window.__streamlit.BACKEND_BASE_URL dans index.html avant JS |
| CSX index renvoie null -> N/A | Fallback + message explicite | Stocker dernier index valide en session et afficher l'etat de la source |

## Architecture Proposee
`
[start.py] -> patch index.html -> streamlit run
    |-> index.html injecte BACKEND_BASE_URL (root)
    |-> JS _stcore ping vers /_stcore/*

[UI pages] -> fetch_csx_index -> fallback dernier index valide
`

## Checklist Technique (Step-by-Step)

### Phase 1: Preparation
- [ ] **1.1** - Ajouter une fonction patch_streamlit_index_html() dans start.py
  - Action: localiser streamlit/static/index.html, injecter un script si absent
  - Validation: HTML contient un marqueur unique + BACKEND_BASE_URL

### Phase 2: Fix auto-refresh (Streamlit)
- [ ] **2.1** - Appeler patch_streamlit_index_html() avant un_streamlit()
  - Validation: GET /Market_Trends contient le script injecte
- [ ] **2.2** - Verifier que le ping cible /_stcore/health (plus de 404 Market_Trends/_stcore)

### Phase 3: CSX Index fallback
- [ ] **3.1** - Ajouter un cache "dernier index valide" dans ui/pages/5_Market_Trends.py
  - Action: si alue ou change_percent non nuls, stocker dans st.session_state
  - Validation: si l'API renvoie null, l'UI affiche la derniere valeur connue + note
- [ ] **3.2** - Repeter la meme logique dans ui/pages/6_Scenario_Analysis.py

### Phase 4: Tests & Validation
- [ ] **4.1** - Test manuel: ouvrir /Market_Trends et verifier absence de 404 _stcore
- [ ] **4.2** - Test manuel: rafraichir la page et verifier auto-refresh stable
- [ ] **4.3** - Test manuel: simuler csx_index null et verifier message/fallback

## Commandes a Executer
`ash
# (Optionnel) Verifier HTML injecte
a) curl https://cambodia.up.railway.app/Market_Trends | rg "BACKEND_BASE_URL"
`

## Risques Identifies
| Risque | Impact | Mitigation |
|---|---|---|
| Patch HTML fragile si Streamlit change son index.html | Moyen | Ajouter un marqueur et injection idempotente |
| CSX index toujours null (upstream) | Moyen | Message explicite + fallback local |

## Points de Validation
- [ ] /Market_Trends/_stcore/health n'est plus appele (ou renvoie 200 si on force)
- [ ] UI reste connectee (statut Streamlit OK)
- [ ] CSX Index ne casse pas l'affichage

## References (Context7)
- Context7 indisponible dans ce runtime; base sur code source Streamlit local.

## Estimation
- **Complexite:** Moyenne
- **Fichiers modifies:** 3 (start.py, ui/pages/5_Market_Trends.py, ui/pages/6_Scenario_Analysis.py)
- **Fichiers crees:** 0
- **Dependances:** Aucune

## Pret pour Implementation
- [x] Analyse complete (01_analysis.md)
- [ ] Plan valide par l'utilisateur
- [x] Toutes les dependances identifiees
- [x] Strategie claire
