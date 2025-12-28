# Quick Start - Testing Daily Pipeline

Guide ultra-rapide pour tester le daily_pipeline en 10 minutes.

## Étape 1: Installation (2 min)

```bash
# Se placer dans le dossier du projet
cd D:\Projects\cambodia

# Installer les dépendances
pip install -r requirements.txt
```

**Si erreur**: Vérifier que Python 3.9+ est installé
```bash
python --version
```

## Étape 2: Vérification Configuration (1 min)

```bash
# Vérifier que .env contient les clés nécessaires
# Les valeurs suivantes DOIVENT être présentes:

SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJhbGci...
PERPLEXITY_API_KEY=pplx-...
CLAUDE_MOCK_MODE=true
```

**Status actuel**:
- ✅ Supabase: Configuré
- ✅ Perplexity: API key présente
- ✅ Claude: MOCK mode activé
- ⚠️ ChromaDB: Optionnel (fallback automatique si absent)

## Étape 3: Dry Run (1 min)

Teste les connexions **sans exécuter** le pipeline.

```bash
python scripts/test_daily_pipeline.py --dry-run
```

**Output attendu**:
```
================================================================================
CHECKING SERVICES
================================================================================
✅ Supabase connected
✅ ChromaDB connected (ou WARNING si serveur absent)
ℹ️  Perplexity in MOCK mode
✅ Claude service initialized

================================================================================
✅ ALL SERVICES READY
================================================================================
```

**Si erreurs**:
- ❌ Supabase failed → Vérifier connexion internet + clés .env
- ❌ ModuleNotFoundError → Installer requirements.txt

## Étape 4: Test MOCK Complet (3-5 min)

Exécute le pipeline en **mode MOCK** (aucun coût API).

```bash
python scripts/test_daily_pipeline.py
```

**Ce qui va se passer** (durée: ~3 minutes):
1. ⏳ Collecte données (MEF, WITS, ODC, GDrive) - 60s
2. ⏳ Stockage Supabase + ChromaDB - 15s
3. ⚡ Analyse Perplexity MOCK (instantané)
4. ⚡ Rapports Claude MOCK (instantané)
5. ⏳ Vérifications post-exécution - 10s

**Output attendu**:
```
================================================================================
RUNNING DAILY PIPELINE TEST (MOCK=True)
================================================================================
🌅 Starting DAILY pipeline...
🔄 Starting data collection from all sources...
✅ Collection complete: MEF=45, WITS=32, ODC=12, GDrive=0
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

Expected results:
  ✅ Perplexity analyses: 2 added (expected: 2)
  ✅ Claude reports: 2 added (expected: 2)
  ✅ ChromaDB embeddings: 2 analyses, 2 reports

================================================================================
✅ ALL TESTS PASSED
================================================================================

📁 Full results saved to: logs/pipeline_test_results_20250115_143022.json
```

## Étape 5: Vérification Supabase (2 min)

### Option A: Via Dashboard Supabase

1. Aller sur https://supabase.com/dashboard/project/xqfozbocgyrelznccweh
2. Table Editor → `perplexity_analyses`
3. Vérifier 2 nouvelles lignes (cashew + rubber)

### Option B: Via SQL

```sql
-- Dernières analyses
SELECT
    commodity_id,
    query_type,
    LEFT(response_text, 100) as preview,
    created_at
FROM perplexity_analyses
ORDER BY created_at DESC
LIMIT 5;

-- Derniers rapports
SELECT
    commodity_id,
    report_type,
    title,
    created_at
FROM claude_reports
ORDER BY created_at DESC
LIMIT 5;
```

**Résultat attendu**: 2 analyses + 2 rapports créés aujourd'hui

## Étape 6: Voir les Données Générées (1 min)

Les logs montrent un aperçu des données générées:

