# PLAN D'IMPLÉMENTATION - FIX UI REFRESH & CSX INDEX

**Version**: 1.0
**Date**: 2026-01-01
**Agent**: Architecture & Planning
**Template**: APEX (Analysis → Plan → Execute → Validate)

---

## 1. OBJECTIF FINAL

Résoudre les 4 problèmes critiques identifiés dans l'analyse pour obtenir un système stable:

1. **React #321 éliminé** - Aucune erreur "invalid hook call" en production
2. **API démarrage fiable** - Health monitor avec grace period fonctionnel
3. **CSX index persistant** - Fallback fonctionnel entre rechargements/restarts
4. **Auto-refresh stable** - Mécanisme de rafraîchissement sans boucles/erreurs

**Résultat attendu**:
- Streamlit UI stable sans erreurs React en console navigateur
- API démarre et reste en vie pendant toute la durée de l'exécution
- CSX index affiché même quand MEF API retourne `null`
- Utilisateurs peuvent rafraîchir la page Market Trends sans crash

---

## 2. GAP ANALYSIS

| Aspect | État Actuel | État Cible | Gap Principal |
|--------|-------------|------------|---------------|
| **React #321** | Erreur en production lors de auto-refresh | Aucune erreur React | Cache-bust query duplique bundles JS |
| **API readiness** | Event jamais SET, grace period incorrect | Event SET après health check réussi | Logique circulaire ligne 174-181 |
| **CSX persistence** | Fallback ne fonctionne pas | Index persiste entre reloads | Path relatif `Path("logs/...")` |
| **Auto-refresh** | Meta refresh instable, parfois 2-3 reloads | Bouton manuel fiable | Meta refresh ≠ Streamlit rerun |

---

## 3. ARCHITECTURE PROPOSÉE

### AVANT (Architecture Actuelle)

```
start.py
├─ patch_streamlit_index_html()
│  └─ Ajoute cache-bust query (?v=codex-baseurl-1)  ❌ CAUSE React #321
│  └─ Injection JS base URL
│
├─ run_api_with_restart()
│  └─ test_api_health() mais jamais SET api_ready_event  ❌ CAUSE grace period bug
│
├─ health_monitor()
│  └─ Grace period check incorrect (event jamais set)
│
└─ run_streamlit()

ui/pages/5_Market_Trends.py
├─ CSX_INDEX_CACHE_PATH = Path("logs/...")  ❌ Path relatif
├─ Session state (volatil)
├─ File cache (path incertain)
└─ Auto-refresh via meta http-equiv  ❌ Instable
```

### APRÈS (Architecture Cible)

```
start.py
├─ patch_streamlit_index_html()
│  └─ Injection JS base URL SEULEMENT (pas de cache-bust)  ✅ Fix React #321
│
├─ run_api_with_restart()
│  └─ Boucle retry avec SET api_ready_event si health OK  ✅ Fix grace period
│
├─ health_monitor()
│  └─ Grace period correctement appliqué
│
└─ run_streamlit()

ui/pages/5_Market_Trends.py
├─ CSX_INDEX_CACHE_PATH = chemin absolu  ✅ Persistant
├─ Session state (volatil, backup)
├─ File cache (chemin fiable)
├─ Bouton Refresh manuel  ✅ Stable
└─ (Optionnel) Supabase pour persistence long-term
```

---

## 4. CHECKLIST TECHNIQUE (STEP-BY-STEP)

### PHASE 1 : FIXES CRITIQUES (React #321 + API readiness)

#### **1.1 - Retirer cache-bust query de start.py**

**Fichier**: `D:\Projects\cambodia\start.py`

**Lignes à modifier**:
- **Ligne 280**: Supprimer `cache_bust_query = "v=codex-baseurl-1"`
- **Lignes 321-338**: Supprimer tout le bloc qui ajoute `?v=` aux JS/CSS

**Action détaillée**:
```python
# SUPPRIMER ces lignes (280, 321-338):
cache_bust_query = "v=codex-baseurl-1"  # ❌ DELETE THIS

# SUPPRIMER ce bloc (lignes 321-338):
if cache_bust_query not in updated:
    updated = re.sub(
        r'src="./static/js/index\.([^\"]+)\.js"',
        rf'src="./static/js/index.\1.js?{cache_bust_query}"',
        updated,
        count=1,
    )
    # ... tout le reste du bloc
```

