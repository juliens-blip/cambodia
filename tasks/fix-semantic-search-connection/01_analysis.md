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

## Commits

- `428bfb4` - fix: pre-load embedding model at API startup to prevent timeout
