# Daily Pipeline Guide - Cambodia Agri Analytics

## Overview

Le **daily_pipeline** est le coeur du système Cambodia Agri Analytics. Il collecte, analyse et génère des rapports quotidiens sur les marchés du cashew et du rubber au Cambodge.

## Architecture du Pipeline

```
daily_pipeline()
│
├─► 1. DATA COLLECTION (run_collectors)
│   ├─► MEF Collector (Ministry of Economy & Finance)
│   ├─► WITS Collector (World Bank Trade Data)
│   ├─► ODC Collector (Open Development Cambodia)
│   └─► Google Drive Collector (PDFs, KML files)
│
├─► 2. DUAL STORAGE (store_data_dual)
│   ├─► Supabase (PostgreSQL)
│   │   ├─► prices table
│   │   └─► production table
│   └─► ChromaDB (Vector Database)
│       ├─► commodity_prices collection
│       └─► production_data collection
│
├─► 3. PERPLEXITY ANALYSIS (research_daily_prices)
│   ├─► Cashew market research
│   └─► Rubber market research
│   └─► Storage:
│       ├─► perplexity_analyses table (Supabase)
│       └─► perplexity_analyses collection (ChromaDB)
│
└─► 4. CLAUDE REPORTS (generate_daily_report)
    ├─► Cashew daily report
    └─► Rubber daily report
    └─► Storage:
        ├─► claude_reports table (Supabase)
        └─► claude_reports collection (ChromaDB)
```

## Flux de Données Détaillé

### Phase 1: Collection (run_collectors)

**Durée estimée**: 30-60 secondes

```python
# Les 4 collectors s'exécutent en parallèle
results = await asyncio.gather(
    mef.run(),      # Données gouvernementales cambodgiennes
    wits.run(),     # Données commerciales mondiales
    odc.run(),      # Données open development
    gdrive.run()    # Documents PDFs et KML
)
```

**Output**:
```python
{
    "mef": [price_records, production_records],
    "wits": [export_records],
    "odc": [geospatial_records],
    "gdrive": [documents]
}
```

### Phase 2: Stockage Dual (store_data_dual)

**Durée estimée**: 10-20 secondes

**Supabase Storage**:
- Utilise `upsert` pour éviter les doublons
- Natural keys: `(commodity_id, date, source, destination_country)`
- Tables mises à jour: `prices`, `production`

**ChromaDB Storage**:
- Génère des embeddings sémantiques
- Permet la recherche par similarité
- Collections: `commodity_prices`, `production_data`

**Important**: ChromaDB est optionnel. Si le serveur ChromaDB n'est pas disponible, le pipeline continue avec Supabase uniquement.

### Phase 3: Analyse Perplexity (research_daily_prices)

**Durée estimée**: 15-30 secondes (REAL mode) / instant (MOCK mode)

**Prompt utilisé** (exemple cashew):
```
Analyze current market conditions for cashew in Cambodia:
1. Latest export prices (USD per ton)
2. Key destination countries (Vietnam, China, Europe)
3. Supply/demand dynamics
4. Geopolitical factors affecting trade
5. Quality grades impact on pricing

Focus on factual data from last 7 days. Include citations.
```

**API Call**:
- Model: `llama-3.1-sonar-large-128k-online`
- Temperature: 0.2 (factual responses)
- Return citations: True

**Output** (stocké dans Supabase et ChromaDB):
```python
{
    "commodity": "cashew",
    "query_type": "price",
    "query_text": "...",
    "response_text": "Comprehensive analysis...",
    "citations": ["https://source1.com", "https://source2.com"],
    "created_at": "2025-01-15T06:15:30Z",
    "metadata": {
        "model": "llama-3.1-sonar-large-128k-online",
        "tokens_used": 1234,
        "request_id": "req_xyz"
    }
}
```

### Phase 4: Rapports Claude (generate_daily_report)

**Durée estimée**: instant (MOCK mode) / 5-10 secondes (REAL mode)

**Mode actuel**: MOCK (templates)

**Input**:
1. Latest price data from Supabase
2. Perplexity analysis from Phase 3

**Template sections**:
- Executive Summary (prix, volume, destination)
- Market Conditions (résumé Perplexity)
- Key Insights (3-5 insights générés)
- Recommendations (3-4 recommandations)

**Output** (stocké dans Supabase et ChromaDB):
```python
{
    "commodity": "cashew",
    "report_type": "daily",
    "title": "Cashew Daily Report - 2025-01-15",
    "content": "# Cashew Daily Report...",
    "insights": ["Insight 1", "Insight 2"],
    "recommendations": ["Rec 1", "Rec 2"],
    "created_at": "2025-01-15T06:16:00Z",
    "metadata": {
        "mock_mode": true,
        "price_usd": 2850.00,
        "price_change_pct": 2.3,
        "volume_tons": 450,
        "destination": "Vietnam"
    }
}
```

