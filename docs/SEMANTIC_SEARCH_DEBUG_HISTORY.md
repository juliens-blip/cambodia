# Historique de Débogage - Recherche Sémantique Cambodia Agri Analytics

**Date**: 30 décembre 2024
**Contexte**: Application déployée sur Railway (FastAPI + Streamlit dans un seul conteneur)

---

## PROBLÈME INITIAL

La page "Scenario Analysis" affichait "0 documents analyzed" alors que 34 documents PDF de Google Drive avaient été collectés dans la table `context_documents`.

### Architecture
- **Frontend**: Streamlit (port Railway dynamique, ex: 8080)
- **Backend**: FastAPI (port 8000 interne)
- **Base de données**: Supabase avec pgvector pour les embeddings
- **Modèle d'embedding**: `intfloat/multilingual-e5-small` (384 dimensions, ~470MB)

---

## TENTATIVE 1: Diagnostic Initial

### Action
Vérification de l'état des tables Supabase.

### Résultat
- `context_documents`: 34 documents présents ✅
- `document_embeddings`: 0 embeddings ❌
- Fonction `match_documents`: existait mais avec mauvaise dimension

### Conclusion
Les documents n'avaient jamais été indexés (embeddings non générés).

---

## TENTATIVE 2: Migration SQL pour match_documents

### Problème
La fonction `match_documents` attendait `vector(384)` mais une ancienne version avec `vector(1024)` existait.

### Action
Création de `scripts/fix_match_documents.sql`:
```sql
DROP FUNCTION IF EXISTS match_documents CASCADE;
CREATE FUNCTION match_documents(
    query_embedding vector(384),
    ...
)
```

### Résultat
**ÉCHEC** - Erreur "function name not unique" car plusieurs versions de la fonction existaient.

### Solution
Création de `scripts/fix_match_documents_v2.sql` avec suppression dynamique:
```sql
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN SELECT ... FROM pg_proc WHERE proname = 'match_documents'
    LOOP
        EXECUTE r.drop_cmd;
    END LOOP;
END $$;
```

### Résultat après v2
**SUCCÈS** - Fonction recréée correctement avec 384 dimensions.

---

## TENTATIVE 3: Script d'indexation local

### Action
Création de `scripts/index_existing_documents.py` pour indexer les 34 documents localement.

### Résultat
**ÉCHEC** - Erreur "No space left on device" sur le PC de l'utilisateur (seulement 22MB libres, modèle = 470MB).

### Conclusion
L'indexation doit se faire sur Railway où le modèle est déjà en cache.

---

## TENTATIVE 4: Endpoints Admin pour indexation sur Railway

### Action
Création de `app/api/routes/admin.py` avec:
- `POST /api/v1/admin/index-documents` - Lance l'indexation en background
- `GET /api/v1/admin/indexation-status` - Vérifie le statut
- `DELETE /api/v1/admin/clear-embeddings` - Supprime les embeddings

### Résultat
**SUCCÈS PARTIEL** - Endpoints créés mais erreur "Connection refused" sur l'UI.

---

## TENTATIVE 5: Fix "Connection refused" - Problème API non accessible

### Diagnostic
L'API (port 8000) n'était pas accessible depuis Streamlit. Logs montraient que l'API démarrait mais Streamlit obtenait "Connection refused".

### Cause identifiée
`start.py` utilisait un thread daemon pour l'API. Si le thread crashait, pas de restart.

### Action (start.py v2.0)
- Ajout de `wait_for_port()` pour attendre que l'API soit prête
- Utilisation de `127.0.0.1` au lieu de `localhost`
- Augmentation du timeout à 90 secondes

### Résultat
**ÉCHEC PARTIEL** - L'API démarrait mais crashait parfois.

---

## TENTATIVE 6: start.py v3.0 - Gestion robuste des processus

### Action
Refonte complète de `start.py`:
```python
# Changements majeurs:
1. Thread non-daemon pour l'API (ne meurt pas si Streamlit crash)
2. Auto-restart si l'API crash (jusqu'à 5 tentatives)
3. Health monitoring toutes les 30 secondes
4. Gestion des signaux SIGTERM/SIGINT
5. Cleanup propre des processus
```

### Résultat
**SUCCÈS** - L'API reste stable et redémarre automatiquement si nécessaire.

---

## TENTATIVE 7: Première indexation réussie

### Action
Via la page Admin, clic sur "Start Indexation".

### Résultat
**SUCCÈS** - 146 chunks créés dans `document_embeddings`.

### Mais...
La recherche sémantique retournait toujours 0 documents sur Scenario Analysis.

---

## TENTATIVE 8: Debugging de la recherche

### Diagnostic
Ajout de logging dans `6_Scenario_Analysis.py`:
```python
print(f"[DEBUG] Searching documents: {url}", flush=True)
print(f"[DEBUG] Search response: {response.status_code}", flush=True)
```

### Découverte
Pas de logs `[DEBUG]` dans les logs Railway = la fonction n'était pas appelée!

