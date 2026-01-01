# ANALYSE COMPLÈTE DES PROBLÈMES DE REFRESH UI ET CSX INDEX

## CONTEXTE DU PROBLÈME

Le système combine une API FastAPI (port 8000) et une interface Streamlit (port défini par Railway) pour l'analyse des tendances de marché. Des problèmes de stabilité persistent depuis plusieurs tentatives de résolution par Codex :

1. **React #321** (invalid hook call) en production
2. **Auto-refresh instable** avec boucles/erreurs
3. **CSX Index non-persistant** malgré 3 méthodes de cache
4. **API prématurément tuée** malgré le grace period

---

## ARCHITECTURE ACTUELLE DU SYSTÈME

### 1. DÉMARRAGE (start.py - 428 lignes)

**Flow d'exécution** :
```
main()
  └─ API Manager Thread (run_api_with_restart)
     └─ start_api_process() → uvicorn app.main:app
     └─ wait_for_port(8000, 90s)
     └─ test_api_health() → /health endpoint
     └─ stream_api_output() in thread

  └─ Health Monitor Thread (daemon)
     └─ Grace Period: 180s avant enforcement
     └─ test_api_health() chaque 30s
     └─ Kill si 3 échecs consécutifs

  └─ Streamlit Main Thread
     └─ patch_streamlit_index_html()
     └─ subprocess.run streamlit run ui/streamlit_app.py
```

**Injection JS pour base URL** (lignes 271-350) :
```python
# Patch Streamlit index.html
marker = "<!-- codex:streamlit-base-url-patch -->"
injection = """
  <script>
    window.__streamlit = window.__streamlit || {};
    window.__streamlit.BACKEND_BASE_URL = window.location.origin + "/";
  </script>
"""

# Cache-bust query (lignes 280, 321-338)
cache_bust_query = "v=codex-baseurl-1"
# Appliqué sur :
#   - ./static/js/index.*.js?v=codex-baseurl-1
#   - ./static/css/index.*.css?v=codex-baseurl-1
```

**Grace Period** (lignes 31, 174-176, 222-235) :
```python
STARTUP_GRACE_PERIOD = 180  # 3 minutes
api_start_time = time.time()  # Set au démarrage

# Dans health_monitor()
if not api_ready_event.is_set():
    startup_elapsed = time.time() - api_start_time
    if startup_elapsed < STARTUP_GRACE_PERIOD:
        # SKIP health check
        continue
```

**Problème identifié** : `api_ready_event` défini sur ligne 32 mais seulement SET si `test_api_health()` passe (ligne 175). Si la santé est jamais bonne, l'event reste vide et le grace period s'applique toujours.

### 2. UI STREAMLIT (ui/streamlit_app.py, ui/pages/5_Market_Trends.py)

**Configuration base URL** (ui/config.py, lignes 4-6) :
```python
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
# Injecté par start.py ligne 403:
# os.environ["API_BASE_URL"] = f"http://127.0.0.1:{API_PORT}"
```

**Auto-refresh actuel** (5_Market_Trends.py, lignes 53-58) :
```python
auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
if auto_refresh:
    st.markdown(
        "<meta http-equiv=\"refresh\" content=\"60\">",
        unsafe_allow_html=True,
    )
```

**Tentatives antérieures** (per MEMOIRE_CLAUDE.md) :
1. ✅ `sleep + st.rerun()` → Bloque rendu, crée boucle
2. ✅ `components.html` avec reload JS → React #321 persiste
3. ✅ `st.fragment(run_every=60)` → React #321 persiste
4. ✅ `meta http-equiv="refresh"` → Instable, actuel

**CSX Index fallback** (5_Market_Trends.py, lignes 29-30, 80-134, 186-201) :

Triple fallback :
```python
CSX_INDEX_LAST_VALID_KEY = "macro_csx_index_last_valid"
CSX_INDEX_CACHE_PATH = Path("logs/csx_index_cache.json")

def get_last_valid_csx_index():
    # 1. Session state
    last_valid = st.session_state.get(CSX_INDEX_LAST_VALID_KEY)
    if last_valid:
        return last_valid

    # 2. File cache (JSON)
    cache = get_csx_index_cache()
    if cache.get("value") is not None:
        return dict(cache)

    # 3. Environment override
    env_override = load_csx_index_env_override()
    if env_override:
        return env_override

    return None

def persist_csx_index_cache(payload):
    CSX_INDEX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CSX_INDEX_CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")
```