## Modes de Fonctionnement

### MOCK Mode (défaut)

**Avantages**:
- Aucun coût API
- Exécution instantanée
- Parfait pour tests et développement

**Configuration**:
```bash
# .env
CLAUDE_MOCK_MODE=true
PERPLEXITY_API_KEY=<key>  # Requis même en MOCK
```

**Comportement**:
- Perplexity: Appels API réels (Perplexity ne coûte que ~0.001$ par requête)
- Claude: Utilise templates (pas d'appel API)

### REAL Mode (production)

**Avantages**:
- Analyses Claude sophistiquées
- Insights personnalisés
- Qualité supérieure

**Configuration**:
```bash
# .env
CLAUDE_MOCK_MODE=false
CLAUDE_API_KEY=sk-ant-api...
PERPLEXITY_API_KEY=pplx-...
```

**Coûts estimés par exécution**:
- Perplexity: 2 requests × $0.001 = $0.002
- Claude Sonnet 3.5: ~5k tokens × $0.003/1k = $0.015
- **Total**: ~$0.017 par jour → $0.51/mois

## Configuration et Variables d'Environnement

### Variables Requises

```bash
# Supabase (REQUIS)
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJhbGci...

# ChromaDB (OPTIONNEL)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_PATH=chroma_data

# Perplexity (REQUIS)
PERPLEXITY_API_KEY=pplx-...
PERPLEXITY_MAX_REQUESTS_PER_MONTH=1000

# Claude (OPTIONNEL en MOCK mode)
CLAUDE_API_KEY=sk-ant-api...
CLAUDE_MOCK_MODE=true
```

### Scheduler Settings

```bash
# Timezone cambodgienne
TIMEZONE=Asia/Phnom_Penh

# Exécution quotidienne à 6h00 du matin
DAILY_JOB_HOUR=6
DAILY_JOB_MINUTE=0
```

## Gestion des Erreurs

### Erreurs Communes

1. **Perplexity Rate Limit Exceeded**
   ```
   Exception: Perplexity API rate limit exceeded for this month
   ```
   **Solution**: Augmenter `PERPLEXITY_MAX_REQUESTS_PER_MONTH` ou attendre le mois prochain

2. **ChromaDB Connection Failed**
   ```
   WARNING: ChromaDB server unavailable, using embedded storage
   ```
   **Impact**: Faible - Le pipeline continue avec stockage embarqué
   **Solution**: Démarrer serveur ChromaDB: `chroma run --host localhost --port 8000`

3. **Supabase Connection Failed**
   ```
   ERROR: Supabase connection failed
   ```
   **Impact**: CRITIQUE - Le pipeline s'arrête
   **Solution**: Vérifier `SUPABASE_URL` et `SUPABASE_KEY`, vérifier la connexion internet

4. **No Price Data Available**
   ```
   WARNING: No prices available for commodity
   ```
   **Impact**: Reports générés avec prix $0.00
   **Solution**: Exécuter collectors manuellement ou vérifier data sources

### Stratégie de Retry

Le pipeline **NE FAIT PAS** de retry automatique pour éviter:
- Double facturation API
- Données dupliquées dans la base

En cas d'erreur:
1. Le pipeline s'arrête
2. L'erreur est loggée
3. Une intervention manuelle est requise

## Monitoring et Logs

### Logs Importants

```python
logger.info("🌅 Starting DAILY pipeline...")        # Début
logger.info("✅ Collection complete: MEF=X, WITS=Y") # Collection OK
logger.info("✅ Data stored successfully")           # Stockage OK
logger.info("✅ DAILY pipeline complete!")           # Fin succès
logger.error("❌ DAILY pipeline failed: {e}")        # Échec
```

### Vérification Post-Exécution

```sql
-- Vérifier les analyses générées aujourd'hui
SELECT commodity_id, query_type, created_at
FROM perplexity_analyses
WHERE created_at::date = CURRENT_DATE;

-- Vérifier les rapports générés aujourd'hui
SELECT commodity_id, report_type, title, created_at
FROM claude_reports
WHERE created_at::date = CURRENT_DATE;

-- Compter les prix collectés aujourd'hui
SELECT source, COUNT(*)
FROM prices
WHERE date = CURRENT_DATE
GROUP BY source;
```

### Métriques ChromaDB

```python
# Dans le code Python
chromadb_service.get_collection_stats()

# Output attendu
{
    "perplexity_analyses": {"count": 145, "name": "perplexity_analyses"},
    "claude_reports": {"count": 145, "name": "claude_reports"},
    "commodity_prices": {"count": 2830, "name": "commodity_prices"},
    "production_data": {"count": 156, "name": "production_data"}
}
```

## Tables et Collections Affectées

### Supabase Tables

| Table | Before Pipeline | After Pipeline | Delta |
|-------|----------------|----------------|-------|
| `commodities` | 2 | 2 | 0 (déjà créés) |
| `prices` | X | X + N | +N nouveaux prix |
| `production` | Y | Y + M | +M nouvelles productions |
| `perplexity_analyses` | Z | Z + 2 | +2 (cashew + rubber) |
| `claude_reports` | W | W + 2 | +2 (cashew + rubber) |

### ChromaDB Collections

| Collection | Before | After | Delta |
|------------|--------|-------|-------|
| `commodity_prices` | X | X + N | +N embeddings |
| `production_data` | Y | Y + M | +M embeddings |
| `perplexity_analyses` | Z | Z + 2 | +2 embeddings |
| `claude_reports` | W | W + 2 | +2 embeddings |
| `commodity_documents` | K | K + L | +L documents (si GDrive a des nouveaux PDFs) |

## Optimisations Possibles

### 1. Caching Perplexity

**Problème**: Même question posée chaque jour coûte des crédits

**Solution**:
```python
# Vérifier si une analyse similaire existe déjà (< 24h)
recent_analysis = await supabase.get_recent_analyses(
    commodity_id,
    query_type="price",
    limit=1
)

if recent_analysis and is_less_than_24h_old(recent_analysis[0]):
    logger.info("Using cached Perplexity analysis")
    return recent_analysis[0]
```

### 2. Batch ChromaDB Inserts

**Problème**: Insertions individuelles sont lentes

**Solution**:
```python
# Au lieu de:
for record in records:
    await chromadb.store_price_with_context(...)

# Utiliser:
await chromadb.batch_store_prices([record1, record2, ...])
```

### 3. Parallel Analysis Generation

**Problème**: Analyses séquentielles (cashew puis rubber)

**Solution**:
```python
# Exécuter en parallèle
cashew_analysis, rubber_analysis = await asyncio.gather(
    perplexity.research_daily_prices("cashew"),
    perplexity.research_daily_prices("rubber")
)
```

### 4. Incremental Collection

**Problème**: Collecte toutes les données à chaque fois

**Solution**:
```python
# Collecter uniquement les nouvelles données
last_collection = await supabase.get_last_collection_timestamp(source)
new_data = await collector.run(since=last_collection)
```

## Troubleshooting

### Pipeline Bloqué

**Symptômes**: Pipeline ne se termine jamais

**Debug**:
1. Vérifier les logs pour la dernière étape
2. Vérifier la connexion ChromaDB (timeout possible)
3. Tester chaque collector individuellement

**Solution temporaire**:
```python
# Désactiver ChromaDB temporairement
chromadb = None  # Le pipeline continue sans embeddings
```

### Données Manquantes

**Symptômes**: Analyses créées mais vides

**Causes possibles**:
1. Collectors n'ont pas retourné de données
2. Problème de parsing des données collectées
3. Erreur silencieuse dans `store_data_dual`

**Vérification**:
```python
# Ajouter logs détaillés
logger.info(f"Collected data: MEF={len(mef_data)}, WITS={len(wits_data)}")
```

### Doublons dans la Base

**Symptômes**: Même analyse/rapport créé plusieurs fois

**Causes**:
1. Pipeline exécuté manuellement plusieurs fois
2. Scheduler déclenché deux fois
3. `upsert` ne fonctionne pas (manque unique constraint)

**Solution**:
```sql
-- Vérifier les doublons
SELECT commodity_id, created_at::date, COUNT(*)
FROM perplexity_analyses
GROUP BY commodity_id, created_at::date
HAVING COUNT(*) > 1;

-- Supprimer les doublons (garder le plus récent)
DELETE FROM perplexity_analyses
WHERE id NOT IN (
    SELECT MAX(id)
    FROM perplexity_analyses
    GROUP BY commodity_id, created_at::date
);
```

## Prochaines Étapes

### Migration vers Claude API Réel

1. Obtenir Claude API key
2. Configurer `.env`: `CLAUDE_MOCK_MODE=false`
3. Tester en mode dry-run
4. Monitorer les coûts

### Amélioration de la Qualité

1. **Enrichir les prompts Perplexity**:
   - Ajouter contexte historique
   - Spécifier sources prioritaires

2. **Personnaliser les templates Claude**:
   - Insights basés sur ML predictions
   - Recommandations basées sur règles métier

3. **Ajouter alertes**:
   - Prix anormalement élevés/bas
   - Changements géopolitiques majeurs

### Automatisation Avancée

1. **Email notifications**:
   - Envoyer rapports aux stakeholders
   - Alertes sur événements critiques

2. **Webhook intégrations**:
   - Notifier systèmes externes
   - Trigger actions automatiques

3. **Dashboard temps réel**:
   - Visualiser exécution pipeline
   - Monitorer santé des services