### Cause
`@st.cache_data(ttl=3600)` cachait le résultat `None` pendant 1 heure (la première recherche avait échoué quand le modèle n'était pas chargé).

### Action
1. Suppression du cache sur `fetch_historical_docs()`
2. Ajout d'un bouton "Clear Cache" dans la sidebar
3. Baisse du seuil de similarité de 0.5 à 0.3

### Résultat après fix
La recherche était maintenant appelée, mais retournait une erreur 500.

---

## TENTATIVE 9: Erreur de dimensions 1024 vs 384

### Diagnostic
Logs montraient:
```
[DEBUG] Search error: "different vector dimensions 1024 and 384"
```

### Cause
Les 146 embeddings stockés étaient en **1024 dimensions**, mais:
- Le modèle `multilingual-e5-small` produit **384 dimensions**
- La fonction `match_documents` attend **384 dimensions**

### Hypothèse sur l'origine du problème
Lors de la première indexation, soit:
1. Un autre modèle était utilisé (e5-large = 1024D)
2. Ou une ancienne version du code utilisait 1024D

### Action
1. `TRUNCATE TABLE document_embeddings;`
2. `ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(384);`
3. Re-lancer l'indexation

---

## TENTATIVE 10: Crash OOM lors de la ré-indexation

### Problème
Lors de "Start Indexation", l'API crashait avec `exit code -9` (OOM Killer).

### Cause
`admin.py` créait un **nouveau** `EmbeddingService()` dans la tâche background:
```python
# PROBLÈME: Charge le modèle une 2ème fois (470MB)
embedding_service = EmbeddingService()
```

Avec le modèle déjà chargé dans le processus principal + le nouveau = dépassement mémoire.

### Action
Modification pour utiliser le singleton:
```python
# SOLUTION: Réutilise le modèle déjà chargé
from app.services.embedding_service import get_embedding_service
embedding_service = get_embedding_service()
```

### Optimisations supplémentaires
1. Traitement par batch de 5 documents
2. `gc.collect()` après chaque batch pour libérer la mémoire
3. Insertion par batch de 20 chunks
4. Logging détaillé pour suivre la progression

### Résultat
**EN COURS** - La modification a été faite, en attente de test.

---

## ÉTAT ACTUEL

### Ce qui fonctionne ✅
- API stable avec auto-restart (start.py v3.0)
- 34 documents dans `context_documents`
- Fonction `match_documents` avec 384 dimensions
- Colonne `embedding` type `vector(384)`
- Tweets affichés correctement (5 tweets)
- Page Admin fonctionnelle

### Ce qui ne fonctionne pas encore ❌
- Recherche sémantique: 0 documents (table `document_embeddings` vide après TRUNCATE)
- Indexation: crash OOM (fix en cours de déploiement)

### Prochaines étapes
1. Déployer le fix pour l'indexation (singleton EmbeddingService)
2. Re-lancer l'indexation
3. Vérifier que 146 chunks sont créés avec 384 dimensions
4. Tester la recherche sémantique

---

## FICHIERS MODIFIÉS

| Fichier | Description |
|---------|-------------|
| `start.py` | v3.0 - Gestion robuste des processus avec auto-restart |
| `app/api/routes/admin.py` | Endpoints d'indexation + fix singleton |
| `app/api/routes/semantic.py` | Recherche sémantique (inchangé mais vérifié) |
| `ui/pages/6_Scenario_Analysis.py` | Suppression cache, ajout debug, bouton Clear Cache |
| `ui/pages/4_Admin.py` | UI pour indexation + test search |
| `ui/config.py` | URLs admin ajoutées |
| `scripts/fix_match_documents_384d.sql` | Migration SQL pour 384D |

---

## VARIABLES D'ENVIRONNEMENT IMPORTANTES

```
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJ...
API_BASE_URL=http://127.0.0.1:8000
PORT=8080 (Railway)
```

---

## COMMANDES UTILES

### Vérifier les embeddings
```sql
SELECT COUNT(*) FROM document_embeddings;
SELECT embedding FROM document_embeddings LIMIT 1;  -- Vérifier dimension
```

### Vérifier la colonne
```sql
SELECT format_type(a.atttypid, a.atttypmod)
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
WHERE c.relname = 'document_embeddings' AND a.attname = 'embedding';
```

### Vider et recréer
```sql
TRUNCATE TABLE document_embeddings;
ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(384);
```

---

## LOGS À SURVEILLER

### Bon démarrage
```
START.PY LOADED - Version 3.0
[MAIN] Starting API manager thread...
[API] API is ready on port 8000
[MAIN] ✅ API health check passed!
```

### Indexation réussie
```
🚀 Starting documents indexation...
✅ Embedding model ready: 384D
📚 Found 34 documents to index
📦 Processing batch 1: docs 1-5
✅ Inserted 25 chunks (total: 25)
...
🎉 Indexation complete: 34 docs, ~146 chunks
```

### Erreur OOM (à éviter)
```
[API] Process exited with code -9
[API] Restarting API...
```

---

## LEÇONS APPRISES

1. **Singleton pour les modèles ML**: Ne jamais charger le modèle plusieurs fois en mémoire
2. **Cache Streamlit**: Peut cacher des erreurs - utiliser avec précaution pour les appels API
3. **Dimensions vectorielles**: Doivent correspondre partout (modèle, SQL, table)
4. **Railway mémoire limitée**: ~512MB, le modèle seul fait 470MB
5. **Threads daemon**: Meurent avec le processus parent - utiliser non-daemon + cleanup

---

*Document créé pour permettre à un autre modèle IA de comprendre le contexte et continuer le débogage.*