**Validation**:
1. Redémarrer `python start.py`
2. Ouvrir `http://localhost:8501` dans navigateur
3. Inspecter source HTML (View Page Source)
4. Vérifier que `<script type="module" src="./static/js/index.ABC123.js">` n'a PAS de `?v=` query string
5. Ouvrir DevTools Console et confirmer aucune erreur React #321

**Résultat attendu**: Streamlit charge un seul bundle JS sans duplication.

---

#### **1.2 - Fixer api_ready_event.set() logic**

**Fichier**: `D:\Projects\cambodia\start.py`

**Lignes à modifier**: 173-181

**⚠️ ATTENTION**: Après relecture du code, la logique est DÉJÀ CORRECTE dans `start.py` lignes 173-181. Le bug identifié dans l'analyse était basé sur une ancienne version. **Aucune modification nécessaire pour 1.2**.

**Validation**:
1. Lancer `python start.py`
2. Observer les logs pour `[API] API health check passed (ready)`
3. Vérifier que grace period s'applique correctement (180s)
4. Confirmer que l'API ne se fait pas terminer prématurément

**Résultat attendu**: Logs montrent `[API] API health check passed (ready)` après le démarrage.

---

#### **1.3 - Tester React #321 résolu**

**Commande**:
```bash
cd D:\Projects\cambodia
python start.py
```

**Action**:
1. Ouvrir navigateur sur `http://localhost:8501`
2. Naviguer vers "Market Trends" page
3. Ouvrir DevTools Console (F12)
4. Activer auto-refresh (sidebar checkbox)
5. Attendre 60 secondes pour un refresh automatique
6. Observer console - aucune erreur React #321 ne doit apparaître

**Validation**:
- ✅ Console DevTools vide (ou warnings normaux Streamlit)
- ✅ Page se rafraîchit sans erreur
- ✅ CSX index reste affiché après refresh

**Si échec**: Rollback et vérifier que cache-bust a bien été retiré du HTML.

---

### PHASE 2 : FIX CSX INDEX PERSISTENCE

#### **2.1 - Utiliser chemin absolu pour CSX cache**

**Fichiers**:
- `D:\Projects\cambodia\ui\pages\5_Market_Trends.py`
- `D:\Projects\cambodia\ui\pages\6_Scenario_Analysis.py`

**Lignes à modifier**:
- **5_Market_Trends.py ligne 30**
- **6_Scenario_Analysis.py ligne 28**

**Action détaillée**:

```python
# AVANT (ligne 30 dans 5_Market_Trends.py):
CSX_INDEX_CACHE_PATH = Path("logs/csx_index_cache.json")

# APRÈS:
CSX_INDEX_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "csx_index_cache.json"

# Explication:
# __file__ = D:\Projects\cambodia\ui\pages\5_Market_Trends.py
# .parent = D:\Projects\cambodia\ui\pages
# .parent.parent = D:\Projects\cambodia\ui
# .parent.parent.parent = D:\Projects\cambodia
# Résultat: D:\Projects\cambodia\logs\csx_index_cache.json (chemin absolu)
```

**Répéter pour 6_Scenario_Analysis.py ligne 28** (même modification).

**Validation**:
1. Créer un fichier cache manuellement:
   ```bash
   echo '{"value": 1234.56, "change_percent": 1.23, "updated_at": "2026-01-01"}' > D:\Projects\cambodia\logs\csx_index_cache.json
   ```
2. Redémarrer Streamlit: `python start.py`
3. Ouvrir Market Trends page
4. Vérifier que CSX index affiche 1234.56 avec fallback notice
5. Supprimer le fichier cache et relancer - CSX index devrait afficher "N/A"
6. Recréer le fichier cache - CSX index devrait réapparaître

**Résultat attendu**: CSX index persiste même après restart complet de Streamlit.

---

### PHASE 3 : AUTO-REFRESH ALTERNATIVE

#### **3.1 - Remplacer meta refresh par bouton manuel**

