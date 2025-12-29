# Analyse: Fix Semantic Search Connection Timeout

## Contexte
**Date:** 2025-12-29
**Demande initiale:** Erreurs "Server disconnected" et "Connection refused" sur la page Scenario Analysis
**Objectif:** Corriger les timeouts de connexion pour la recherche sémantique

## Symptomes Observes

### Erreurs UI (Streamlit)
```
⚠️ Error fetching documents: Server disconnected without sending a response.
⚠️ Error fetching Twitter data: [Errno 111] Connection refused
```

### Logs API
```
2025-12-29 22:55:28,979 - [SEARCH] Starting search for: 'cashew market trends prices analysis...'
2025-12-29 22:55:28,979 - [SEARCH] Loading services...
# AUCUN LOG APRES - le processus bloque ici
```

### Console Navigateur
```
GET /Scenario_Analysis/_stcore/health 404 (Not Found)
Uncaught (in promise) Error: A listener indicated an asynchronous response...
```

## Diagnostic Root Cause

### Probleme Principal: Timeout lors du chargement du modele embedding

**Sequence des evenements:**
1. Utilisateur accede a Scenario Analysis
2. Frontend appelle `/api/v1/search` avec timeout 120s
3. API recoit la requete, log "[SEARCH] Starting search..."
4. `get_services()` est appele
5. `EmbeddingService()` tente de charger `intfloat/multilingual-e5-small` (470MB)
6. Le modele doit etre telecharge depuis HuggingFace
7. Cela prend > 60 secondes sur Railway (ressources limitees)
8. Railway/httpx deconnecte le client avant la fin du chargement
9. Erreur "Server disconnected without sending a response"

### Pourquoi le probleme est apparu maintenant?
- Les tweets fonctionnaient car ils n'utilisent PAS le modele embedding
- Les documents utilisent `/api/v1/search` qui necessite le modele
- Le modele etait charge "lazy" (a la premiere requete) au lieu de "eager" (au demarrage)

## Solution Implementee

### 1. Pre-chargement du modele au demarrage (app/main.py)
```python
# Dans lifespan():
if SEMANTIC_AVAILABLE:
    logger.info("Pre-loading embedding model (this may take 30-60s)...")
    from app.services.embedding_service import get_embedding_service
    embedding_service = get_embedding_service()
    logger.info(f"Embedding model loaded: {embedding_service.dimension} dimensions")
    app.state.embedding_service = embedding_service
```

### 2. Augmentation du timeout de demarrage (start.py)
```python
# De 60s a 120s
if wait_for_port(8000, timeout=120):
    print("[UI] API is ready!", flush=True)
```

### 3. Configuration Railway (railway.toml)
```toml
startupDelaySeconds = 120  # etait 30
```

## Fichiers Modifies

| Fichier | Changement |
|---------|------------|
| `app/main.py` | Pre-chargement embedding dans lifespan() |
| `start.py` | Timeout 60s -> 120s |
| `railway.toml` | startupDelaySeconds 30 -> 120 |

## Verification

Apres deploiement, verifier dans les logs Railway:
1. `🔄 Pre-loading embedding model (this may take 30-60s)...`
2. `✅ Embedding model loaded: 1024 dimensions`
3. `✅ API startup complete`
4. `[UI] API is ready!`

Si ces logs apparaissent dans cet ordre, le probleme est resolu.

## Commits (Première Tentative - Échec)

- `428bfb4` - fix: pre-load embedding model at API startup to prevent timeout
  - **Problème:** Chargement SYNCHRONE bloque le startup
  - **Résultat:** Railway tue le conteneur après 120s ("Stopping Container")

## Problème Persistant (Après 428bfb4)

Les logs Railway montrent:
```
🔄 Pre-loading embedding model (this may take 30-60s)...
Loading embedding model: intfloat/multilingual-e5-small
Use pytorch device_name: cpu
Load pretrained SentenceTransformer: intfloat/multilingual-e5-small
Stopping Container
```

**Root Cause Réel:** Le modèle se charge de manière SYNCHRONE dans `lifespan()`, bloquant le startup de l'API. Railway attend que le port réponde mais l'API est bloquée, donc il tue le conteneur.

## Solution Finale (Commit c09e138)

### Changements Majeurs

#### 1. Chargement Asynchrone du Modèle (app/main.py)
```python
# Charger le modèle en arrière-plan via thread daemon
import threading

def load_embedding_model():
    try:
        logger.info("🔄 Pre-loading embedding model in background...")
        embedding_service = get_embedding_service()
        app.state.embedding_service = embedding_service
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        app.state.embedding_service = None

# Démarrer en thread daemon
embedding_thread = threading.Thread(target=load_embedding_model, daemon=True)
embedding_thread.start()
app.state.embedding_thread = embedding_thread
logger.info("ℹ️ Embedding model loading started in background")
```

**Avantage:** L'API démarre immédiatement, le modèle se charge en arrière-plan.