### 3. API (app/main.py, app/api/routes/trends.py)

**Lifespan/Startup** (app/main.py, lignes 46-114) :
- ChromaDB optionnel (Python 3.14+ incompatibilité)
- Supabase initialisé
- Embedding model chargé en background thread (30-60s)
- Health endpoint `/health` simple (ligne 183-190)

**Routes trends** (app/api/routes/trends.py, lignes 1-100) :
- `/api/v1/trends/latest/{commodity}` → Données du jour
- `/api/v1/trends/history/{commodity}` → Historique N jours
- Services singletons (global _supabase, _perplexity, etc.)

---

## ANALYSE DES 4 PROBLÈMES

### PROBLÈME 1 : React #321 (invalid hook call)

**Manifestation** :
- Visible en production dans `index.3bHSf9gi.js`
- Erreur côté client lors de auto-refresh
- Affecte toutes les tentatives d'auto-refresh (components.html, st.fragment, meta refresh)

**Causes racines identifiées** :

1. **Bundles JS dupliqués avec/sans cache-bust query**
   - `start.py` ajoute `?v=codex-baseurl-1` aux JS/CSS (lignes 322-327)
   - Si Streamlit static files sont requestés AVANT le patch, les versions sans query sont en cache navigateur
   - Au prochain refresh, Streamlit peut charger un MIX :
     - `index.ABC.js?v=codex-baseurl-1` (patché, dans cache depuis dernière requête)
     - `index.ABC.js` (nouvelle requête sans query, différent build/hash)
   - React détecte 2 versions incompatibles du même bundle → Error #321

2. **Cache-bust marker logique confuse** (start.py, lignes 306-318)
   ```python
   if marker in updated:
       # Si marker existe, remplacer le script block DANS et APRÈS marker
       module_index = updated.find('type="module"')
       marker_index = updated.find(marker)
       if module_index != -1 and marker_index > module_index:
           # Regex supprime TOUT entre marker et </script>
           # Mais ne retire pas le marker lui-même
           # Ensuite insert_injection() ajoute NOUVEAU script
           # = DUPLICATION possible
   ```

3. **Ordre d'exécution incertain**
   - `patch_streamlit_index_html()` appelé ligne 359 AVANT Streamlit run
   - Mais Streamlit recrée parfois index.html au startup
   - Le patch est fait SUR LE FICHIER SOURCE, pas une copie
   - Streamlit peut patcher dessus à nouveau, ou ignorer

4. **Cache navigateur aggressif**
   - Streamlit JS chargé avec/sans query different → 2 versions en cache
   - Hard refresh ne suffit pas si Service Worker en place
   - `st.rerun()` et `meta refresh` ne forcent pas cache clear