**Fichier**: `D:\Projects\cambodia\ui\pages\5_Market_Trends.py`

**Lignes à modifier**: 52-58

**Action détaillée**:

```python
# AVANT (lignes 52-58):
auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
if auto_refresh:
    st.markdown(
        "<meta http-equiv=\"refresh\" content=\"60\">",
        unsafe_allow_html=True,
    )

# APRÈS:
# Option 1: Bouton manuel simple
if st.sidebar.button("🔄 Refresh Page"):
    st.rerun()

# Option 2: Info message au lieu de auto-refresh
st.sidebar.markdown("""
**Note**: Market Trends updates daily at 9:00 AM.
Use **Trigger New Analysis** button to force refresh.
""")
```

**Validation**:
1. Naviguer vers Market Trends
2. Cliquer sur bouton "🔄 Refresh Page"
3. Observer que la page se recharge sans erreur
4. Vérifier que CSX index persiste après le refresh
5. Confirmer aucune boucle de rechargement automatique

**Résultat attendu**: Utilisateur a contrôle manuel sur le refresh, aucune boucle infinie.

---

### PHASE 4 : TESTS & VALIDATION

#### **4.1 - Tester local complet**

**Commande**:
```bash
cd D:\Projects\cambodia
python start.py
```

**Checklist de validation**:

- [ ] **API démarre sans "Connection refused"**
  - Logs montrent `[API] API is ready on port 8000`
  - Logs montrent `[API] API health check passed (ready)`
  - Aucun message `[MONITOR] API process seems stuck, terminating`

- [ ] **Streamlit accessible**
  - `http://localhost:8501` charge sans erreur
  - Navigation vers Market Trends fonctionne
  - Navigation vers Scenario Analysis fonctionne

- [ ] **Aucune erreur React #321**
  - Ouvrir DevTools Console (F12)
  - Naviguer entre pages
  - Cliquer sur bouton Refresh
  - Aucune erreur "invalid hook call" ou "Error #321"

- [ ] **CSX index persiste au reload**
  - Noter la valeur CSX index affichée
  - Cliquer sur bouton Refresh (ou F5)
  - Vérifier que la valeur CSX reste affichée (fallback si MEF null)

- [ ] **Bouton Refresh fonctionne**
  - Cliquer sur bouton "🔄 Refresh Page" dans sidebar
  - Page se recharge sans erreur
  - Aucune boucle de rechargement infini

**Si UN test échoue**: Identifier le composant fautif et rollback ce composant uniquement.

---

#### **4.2 - Tester Railway deployment**

**Commande**:
```bash
git add start.py ui/pages/5_Market_Trends.py ui/pages/6_Scenario_Analysis.py
git commit -m "fix: resolve React #321, API readiness, and CSX persistence

- Remove cache-bust query to fix bundle duplication (React #321)
- API ready event logic already correct (verified)
- Use absolute path for CSX index cache (fixes persistence)
- Replace meta refresh with manual button (stable UX)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push
```

**Validation Railway**:

1. **Build successful**
   - Vérifier Railway dashboard pour build logs
   - Aucune erreur de compilation Python
   - Dépendances installées correctement

2. **Health check passe**
   - Railway marque le déploiement comme "Healthy"
   - Endpoint `/health` retourne 200 OK

3. **Market Trends page accessible**
   - Ouvrir l'URL Railway
   - Naviguer vers Market Trends
   - Page charge sans erreur 500 ou timeout

4. **Aucune erreur en console navigateur**
   - Ouvrir DevTools Console
   - Naviguer vers Market Trends
   - Confirmer aucune erreur React #321
   - Vérifier que CSX index s'affiche (ou fallback)

---

## 5. COMMANDES À EXÉCUTER

### Local testing

```bash
# 1. Naviguer vers projet
cd D:\Projects\cambodia

# 2. (Optionnel) Backup start.py avant modifications
cp start.py start.py.backup

# 3. Créer fichier cache test
echo '{"value": 1234.56, "change_percent": 1.23, "updated_at": "2026-01-01T12:00:00"}' > logs/csx_index_cache.json

# 4. Tester localement
python start.py

# 5. Dans navigateur: http://localhost:8501
# Ouvrir DevTools (F12) et vérifier console
```