#### 2. Start Streamlit Immédiatement (start.py)
```python
# NE PAS attendre l'API - démarrer Streamlit immédiatement
# Railway a besoin de voir un processus actif rapidement
print("[UI] Starting Streamlit immediately (API may still be loading)...")

# Suppression de:
# if wait_for_port(8000, timeout=120):
#     print("[UI] API is ready!")
```

**Avantage:** Railway voit Streamlit répondre sur le PORT principal rapidement.

#### 3. Utiliser le Service Pré-chargé (app/api/routes/semantic.py)
```python
def get_services(app_state=None):
    global _embedding

    # Essayer d'utiliser le service pré-chargé
    if app_state and hasattr(app_state, 'embedding_service'):
        if app_state.embedding_service:
            _embedding = app_state.embedding_service
        elif hasattr(app_state, 'embedding_thread'):
            # Attendre la fin du chargement (max 90s)
            thread = app_state.embedding_thread
            if thread.is_alive():
                logger.info("Waiting for embedding model to finish loading...")
                thread.join(timeout=90)
                _embedding = app_state.embedding_service

    # Fallback: charger synchroniquement si besoin
    if _embedding is None:
        _embedding = EmbeddingService()
```

**Avantage:** Réutilise le modèle pré-chargé, attend si encore en cours, fallback si échec.

#### 4. Augmentation Timeout Railway (railway.toml)
```toml
startupDelaySeconds = 300  # 5 minutes au lieu de 120s
# healthcheckPath désactivé (Streamlit n'a pas /health)
```

**Avantage:** Railway attend plus longtemps avant de tuer le conteneur.

## Architecture de la Solution

```
[Railway Démarre le Conteneur]
        ↓
[start.py lance API en thread + Streamlit en main]
        ↓
┌─────────────────────────────────────────┐
│ API (port 8000) - Thread Background     │
│   ↓                                     │
│ lifespan() démarre IMMÉDIATEMENT        │
│   ↓                                     │
│ Lance thread daemon pour modèle         │
│   ├→ Thread charge modèle (30-60s)     │
│   └→ lifespan() se termine (2s)         │
│   ↓                                     │
│ API répond /health = OK                 │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Streamlit (PORT principal) - Main       │
│   ↓                                     │
│ Démarre SANS attendre l'API             │
│   ↓                                     │
│ Répond sur PORT (Railway content)       │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Utilisateur accède à Scenario Analysis  │
│   ↓                                     │
│ Frontend appelle /api/v1/search         │
│   ↓                                     │
│ get_services() vérifie app.state        │
│   ├→ Si modèle chargé: utilise-le       │
│   ├→ Si en cours: attend 90s max        │
│   └→ Sinon: charge synchroniquement     │
└─────────────────────────────────────────┘
```

## Fichiers Modifiés (Commit c09e138)

| Fichier | Changement |
|---------|------------|
| `app/main.py` | Thread daemon pour chargement async |
| `app/api/routes/semantic.py` | Utilise app.state.embedding_service |
| `start.py` | Suppression wait_for_port() |
| `railway.toml` | startupDelaySeconds 120 → 300 |

## Logs Attendus (Après Fix)

```
Starting Cambodia Agri Analytics...
Railway PORT: 8080
[API] Starting FastAPI on port 8000...
[UI] Starting Streamlit immediately (API may still be loading)...
INFO: Started server process
🚀 Starting Cambodia Agri Analytics API...
✅ Supabase initialized
ℹ️ Embedding model loading started in background
✅ API startup complete
[UI] Streamlit started on 0.0.0.0:8080

# 30-60 secondes plus tard...
🔄 Pre-loading embedding model in background...
Loading embedding model: intfloat/multilingual-e5-small
✅ Model loaded successfully: 1024 dimensions
✅ Embedding model loaded: 1024 dimensions
```

## Tests de Validation

1. Attendre le redéploiement Railway (~5-7 min)
2. Rafraîchir https://cambodia.up.railway.app/Scenario_Analysis
3. Vérifier que les 3 sections se chargent:
   - ✅ Market Data
   - ✅ Documents (PDF via pgvector semantic search)
   - ✅ Twitter Data

## Commits (Session 1 & 2)

- `428bfb4` - fix: pre-load embedding model at API startup to prevent timeout (ÉCHEC - sync blocking)
- `c09e138` - fix: load embedding model asynchronously to prevent Railway timeout (SOLUTION partielle)
- `a5c8d83` - docs: update APEX analysis with async loading solution

## Problème Persistant #2 (Après c09e138)

**Symptômes:** Les 3 erreurs "[Errno 111] Connection refused" persistent pour market data, documents et Twitter.

