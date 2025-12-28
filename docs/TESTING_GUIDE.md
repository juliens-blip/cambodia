# Testing Guide - Daily Pipeline

## Prérequis

### 1. Installer les Dépendances

```bash
# Depuis la racine du projet
pip install -r requirements.txt
```

### 2. Vérifier la Configuration

```bash
# Vérifier que .env contient les clés nécessaires
cat .env | grep -E "SUPABASE|PERPLEXITY|CLAUDE|CHROMA"
```

Configuration minimale requise:
```bash
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJhbGci...
PERPLEXITY_API_KEY=pplx-...
CLAUDE_MOCK_MODE=true
```

### 3. ChromaDB (Optionnel)

**Option A**: Serveur ChromaDB (recommandé)
```bash
# Installer ChromaDB
pip install chromadb

# Démarrer le serveur
chroma run --host localhost --port 8000
```

**Option B**: Mode embarqué (fallback)
- Le service détectera automatiquement si le serveur n'est pas disponible
- Utilisera le stockage local dans `chroma_data/`

## Modes de Test

### Mode 1: Dry Run (Vérification Services)

Vérifie que tous les services sont accessibles **SANS** exécuter le pipeline.

```bash
python scripts/test_daily_pipeline.py --dry-run
```

**Output attendu**:
```
================================================================================
CHECKING SERVICES
================================================================================
✅ Supabase connected - Database stats: {'commodities': 2, 'prices': 1415, ...}
✅ ChromaDB connected - Collections: {'perplexity_analyses': {'count': 0}, ...}
ℹ️  Perplexity in MOCK mode - skipping API check
✅ Claude service initialized (MOCK mode: True)

================================================================================
✅ ALL SERVICES READY
================================================================================
```

**Utilité**:
- Vérifier la configuration avant exécution
- Diagnostiquer problèmes de connexion
- Pas de coût API, pas de modifications en base

### Mode 2: MOCK Mode (Test Complet sans Coûts)