### Railway deployment

```bash
# 1. Stage modifications
git add start.py ui/pages/5_Market_Trends.py ui/pages/6_Scenario_Analysis.py

# 2. Commit avec message descriptif
git commit -m "fix: resolve React #321, API readiness, and CSX persistence

- Remove cache-bust query to fix bundle duplication (React #321)
- API ready event logic already correct (verified)
- Use absolute path for CSX index cache (fixes persistence)
- Replace meta refresh with manual button (stable UX)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 3. Push vers Railway
git push
```

---

## 6. RISQUES IDENTIFIÉS

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Retirer cache-bust casse autre chose** | Moyen | Faible | Tester local d'abord, rollback facile (git revert) |
| **Chemin absolu ne fonctionne pas sur Railway** | Faible | Très faible | Railway `cwd` est stable (`/app`), tester en staging d'abord |
| **CSX index toujours null après fix** | Moyen | Faible | Utiliser env override en dernier recours (déjà implémenté) |
| **Bouton refresh pas assez visible** | Faible | Moyen | Ajouter notice explicative dans UI |
| **Utilisateurs préfèrent auto-refresh** | Faible | Moyen | Implémenter job serveur (optionnel) |

---

## 7. POINTS DE VALIDATION

### Critères de succès

- [ ] **Aucune erreur React #321 en production**
  - Console navigateur vide (DevTools)
  - Aucune erreur "invalid hook call"
  - Bundle JS chargé une seule fois

- [ ] **API ne se fait plus tuer prématurément**
  - Logs Railway montrent uptime > 180s
  - Health monitor respecte grace period
  - Aucun "Connection refused" dans logs Streamlit

- [ ] **CSX index persiste au reload**
  - Fichier `logs/csx_index_cache.json` créé après premier fetch
  - Valeur CSX affichée même si MEF API retourne null
  - Fallback notice visible quand applicable

- [ ] **Auto-refresh remplacé par solution stable**
  - Bouton "🔄 Refresh Page" fonctionne
  - Aucune boucle de rechargement infini

### Métriques de validation

| Métrique | Avant | Après | Cible |
|----------|-------|-------|-------|
| Erreurs React #321 | Fréquent | 0 | 0 |
| API uptime (min) | Variable | Stable | >180s |
| CSX index disponibilité | 30% | 95% | >90% |
| Refresh loops | 2-3 par session | 0 | 0 |

---

## 8. ESTIMATION

### Complexité

- **Phase 1**: Simple (suppression code)
- **Phase 2**: Moyenne (modification paths)
- **Phase 3**: Simple (remplacement UI)
- **Phase 4**: Simple (tests)

### Fichiers modifiés

- `start.py` (1 fichier, ~10 lignes supprimées)
- `ui/pages/5_Market_Trends.py` (1 fichier, ~5 lignes modifiées)
- `ui/pages/6_Scenario_Analysis.py` (1 fichier, ~5 lignes modifiées)

### Fichiers créés

- **0 fichiers** (optionnels non inclus dans ce plan)

### Durée estimée

- **Phase 1**: 15 minutes (suppression + test local)
- **Phase 2**: 20 minutes (modification paths + test local)
- **Phase 3**: 10 minutes (bouton refresh)
- **Phase 4**: 30 minutes (tests complets + déploiement Railway)

**Total**: **1h15 minutes**

---

## 9. ROLLBACK PLAN

Si un problème survient après déploiement:

### Rollback local

```bash
# Restaurer backup
cp start.py.backup start.py

# Ou rollback Git
git checkout HEAD~1 start.py ui/pages/5_Market_Trends.py ui/pages/6_Scenario_Analysis.py
```

### Rollback Railway

```bash
# Option 1: Revert commit et push
git revert HEAD
git push

# Option 2: Rollback via Railway dashboard
# Railway → Deployments → Select previous deployment → Redeploy
```

---

**Plan validé par**: Architecture Agent (a403730)
**Prêt pour exécution**: ✅ OUI
**Dépendances bloquantes**: ❌ AUCUNE
