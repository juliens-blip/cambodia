# Plan d'Implementation: Market Trends - _stcore routing + CSX index fallback

## Informations
**Date:** 2026-01-01 00:50
**Base sur:** tasks/market-trends-stcore-csx-index/01_analysis.md
**Approche:** Stabiliser Streamlit (_stcore + auto-refresh via meta refresh HTML) et rendre le CSX Index constant via un fallback persistant (session + cache partage + fichier).

## Objectif Final
- Auto-refresh Streamlit stable (plus de 404 sur /Market_Trends/_stcore/*) et sans blocage.
- CSX Index affiche une valeur quand disponible, sinon message clair + fallback "dernier index valide" persistant.

## Gap Analysis
| Etat Actuel | Etat Cible | Action Requise |
|---|---|---|
| JS Streamlit derive la base sur /Market_Trends | Base fixe sur la racine | Injecter window.__streamlit.BACKEND_BASE_URL dans index.html avant JS |
| Injection BACKEND_BASE_URL en fin de `<head>` | Injection avant le module JS | Repositionner l'injection avant le script module |
| Auto-refresh bloque le rendu | Auto-refresh non bloquant | Utiliser un meta refresh HTML (sans widget) |
| CSX index renvoie null -> N/A | Fallback persistant + message explicite | Stocker dernier index valide en session + cache partage + fichier |
| React #321 (invalid hook call) | Front stable sans erreur | Supprimer widgets custom et utiliser meta refresh |
| Aucun fallback manuel CSX | Valeur stable si MEF renvoie null | Ajouter override via env (CSX_INDEX_FALLBACK_VALUE + UPDATED_AT) |

## Architecture Proposee
`
[start.py] -> patch index.html -> streamlit run
    |-> index.html injecte BACKEND_BASE_URL (root)
    |-> JS _stcore ping vers /_stcore/*

[UI pages] -> fetch_csx_index -> cache partage dernier index valide
[Market Trends] -> auto-refresh non bloquant (meta refresh HTML)
`

## Checklist Technique (Step-by-Step)

### Phase 1: Preparation
- [ ] **1.1** - Ajouter une fonction patch_streamlit_index_html() dans start.py
  - Action: localiser streamlit/static/index.html, injecter un script si absent
  - Validation: HTML contient un marqueur unique + BACKEND_BASE_URL
- [ ] **1.2** - Repositionner l'injection BACKEND_BASE_URL avant le script module
  - Action: si marker trouve apres le module, le retirer puis reinserer apres `<head>`
  - Validation: l'injection est avant `<script type="module">`

### Phase 2: Fix auto-refresh (Streamlit)
- [ ] **2.1** - Appeler patch_streamlit_index_html() avant run_streamlit()
  - Validation: GET /Market_Trends contient le script injecte
- [ ] **2.2** - Remplacer l'auto-refresh par meta refresh HTML
  - Action: injecter `<meta http-equiv="refresh" content="60">` via st.markdown
  - Validation: pas d erreur React #321, la page se rafraichit sans blocage
- [ ] **2.3** - Verifier que le ping cible /_stcore/health (plus de 404 Market_Trends/_stcore)

### Phase 3: CSX Index fallback persistant
- [ ] **3.1** - Ajouter un cache partage + fichier local (Market Trends)
  - Action: stocker dernier index valide dans cache partage + session_state + logs/csx_index_cache.json
  - Validation: reload navigateur conserve la derniere valeur connue
- [ ] **3.2** - Utiliser ce cache dans ui/pages/6_Scenario_Analysis.py
  - Action: fallback identique + usage dans le contexte macro
  - Validation: CSX Index stable meme si MEF renvoie null
- [ ] **3.3** - Ajouter un fallback manuel via env (optionnel)
  - Action: lire CSX_INDEX_FALLBACK_VALUE (+ CSX_INDEX_FALLBACK_UPDATED_AT)
  - Validation: une valeur s'affiche meme si API renvoie null

### Phase 4: Tests & Validation
- [ ] **4.1** - Test manuel: ouvrir /Market_Trends et verifier absence de 404 _stcore
- [ ] **4.2** - Test manuel: activer auto-refresh et verifier que la page ne boucle pas (rendu OK)
- [ ] **4.3** - Test manuel: verifier absence d erreur React #321 dans la console
- [ ] **4.4** - Test manuel: simuler csx_index null et verifier message + fallback persistant

## Commandes a Executer
```bash
# (Optionnel) Verifier HTML injecte
curl https://cambodia.up.railway.app/Market_Trends | rg "BACKEND_BASE_URL"
```

## Risques Identifies
| Risque | Impact | Mitigation |
|---|---|---|
| Patch HTML fragile si Streamlit change son index.html | Moyen | Ajouter un marqueur et injection idempotente |
| CSX index toujours null (upstream) | Moyen | Message explicite + fallback local |

## Points de Validation
- [ ] /Market_Trends/_stcore/health n'est plus appele (ou renvoie 200 si on force)
- [ ] UI reste connectee (statut Streamlit OK, pas de loop)
- [ ] Pas d erreur React #321 dans la console
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
- [x] Plan valide par l'utilisateur
- [x] Toutes les dependances identifiees
- [x] Strategie claire