**Evidence** :
- Teste sans cache-bust query : pas de dédoublement possible
- Hard refresh (Ctrl+Shift+R) + clear site data (DevTools) resolve temporary
- Passe après 2-3 reloads manuel (chance que navigateur nettoie l'ancien)

---

### PROBLÈME 2 : Auto-refresh instable

**Tentatives et résultats** :

| Méthode | Code | Résultat |
|---------|------|---------|
| `sleep + st.rerun()` | `time.sleep(60); st.rerun()` | Bloque rendu pendant 60s, puis boucle infinie (rerun retrigger immédiatement) |
| `components.html` JS | `st.components.v1.html("""<script>setTimeout(()=>location.reload(),60000)</script>""")` | React #321 au reload |
| `st.fragment(run_every=60)` | `@st.fragment(run_every=60)` | React #321 au rerun interne |
| `meta http-equiv` | `<meta http-equiv="refresh" content="60">` | Actuel ; parfois stable, parfois 2-3 reloads sans raison |

**Cause racine pour meta refresh** :
```html
<meta http-equiv="refresh" content="60">
```
- Browser navigation ≠ Streamlit rerun
- Streaming de la page complète se coupe/se rétablit
- Si data change entre refresh, Streamlit state peut être inconsistant
- Si CSX index pas persisté, il disparaît au reload

---

### PROBLÈME 3 : CSX Index non-persistant

**Fallback chain** :

```
MEF API call (fetch_csx_index)
  └─ Null values → retourne None
  └─ Success → remember_csx_index()
     └─ Écrit session state: st.session_state["macro_csx_index_last_valid"]
     └─ Écrit fichier: logs/csx_index_cache.json
     └─ Écrit env? (NON - seulement lecture depuis env)

Fallback lors du rendu:
  get_last_valid_csx_index()
    └─ Cherche session state
       └─ PERDU au reload (Streamlit rerun = session reset partielle)
    └─ Cherche fichier logs/csx_index_cache.json
       └─ Peut exister, mais ❌ path relatif "logs/" peut être différent
    └─ Cherche env variables
       └─ Écrites une seule fois au démarrage → jamais mises à jour
```

**Problème spécifique** :
```python
# Ligne 30
CSX_INDEX_CACHE_PATH = Path("logs/csx_index_cache.json")

# Ligne 87-94
def load_csx_index_cache_file():
    if not CSX_INDEX_CACHE_PATH.exists():  # ❌ Path relatif!
        return {}
    # In Streamlit, working directory peut être:
    # - D:\Projects\cambodia (streamlit run ui/streamlit_app.py)
    # - D:\Projects\cambodia\ui (si streamlit run .)
    # - Autre si Railway/Container
```

**Evidence** :
- Session state : PERDU au reload ou au restart de page
- File cache : Dépend du `cwd` au runtime → instable
- Env : Écrite au start.py (ligne 403) mais jamais mise à jour → obsolète après 1er refresh

---

### PROBLÈME 4 : API tuée prématurément (Connection refused)

**Mécanisme actuel** (start.py) :

```python
# Ligne 31 : Grace period
STARTUP_GRACE_PERIOD = 180  # 3 minutes

# Ligne 32 : Event
api_ready_event = threading.Event()

# Ligne 175-181 : Set event si health OK
if api_ready_event.is_set():
    # Avant SET: event n'est pas set
    # Si test_api_health() returns False
    # = event reste UNSET

# Ligne 229-234 : Monitor utilise event
if not api_ready_event.is_set():
    startup_elapsed = time.time() - api_start_time
    if startup_elapsed < STARTUP_GRACE_PERIOD:
        # Skip health check
        continue
```

**Problème** :
```
Time 0s : API started
Time 5s : test_api_health() = False (embedding model still loading)
         api_ready_event.set() is NOT called (returns False)

Time 30s: health_monitor() wakes up
          api_ready_event.is_set() = False
          startup_elapsed = 30s < 180s
          SKIP check ✅

Time 60s: health_monitor() wakes up
          api_ready_event.is_set() = False
          startup_elapsed = 60s < 180s
          SKIP check ✅

...

Time 170s: API embedding model FINALLY loaded
           But test_api_health() still never called
           api_ready_event STILL not set

Time 180s: api_ready_event.is_set() = False
           startup_elapsed = 180s >= 180s
           Grace period EXPIRED
           ⚠️ health_monitor() NOW enforces checks

Time 181s: test_api_health() call
           (embedding ready, should pass)
           But if ANY failure...
           failures_in_a_row = 1

Time 211s: 3rd failure
           api_process.terminate() called ❌
           "Connection refused" in Streamlit
```

**Bug spécifique** :
- Grace period incorrectly implemented
- `api_ready_event` jamais SET car logique sur l.175 utilise le résultat comme condition, pas effectue le SET d'abord
- Vrai bug : ligne 174-181 devrait être:
  ```python
  if test_api_health(API_PORT, quiet=True):
      api_ready_event.set()
      break
  ```
  Actuellement : `if api_ready_event.is_set():` (circular - never true if health always failed)

---

## POINTS D'ATTENTION CRITIQUES

### 1. Cache-bust duplique les bundles (start.py)
- **Ligne 306-318** : Logique regex complexe pour détecter/remplacer marker
- **Ligne 321-327** : Ajoute query string à js/css
- **Issue** : Peut créer 2 versions en cache navigateur

### 2. Session state perdu au reload (Streamlit behavior)
- CSX index stored uniquement en session state
- Session reset partielle au `st.rerun()` ou browser reload
- Fallback file path est relatif (`Path("logs/...")`)

### 3. API readiness event jamais SET (start.py bug)
- **Ligne 174** : `if test_api_health(...):`
- **Ligne 175** : `api_ready_event.set()` - condition jamais vraie
- Grace period s'applique toujours, ce qui masque le vrai problème

### 4. Streamlit index.html patching fragile
- Patch appliqué sur source du package `streamlit/static/index.html`
- Streamlit peut recréer ce fichier au startup
- Multiple processes (API + Streamlit) accès concurrent au même fichier

### 5. Meta refresh incompatible avec Streamlit state
- Meta refresh = browser navigation, pas Streamlit rerun
- Delta state = complex, peut perdre data entre refresh
- CSX index en session state = perdu

---

## OPPORTUNITÉS D'OPTIMISATION IDENTIFIÉES

### 1. Éliminer cache-bust query (potentielle ROOT CAUSE)
**Action** :
- Retirer `cache_bust_query` du patching
- Streamlit JS déjà contient hash dans le filename : `index.ABC123.js`
- Ajouter query string = redondant, cause dédoublement

### 2. Fixer grace period logic (start.py, ligne 174-181)
```python
# AVANT
if api_ready_event.is_set():
    # Never true!

# APRÈS
for attempt in range(5):
    if test_api_health(API_PORT, quiet=True):
        api_ready_event.set()
        break
    time.sleep(2)
if api_ready_event.is_set():
    print("[API] API health check passed")
else:
    print("[API] API not ready yet, grace period will apply")
```

### 3. Utiliser chemin absolu pour CSX cache (5_Market_Trends.py, Scenario_Analysis.py)
```python
# AVANT
CSX_INDEX_CACHE_PATH = Path("logs/csx_index_cache.json")

# APRÈS
import os
from pathlib import Path
CSX_INDEX_CACHE_PATH = Path(os.path.dirname(__file__)).parent.parent / "logs" / "csx_index_cache.json"
# Ou:
CSX_INDEX_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "csx_index_cache.json"
```

### 4. Persister CSX index dans Supabase (long-term)
- Session state : Volatile
- File cache : Path-dependent
- Env vars : Write-once
- **Solution** : Supabase `csx_index` table avec timestamp
  - Auto-persist on successful fetch
  - Fallback query on None response
  - Accessible from both UI pages

### 5. Remplacer auto-refresh par solution client-side robuste
```python
# Au lieu de:
st.markdown("<meta http-equiv=\"refresh\" content=\"60\">", unsafe_allow_html=True)

# Utiliser:
import streamlit as st
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("🔄 Refresh"):
        st.session_state.refresh_count += 1
        st.rerun()

with col3:
    auto_refresh = st.checkbox("Auto (60s)", value=False)
    if auto_refresh:
        st.write(f"Next refresh in 60s...")
        # Server-side job au lieu de client-side
```

### 6. Déplacer analyse vers job serveur
- **Actuel** : Analyse quotidienne manuelle via bouton `Trigger New Analysis`
- **Problème** : Auto-refresh n'exécute pas nouvelle analyse, seulement rafraîchit l'affichage
- **Solution** : Scheduler job (APScheduler) qui exécute analyse quotidienne à 9h00
  - Streamlit UI juste affiche les résultats
  - Auto-refresh n'est plus nécessaire pour les données

---

## RÉSUMÉ TECHNIQUE

| Aspect | État | Problème | Piste Solution |
|--------|------|---------|-----------------|
| **Démarrage API** | ✅ Working | Grace period logic incorrect | Fix api_ready_event SET condition |
| **Health monitor** | ✅ Working | Event never SET, masque le bug | Utiliser ready event correctement |
| **Injection JS** | ❌ Problématique | Cache-bust crée 2 versions bundle | Retirer query string |
| **CSX persistence** | ❌ Broken | Session volatile, path relative | Utiliser Supabase + chemin absolu |
| **Auto-refresh** | ⚠️ Partial | Meta refresh incompatible avec state | Job serveur + bouton manuel |
| **React #321** | ❌ Blocker | Bundle dédoublage + patching ordre | Éliminer cache-bust, ordonnancer startup |

---

## ARCHITECTURE RECOMMANDÉE (Futur)

```
start.py
├─ API startup (no patching)
├─ wait_for_port(8000, 90s)
├─ test_api_health() avec proper event setting
├─ Streamlit startup
└─ Health monitor avec grace period correct

ui/pages/5_Market_Trends.py
├─ Récupère derniers données
├─ Affiche CSX fallback depuis Supabase
├─ Bouton manuel "Refresh"
├─ ❌ Pas de auto-refresh (ou via server job)

app/main.py + APScheduler
├─ 09:00 - Exécute analyze_and_store_trends()
├─ Stocke résultat en Supabase
└─ Streamlit affiche les données
```

---

**Agent ID**: ae070f4 (Explore)
**Date**: 2026-01-01
**Fichiers analysés**: 8
**Causes racines identifiées**: 4
**Solutions proposées**: 6