```
================================================================================
SAMPLE GENERATED DATA
================================================================================

📊 Latest Cashew Analysis:
  - Query Type: price
  - Created: 2025-01-15T14:31:02
  - Response: ## Current Market Analysis for Cashew in Cambodia

### Latest Export Prices
- Current price range: $2,800-3,200 USD per ton (FOB)
- Price trend: Stable with slight upward pressure (+2.3% week-over-week)
...

📄 Latest Cashew Report:
  - Title: Cashew Daily Report - 2025-01-15
  - Type: daily
  - Created: 2025-01-15T14:31:15
  - Content preview:
# Cashew Daily Report - 2025-01-15

## Executive Summary
- **Current Price**: $2850.00/ton (+2.30% vs yesterday)
- **Volume Traded**: 450 tons
- **Top Destination**: Vietnam
...
```

## Problèmes Courants

### Erreur: "ModuleNotFoundError: No module named 'chromadb'"

**Solution**:
```bash
pip install -r requirements.txt
```

### Erreur: "Supabase connection failed"

**Vérifications**:
1. Connexion internet OK?
2. Clés dans .env correctes?
3. Copier-coller depuis .env (pas de typo)

**Test manuel**:
```bash
curl https://xqfozbocgyrelznccweh.supabase.co
```

### Warning: "ChromaDB server unavailable, using embedded storage"

**Impact**: FAIBLE - Le système continue

**Explication**: ChromaDB serveur non démarré, fallback sur mode embedded (stockage local)

**Pour démarrer serveur** (optionnel):
```bash
chroma run --host localhost --port 8000
```

### Erreur: "No price data available"

**Cause**: Collectors n'ont pas retourné de données

**Solutions**:
1. Vérifier connexion internet
2. APIs externes peut-être indisponibles
3. Réessayer plus tard

### Tests passent mais 0 analyses créées

**Debug**:
```bash
# Regarder les logs détaillés
cat logs/test_daily_pipeline_YYYYMMDD_HHMMSS.log | grep -i error
```

## Étapes Suivantes

### Si tests MOCK réussis ✅

1. **Activer le scheduler** pour exécution quotidienne:
   - Voir `app/main.py`
   - Ou utiliser cron (Linux) / Task Scheduler (Windows)

2. **Configurer monitoring**:
   - Script de health check quotidien
   - Alertes en cas d'échec

3. **Migrer vers API réelles** (optionnel):
   - Claude API: `CLAUDE_MOCK_MODE=false` + `CLAUDE_API_KEY=...`
   - Coût: ~$0.50/mois

### Test avec API Perplexity Réelle (optionnel)

⚠️ **Coût: $0.002 par test**

```bash
python scripts/test_daily_pipeline.py --real
```

Seulement si:
- Tests MOCK tous OK
- Vérifier qualité analyses Perplexity
- Avant déploiement production

## Documentation Complète

Pour aller plus loin:

| Document | Description |
|----------|-------------|
| `docs/DAILY_PIPELINE_GUIDE.md` | Architecture détaillée du pipeline |
| `docs/TESTING_GUIDE.md` | Guide de test complet |
| `docs/PIPELINE_RECOMMENDATIONS.md` | Recommandations et roadmap |
| `scripts/README.md` | Documentation des scripts |

## Support

En cas de problème:

1. Consulter les logs: `logs/test_daily_pipeline_*.log`
2. Vérifier `docs/TESTING_GUIDE.md` section "Troubleshooting"
3. Vérifier `.env` configuration
4. Re-installer dépendances: `pip install -r requirements.txt`

## Résumé Visuel

```
┌─────────────────────────────────────────────────────────────┐
│  QUICK START - Daily Pipeline Testing                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. pip install -r requirements.txt        [2 min]         │
│  2. Vérifier .env                          [1 min]         │
│  3. python scripts/test_daily_pipeline.py --dry-run        │
│                                            [1 min]         │
│  4. python scripts/test_daily_pipeline.py  [3-5 min]       │
│  5. Vérifier Supabase                      [2 min]         │
│                                                             │
│  Total: ~10 minutes                                         │
│                                                             │
│  ✅ Success → Activer scheduler                             │
│  ❌ Error → Voir logs/ et troubleshooting                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Coût du test**: $0.00 (mode MOCK)

**Prêt à commencer?** Lancer `pip install -r requirements.txt` maintenant!