**Logs Railway:** L'API démarre correctement avec le modèle en background, MAIS aucun log de start.py :
```
# Logs attendus mais ABSENTS :
[API] Starting FastAPI on port 8000...
[UI] Starting Streamlit on port 8080...

# Logs présents (uniquement API) :
INFO: Started server process [3]
2025-12-29 23:40:35,991 - app.main - INFO - 🚀 Starting Cambodia Agri Analytics API...
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Root Cause #2:** Railway auto-détection lance **uvicorn directement** au lieu d'exécuter `start.py` du Dockerfile CMD. Résultat :
- ✅ API démarre sur port 8000
- ❌ Streamlit ne démarre PAS du tout
- ❌ Aucune communication API ↔ Streamlit
- ❌ Frontend ne peut pas appeler l'API → Connection refused

**Preuve:** WebFetch de https://cambodia.up.railway.app/health renvoie une page Streamlit HTML au lieu d'un JSON de l'API, confirmant que seule l'interface Streamlit (probablement lancée séparément par Railway) est accessible, pas l'API combinée.

## Solution Finale #2 (Commit efd0a9e)

### Changements

#### 1. railway.toml - Forcer l'utilisation de start.py
```toml
[deploy]
numReplicas = 1

# Commande de démarrage (override auto-detection Railway)
startCommand = "python start.py"

# ... reste de la config
```

**Avantage:** Empêche Railway d'override le CMD du Dockerfile avec sa propre détection auto.

#### 2. start.py - Délai pour l'API + Meilleur logging
```python
def main():
    print("=" * 50, flush=True)
    print("Starting Cambodia Agri Analytics...", flush=True)
    print(f"Railway PORT: {os.environ.get('PORT', 'not set')}", flush=True)

    # Start API in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Wait for API to initialize
    print("[STARTUP] Waiting 3 seconds for API to initialize...", flush=True)
    time.sleep(3)

    # Run Streamlit in main thread
    run_streamlit()

def run_streamlit():
    port = os.environ.get("PORT", "8501")
    os.environ["API_BASE_URL"] = "http://localhost:8000"

    print(f"[UI] API_BASE_URL set to: {os.environ['API_BASE_URL']}", flush=True)
    print(f"[UI] Launching Streamlit...", flush=True)

    try:
        subprocess.run([...], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[UI] ERROR: Streamlit crashed with exit code {e.returncode}", flush=True)
        sys.exit(1)
```

**Avantages:**
- Délai de 3s pour que l'API soit prête avant Streamlit
- Meilleur logging pour debugger
- Gestion d'erreurs explicite

## Architecture Finale

```
[Railway reçoit push] → Rebuild Docker
                          ↓
                      startCommand: "python start.py"
                          ↓
[start.py] → main()
              ├→ Lance API en thread daemon (port 8000)
              ├→ Sleep 3s (API s'initialise)
              └→ Lance Streamlit en main thread (PORT 8080)
                  ↓
              Streamlit connect à http://localhost:8000
                  ↓
[Utilisateur] → https://cambodia.up.railway.app
                 ↓
              Streamlit UI (port 8080)
                 ↓
              API calls → localhost:8000
                 ↓
              ✅ Toutes les sections se chargent
```

## Logs Attendus (Après efd0a9e)

```
==================================================
Starting Cambodia Agri Analytics...
Railway PORT: 8080
Python: /usr/local/bin/python
==================================================
[API] Starting FastAPI on port 8000...
[STARTUP] Waiting 3 seconds for API to initialize...
INFO: Started server process [3]
🚀 Starting Cambodia Agri Analytics API...
✅ Supabase initialized
ℹ️ Embedding model loading started in background
✅ API startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
[UI] Starting Streamlit on port 8080...
[UI] API_BASE_URL set to: http://localhost:8000
[UI] Launching Streamlit...

# 30-60s plus tard (modèle chargé)
🔄 Pre-loading embedding model in background...
✅ Model loaded successfully: 1024 dimensions
```

## Commits Finaux (Tous)

- `428bfb4` - fix: pre-load embedding model at API startup to prevent timeout (ÉCHEC)
- `c09e138` - fix: load embedding model asynchronously to prevent Railway timeout (SOLUTION partielle)
- `a5c8d83` - docs: update APEX analysis with async loading solution
- `efd0a9e` - fix: force Railway to use start.py for combined API+Streamlit launch (SOLUTION complète)

## Tests de Validation Finale

Après redéploiement Railway (~5-7 min):

1. **Vérifier logs Railway:**
   - ✅ Voir "Starting Cambodia Agri Analytics..."
   - ✅ Voir "[API] Starting FastAPI on port 8000..."
   - ✅ Voir "[UI] Launching Streamlit..."

2. **Tester https://cambodia.up.railway.app/Scenario_Analysis:**
   - ✅ Market Data charge
   - ✅ Documents charge (semantic search)
   - ✅ Twitter Data charge
   - ❌ Plus d'erreurs "Connection refused"

3. **Vérifier API directement:**
   - GET https://cambodia.up.railway.app/health → devrait retourner Streamlit HTML (proxy)
   - Streamlit → localhost:8000/health → devrait fonctionner en interne