Exécute le pipeline complet avec Perplexity en **MOCK** (pas d'appels API réels).

```bash
python scripts/test_daily_pipeline.py
```

**Ce qui se passe**:
1. ✅ Collecte de données (MEF, WITS, ODC, GDrive)
2. ✅ Stockage dans Supabase + ChromaDB
3. 🔄 **MOCK** Perplexity (réponses pré-générées)
4. ✅ Rapports Claude (templates)

**Durée**: 2-5 minutes

**Coût API**: **$0.00** (mode MOCK complet)

**Output attendu**:
```
================================================================================
RUNNING DAILY PIPELINE TEST (MOCK=True)
================================================================================
🔄 Starting data collection from all sources...
✅ Collection complete: MEF=45, WITS=32, ODC=12, GDrive=3
💾 Storing data in Supabase + ChromaDB...
✅ Data stored successfully

🔄 MOCK: Generating daily price analysis for cashew
🔄 MOCK: Generating daily price analysis for rubber
✅ Perplexity query successful for cashew (price)
✅ Perplexity query successful for rubber (price)

✅ Generated daily report for cashew (MOCK)
✅ Generated daily report for rubber (MOCK)

✅ DAILY pipeline complete!

================================================================================
VERIFYING RESULTS (AFTER PIPELINE)
================================================================================
Supabase table changes:
  ✅ perplexity_analyses: 0 → 2 (+2)
  ✅ claude_reports: 0 → 2 (+2)
  ✅ prices: 1415 → 1507 (+92)

ChromaDB collection changes:
  ✅ perplexity_analyses: 0 → 2 (+2)
  ✅ claude_reports: 0 → 2 (+2)
  ✅ commodity_prices: 2830 → 2922 (+92)

Expected results:
  ✅ Perplexity analyses: 2 added (expected: 2)
  ✅ Claude reports: 2 added (expected: 2)
  ✅ ChromaDB embeddings: 2 analyses, 2 reports

================================================================================
✅ ALL TESTS PASSED
================================================================================

📁 Full results saved to: logs/pipeline_test_results_20250115_143022.json
```

### Mode 3: REAL Mode (Production avec Perplexity Réel)

⚠️ **ATTENTION**: Utilise de vrais crédits Perplexity API (environ $0.002 par exécution)

```bash
python scripts/test_daily_pipeline.py --real
```

**Ce qui se passe**:
1. ✅ Collecte de données
2. ✅ Stockage Supabase + ChromaDB
3. 💰 **REAL** Perplexity API calls (2 requests, ~$0.002)
4. ✅ Rapports Claude (templates si CLAUDE_MOCK_MODE=true)

**Durée**: 3-7 minutes (Perplexity API prend 15-30s par requête)

**Coût API**:
- Perplexity: 2 × $0.001 = **$0.002**
- Claude: $0 (si MOCK mode)

**Quand utiliser**:
- Avant déploiement production
- Pour vérifier la qualité des analyses Perplexity
- Une fois par semaine max pendant développement

### Mode 4: Skip Collectors (Test Analyse Uniquement)

Teste uniquement la génération d'analyses et rapports, sans collecter de nouvelles données.

```bash
python scripts/test_daily_pipeline.py --skip-collectors
```

**Utilité**:
- Tester modifications dans les templates
- Développer nouvelles fonctionnalités d'analyse
- Execution rapide (< 1 minute)

## Interpréter les Résultats

### Fichiers de Logs

Tous les tests créent 2 fichiers:

1. **Log détaillé**: `logs/test_daily_pipeline_YYYYMMDD_HHMMSS.log`
   - Tous les messages de log
   - Erreurs complètes avec traceback
   - Utile pour debugging

2. **Résultats JSON**: `logs/pipeline_test_results_YYYYMMDD_HHMMSS.json`
   - Structure:
   ```json
   {
     "test_started_at": "2025-01-15T14:30:22",
     "mock_mode": true,
     "service_status": {
       "supabase": true,
       "chromadb": true,
       "perplexity": true,
       "claude": true
     },
     "baseline": {
       "supabase": {"perplexity_analyses": 0, "claude_reports": 0},
       "chromadb": {"perplexity_analyses": {"count": 0}}
     },
     "pipeline_execution": {
       "success": true,
       "duration_seconds": 142.5,
       "error": null
     },
     "verification": {
       "supabase_changes": {
         "perplexity_analyses": 2,
         "claude_reports": 2
       },
       "chromadb_changes": {
         "perplexity_analyses": 2,
         "claude_reports": 2
       },
       "all_checks_passed": true
     },
     "test_ended_at": "2025-01-15T14:32:45",
     "overall_success": true
   }
   ```

### Vérification Manuelle dans Supabase

Après un test réussi:

```sql
-- Dernières analyses Perplexity
SELECT
    c.name as commodity,
    pa.query_type,
    pa.created_at,
    LEFT(pa.response_text, 100) as response_preview
FROM perplexity_analyses pa
JOIN commodities c ON c.id = pa.commodity_id
ORDER BY pa.created_at DESC
LIMIT 5;

-- Derniers rapports Claude
SELECT
    c.name as commodity,
    cr.report_type,
    cr.title,
    cr.created_at,
    (cr.metadata->>'mock_mode')::boolean as is_mock
FROM claude_reports cr
JOIN commodities c ON c.id = cr.commodity_id
ORDER BY cr.created_at DESC
LIMIT 5;
```

### Vérification dans ChromaDB

```python
# Dans un notebook Python ou script
from app.services import ChromaDBService
from app.config import settings

chromadb = ChromaDBService(
    host=settings.chroma_host,
    port=settings.chroma_port
)
chromadb.init_collections()

# Voir les stats
stats = chromadb.get_collection_stats()
print(stats)

# Rechercher une analyse
results = await chromadb.search_analyses(
    query="export prices Vietnam",
    commodity="cashew",
    n_results=3
)

for result in results:
    print(f"Distance: {result['distance']}")
    print(f"Content: {result['document'][:200]}")
    print(f"Metadata: {result['metadata']}")
```

## Erreurs Communes et Solutions

### 1. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution**:
```bash
pip install -r requirements.txt
```

### 2. Supabase Connection Failed

```
ERROR: Supabase connection failed: HTTPStatusError
```

**Solutions**:
- Vérifier `SUPABASE_URL` et `SUPABASE_KEY` dans `.env`
- Vérifier connexion internet
- Tester manuellement: `curl https://xqfozbocgyrelznccweh.supabase.co`

### 3. ChromaDB Server Unavailable

```
WARNING: ChromaDB server unavailable, using embedded storage
```

**Impact**: Faible - Le système continue avec stockage local

**Solutions**:
- Démarrer serveur: `chroma run --host localhost --port 8000`
- Ou ignorer (embedded mode fonctionne bien)

### 4. Perplexity Rate Limit

```
Exception: Perplexity API rate limit exceeded for this month
```

**Solutions**:
- Attendre le mois prochain
- Augmenter `PERPLEXITY_MAX_REQUESTS_PER_MONTH` dans `.env`
- Utiliser MOCK mode pour les tests

### 5. Pipeline Timeout

```
ERROR: Pipeline failed: asyncio.TimeoutError
```

**Causes**:
- Collectors bloqués (API externes lentes)
- ChromaDB en timeout

**Solutions**:
```bash
# Tester avec skip-collectors
python scripts/test_daily_pipeline.py --skip-collectors

# Désactiver ChromaDB temporairement
# Dans .env, commentez CHROMA_HOST
```

### 6. No Data Generated

```
⚠️  Perplexity analyses: 0 added (expected: 2)
```

**Debug**:
1. Vérifier logs pour erreurs
2. Tester Perplexity manuellement:
   ```python
   from app.services import PerplexityService
   from app.config import settings

   perplexity = PerplexityService(
       api_key=settings.perplexity_api_key,
       max_requests_per_month=1000
   )

   result = await perplexity.research_daily_prices("cashew")
   print(result)
   ```

## Best Practices

### Pendant le Développement

1. **Toujours utiliser MOCK mode**:
   ```bash
   python scripts/test_daily_pipeline.py
   ```

2. **Dry-run avant chaque test majeur**:
   ```bash
   python scripts/test_daily_pipeline.py --dry-run
   ```

3. **Utiliser skip-collectors pour tests rapides**:
   ```bash
   python scripts/test_daily_pipeline.py --skip-collectors
   ```

### Avant Déploiement Production

1. **Test MOCK complet**:
   ```bash
   python scripts/test_daily_pipeline.py
   ```

2. **UN test REAL pour validation**:
   ```bash
   python scripts/test_daily_pipeline.py --real
   ```

3. **Vérifier les résultats manuellement** dans Supabase

4. **Sauvegarder les logs** de test réussi

### En Production

1. **Ne JAMAIS** exécuter les tests en production
2. **Utiliser le scheduler** (APScheduler) pour exécutions automatiques
3. **Monitorer les logs** quotidiennement
4. **Backups réguliers** de Supabase et ChromaDB

## Monitoring Continu

### Script de Vérification Quotidienne

```python
# scripts/check_daily_pipeline_health.py
import asyncio
from datetime import date
from app.services import SupabaseService
from app.config import settings

async def check_health():
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    # Vérifier analyses aujourd'hui
    stats = await supabase.get_database_stats()

    # Requête pour compter analyses aujourd'hui
    # (nécessite ajout d'une méthode dans SupabaseService)

    print(f"Health check for {date.today()}:")
    print(f"✅ Total analyses: {stats['perplexity_analyses']}")
    print(f"✅ Total reports: {stats['claude_reports']}")

asyncio.run(check_health())
```

### Alertes

Configurer des alertes si:
- Aucune analyse générée pendant 24h
- Erreurs dans les logs
- ChromaDB collection vide après exécution

## Performance Benchmarks

### Temps d'Exécution Typiques

| Mode | Collectors | Perplexity | Claude | Total |
|------|-----------|-----------|--------|-------|
| MOCK (skip-collectors) | 0s | 0s (mock) | 2s | **2s** |
| MOCK (complet) | 45s | 0s (mock) | 2s | **47s** |
| REAL (skip-collectors) | 0s | 30s (API) | 2s | **32s** |
| REAL (complet) | 45s | 30s (API) | 2s | **77s** |

### Volumétrie par Exécution

| Métrique | Valeur Moyenne |
|----------|---------------|
| Prix collectés | 80-120 records |
| Productions collectées | 10-20 records |
| Documents GDrive | 0-5 (si nouveaux) |
| Analyses Perplexity | 2 (cashew + rubber) |
| Rapports Claude | 2 (cashew + rubber) |
| Embeddings ChromaDB | 100-150 vectors |

## Prochaines Étapes

Une fois les tests validés:

1. **Activer le scheduler** (voir `app/main.py`)
2. **Configurer REAL mode** pour Perplexity en production
3. **Migrer vers Claude API** réel si budget disponible
4. **Implémenter email notifications** pour rapports quotidiens
5. **Ajouter dashboard** Streamlit pour visualisation

## Support

En cas de problème:

1. Consulter les logs: `logs/test_daily_pipeline_*.log`
2. Vérifier cette documentation
3. Consulter `docs/DAILY_PIPELINE_GUIDE.md` pour détails techniques
4. Vérifier le RESUME_CODEX.md pour architecture générale
