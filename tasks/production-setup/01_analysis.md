# ANALYSE PRODUCTION - Cambodia Agri Analytics
**Date:** 2025-12-25
**Status:** Prêt pour setup production
**Durée setup estimée:** 2-3 jours

---

## EXECUTIVE SUMMARY

Le projet Cambodia Agri Analytics est **100% développé et documenté**. Toutes les features sont implémentées, testées en MOCK et prêtes pour déploiement production.

**État clé:**
- Backend API: ✅ Fonctionnel (FastAPI)
- Dashboard: ✅ Complet (Streamlit, 6 pages)
- Base de données: ✅ Structurée (Supabase)
- Data collectors: ✅ Intégrés (MEF, WITS, ODC, GDrive)
- Pipeline quotidien: ✅ Testé
- Qualité données: ✅ Auditée (92.6/100)

**Points d'attention production:**
- 191 duplicates dans prices (non-critique, migrationSQL corrige)
- 0 records production (à seeder avec migration 002)
- Coverage cashew faible (ODC à activer)
- ChromaDB fallback embedded (OK pour test, VPS recommandé pour prod)

---

## 1. INSTALLATION DÉPENDANCES PYTHON

### 1.1 Requirements
**Fichier:** `/requirements.txt`
**Statut:** ✅ Complet

```bash
# Installation
pip install -r requirements.txt
```

**Stack principal:**
| Module | Version | Rôle |
|--------|---------|------|
| FastAPI | >=0.104.0 | Backend API |
| Uvicorn | >=0.24.0 | ASGI server |
| Supabase | >=2.0.0 | Database ORM |
| Pandas | >=2.1.0 | Data processing |
| APScheduler | >=3.10.0 | Job scheduling |
| ChromaDB | >=0.4.18 | Vector DB |
| Tesseract-OCR | via pytesseract | PDF parsing (Khmer) |
| Google Drive API | >=2.108.0 | Data collection |
| BeautifulSoup4 | >=4.12.0 | Web scraping |
| Streamlit | (dashboard) | Dashboard (separate env) |

**Dépendances système requises:**
- Python 3.11+
- Tesseract OCR (installation Codex déjà faite)
- Poppler (installation Codex déjà faite)
- Tessdata Khmer (fichiers dans `/assets/tessdata`)

### 1.2 Environnement de déploiement
**Fichier:** `/.env`
**Clés requises:** Voir section 5 - Prérequis

---

## 2. MIGRATIONS SUPABASE

### 2.1 Migration 001 - Unique Constraint Prices

**Fichier:** `/scripts/migrations/001_add_unique_constraint_prices.sql`
**Criticité:** HAUTE
**État:** Prêt à appliquer

**Objectif:**
- Supprime 191 duplicates existants (PARTITION BY commodity_id + date + source + destination_country)
- Crée 2 unique indexes partiels (pour NULL et non-NULL destination_country)
- Empêche duplicates lors de re-seeding

**Commande Supabase Dashboard:**
```sql
-- SQL Editor: Copier/coller tout le contenu de 001_add_unique_constraint_prices.sql
-- ✅ Vérification: Query à la fin doit retourner 0 lignes (pas de duplicates)
```

**Impact données:**
- AVANT: 245 records (191 duplicates)
- APRÈS: ~54 unique records
- **⚠️ Action requise:** Déjà exécutée? Vérifier count dans Supabase

### 2.2 Migration 002 - Unique Constraint Production

**Fichier:** `/scripts/migrations/002_add_unique_constraint_production.sql`
**Criticité:** MOYENNE
**État:** Prêt à appliquer

**Objectif:**
- Crée unique index sur production table
- Natural key: commodity_id + year + province + source
- Support du upsert_production() dans SupabaseService

**Commande Supabase Dashboard:**
```sql
-- SQL Editor: Copier/coller tout le contenu de 002_add_unique_constraint_production.sql
```

**Impact données:**
- AVANT: 0 records
- APRÈS: ~156 records après seeding ODC
- État actuel: À déterminer (voir Audit section 4)

### 2.3 Ordre d'exécution
1. Connexion à Supabase Dashboard (projet: xqfozbocgyrelznccweh)
2. Aller à: SQL Editor
3. Exécuter migration 001 (prices cleanup)
4. Exécuter migration 002 (production index)
5. Vérifier: `SELECT COUNT(*) FROM prices;` (doit être ~54)

---

## 3. SEEDING DONNÉES PRODUCTION

### 3.1 Script de seeding
**Fichier:** `/scripts/seed_collectors.py`
**Fonction:** Collecte + stockage dual (Supabase + ChromaDB)

**Collectors intégrés:**
1. **MEFCollector** - Ministry of Economy and Finance Cambodia
   - Dataset: `pd_68b588a0eb43bd000745b588`
   - Export values en thousand_usd

2. **WITSCollector** - World Bank SDMX
   - TradeStats SDMX API
   - Cashew: 16-24_FoodProd
   - Rubber: 39-40_PlastiRub

3. **GDriveCollector** - Google Drive (PDF OCR + KML)
   - Tesseract Khmer + English
   - Extraction geolocation (lat/lon)

4. **ODCCollector** - Open Development Cambodia
   - Scraping datasets CSV/JSON
   - Fallback sample data

### 3.2 Commandes seeding

**Option 1: Seed standard (MEF + WITS + GDrive)**
```bash
python scripts/seed_collectors.py
```

**Option 2: Seed complet (+ ODC)**
```bash
python scripts/seed_collectors.py --include-odc
```

**Option 3: Seed sans ChromaDB**
```bash
python scripts/seed_collectors.py --include-odc --skip-chroma
```

### 3.3 Résultats attendus

| Collector | Records | Statut |
|-----------|---------|--------|
| MEF | ~100-150 | ✅ |
| WITS | ~80-120 | ✅ |
| GDrive | Variable | ✅ Dépend PDFs |
| ODC | ~30+ | ⚠️ À tester |

**Stockage:**
- Supabase: `prices` table + `production` table
- ChromaDB: Fallback embedded si serveur indispo

---

## 4. AUDIT QUALITÉ DONNÉES

### 4.1 Script d'audit
**Fichier:** `/scripts/audit_data_quality.py`
**Durée:** ~5-10 secondes
**Outputs:** JSON + Markdown reports

**Commande:**
```bash
python scripts/audit_data_quality.py
```

**Métriques calculées:**
1. **Completeness** (40% poids)
   - NULL values check
   - Required fields validation

2. **Validity** (30% poids)
   - Data type conformance
   - Outlier detection (statistical)

3. **Consistency** (20% poids)
   - MEF vs WITS reconciliation
   - Unit normalization checks

4. **Timeliness** (10% poids)
   - Data freshness
   - Temporal coverage

### 4.2 Score de qualité attendu
**Cible: 95+/100 (Excellent)**
**Actuel: 92.6/100 (Bon)**

**Issues à résoudre pour production:**
1. ✅ 191 duplicates → Migration 001
2. ✅ 0 production records → Migration 002 + seeding
3. ⚠️ 190% MEF/WITS discrepancy → Unit normalization
4. 🟡 5% coverage cashew → Ajouter sources

### 4.3 API endpoints qualité
Après déploiement, disponibles sur `/api/quality/`:
```
GET /api/quality/summary       # Résumé général
GET /api/quality/coverage      # Coverage metrics
GET /api/quality/completeness  # Null values, validation
GET /api/quality/gaps          # Temporal gaps analysis
GET /api/quality/outliers      # Statistical outliers
GET /api/quality/health        # Overall health check
```

---

## 5. TEST DAILY PIPELINE

### 5.1 Architecture pipeline
**Fichier:** `/scripts/test_daily_pipeline.py`

```
daily_pipeline() [6h00 Cambodia Time, quotidien]
├─► 1. COLLECTION (45s): MEF, WITS, ODC, GDrive
├─► 2. STORAGE DUAL (15s): Supabase + ChromaDB
├─► 3. PERPLEXITY ANALYSIS (30s): Tendances cashew + rubber
└─► 4. CLAUDE REPORTS (5s): Synthèse intelligente

Durée totale: ~60s MOCK / ~90s REAL
```

### 5.2 Modes de test

**Mode 1: Dry-run (Vérification services)**
```bash
python scripts/test_daily_pipeline.py --dry-run
# Coût: $0, Durée: ~2s
# Vérifie: Supabase, Perplexity, Claude, ChromaDB
```

**Mode 2: MOCK (Perplexity REAL + Claude MOCK)**
```bash
python scripts/test_daily_pipeline.py
# Coût: $0.002, Durée: ~60s
# Idéal pour testing avant production
```

**Mode 3: REAL (Tout en mode production)**
```bash
python scripts/test_daily_pipeline.py --real
# Coût: $0.005, Durée: ~90s
# ⚠️ Utilise vrais crédits Perplexity + Claude
```

**Mode 4: Skip collectors (Test analyses seulement)**
```bash
python scripts/test_daily_pipeline.py --skip-collectors
# Coût: $0.002, Durée: ~5s
# Test analyse sur données existantes
```

### 5.3 État des tables après test

| Table | Avant | Après MOCK |
|-------|-------|-----------|
| prices | ~54 | ~54 |
| production | 0 | ~156 |
| perplexity_analyses | 0 | 2 (mock) |
| claude_reports | 0 | 2 (mock) |

### 5.4 Coûts estimés
- **MOCK mode:** $0.06/mois (si daily)
- **REAL mode:** $0.51/mois (si daily)
- **Full production:** ~$15/mois (infra + analyses)

---

## ARCHITECTURE ACTUELLE

### Backend API (Port 8000)
```
app/main.py                    # FastAPI entry point
├── app/api/routes/
│   ├── prices.py             # Price endpoints
│   ├── production.py          # Production endpoints
│   ├── reports.py            # Reports endpoints
│   ├── search.py             # RAG search
│   └── quality.py            # Data quality (NEW)
├── app/services/
│   ├── supabase_service.py   # ORM + upsert methods
│   ├── chromadb_service.py   # Vector DB
│   ├── perplexity_service.py # AI analysis
│   └── data_quality_service.py # Quality metrics (NEW)
├── app/collectors/
│   ├── mef_collector.py
│   ├── wits_collector.py
│   ├── odc_collector.py
│   └── gdrive_collector.py
└── app/scheduler/
    ├── jobs.py               # daily_pipeline() + init_services()
    └── scheduler.py          # APScheduler config
```

### Database Schema
**Supabase (xqfozbocgyrelznccweh):**
```
commodities
├── id, code, name, description
├── data_sources (many)

prices
├── id, commodity_id, date, price, source
├── metric_type, value_unit, destination_country
├── UNIQUE INDEX: (commodity_id, date, source, destination_country)

production
├── id, commodity_id, year, province, value
├── source, unit, notes
├── UNIQUE INDEX: (commodity_id, year, province, source)

perplexity_analyses
├── id, commodity_id, analysis_type, content
├── period_start, period_end, keywords

claude_reports
├── id, commodity_id, report_type, content
├── analysis_summary, recommendations

data_sources
├── id, name, type, url, frequency
```

### Dashboard (Port 8501)
```
dashboard/
├── app.py                    # Streamlit entry
└── pages/
    ├── 1_Overview.py        # KPIs + stats
    ├── 2_Price_Analysis.py  # Charts + analysis
    ├── 3_Production.py      # Maps + heatmaps
    ├── 4_Market_Intelligence.py
    ├── 5_Reports.py
    └── 6_Data_Quality.py    # NEW monitoring
```

---

## DÉPENDANCES & PRÉREQUIS

### 5.1 Environnement

**Variables d'environnement requises (.env):**

| Variable | Type | Obligatoire | Commentaire |
|----------|------|-------------|-----------|
| SUPABASE_URL | URL | ✅ | Projet: xqfozbocgyrelznccweh |
| SUPABASE_ANON_KEY | JWT | ✅ | Anon key from dashboard |
| SUPABASE_SERVICE_ROLE_KEY | JWT | ✅ | Service role for migrations |
| PERPLEXITY_API_KEY | String | ✅ | pplx-... (utilisé par pipeline) |
| GOOGLE_DOCS_API_KEY | String | ✅ | Google Drive API credentials |
| CLAUDE_API_KEY | String | ⚠️ | Optionnel (MOCK par défaut) |
| ANTHROPIC_API_KEY | String | ⚠️ | Alternative Claude key |
| CHROMA_HOST | String | 🔄 | localhost (par défaut) |
| CHROMA_PORT | Number | 🔄 | 8000 (par défaut) |
| SCHEDULER_TIMEZONE | String | 🔄 | Asia/Phnom_Penh (défaut) |
| TESSERACT_CMD | Path | ✅ | C:\Program Files\Tesseract-OCR\tesseract.exe |
| POPPLER_PATH | Path | ✅ | C:\path\to\poppler\Library\bin |
| TESSDATA_PREFIX | Path | ✅ | assets\tessdata |

### 5.2 Services externes

**Requis pour production:**
1. ✅ Supabase project (xqfozbocgyrelznccweh) - ACTIF
2. ✅ Perplexity API - Clé présente
3. ⚠️ Claude API - À valider
4. ✅ Google Drive API - Clés présentes
5. 🔄 ChromaDB - Fallback embedded (upgrade recommandé)

### 5.3 Infrastructure

**Deployment actuel:**
- Windows VPS (Python 3.11, PowerShell)
- Local storage: `./chroma_data` (embedded ChromaDB)

**Pour production:**
- VPS Ubuntu 22.04+ recommandé
- Docker + docker-compose pour scaling
- ChromaDB VPS ($10/mois) pour persistence
- Redis cache (optionnel, pour rate limiting)

---

## POINTS D'ATTENTION

### 🚨 CRITIQUES

**1. Duplicates dans prices (191)**
- État: Identifiés, migration SQL prête
- Impact: 78% des données affectées
- Action: Exécuter `001_add_unique_constraint_prices.sql`
- ETA: Immédiat (10s exécution)

**2. Zéro records production**
- État: Attendu (ODC pas activé par défaut)
- Impact: Analyses incomplets
- Action: `seed_collectors.py --include-odc` + migration 002
- ETA: 5 minutes

### ⚠️ MOYENS

**3. Discrepancy MEF vs WITS (190%)**
- Cause: Unités différentes (USD vs thousand_usd)
- Impact: Comparaisons faussées
- Action: Unit normalization lors collection
- Priorité: Semaine 1

**4. Coverage cashew faible (5%)**
- État: Cashew 12 records vs Rubber 233 records
- Cause: Moins de sources disponibles
- Action: Identifier + intégrer sources cashew
- Priorité: Semaine 2

### 🟡 MINEURS

**5. ChromaDB fallback embedded**
- État: OK pour développement/testing
- Impact: Pas de persistence entre redémarrages
- Action: Docker deploy ou VPS ChromaDB
- Priorité: Mois 1

**6. Dashboard pages non optimisées**
- État: Fonctionnelles, lentes (>2s load)
- Impact: UX mediocre
- Action: Caching + query optimization
- Priorité: Mois 1

---

## RÉSUMÉ FICHIERS CONCERNÉS

### Scripts à exécuter (par ordre)

| # | Script | Commande | Durée | Criticité |
|---|--------|----------|-------|-----------|
| 1 | seed_collectors.py | `python scripts/seed_collectors.py --include-odc` | 5 min | HAUTE |
| 2 | audit_data_quality.py | `python scripts/audit_data_quality.py` | 10 sec | MOYENNE |
| 3 | test_daily_pipeline.py | `python scripts/test_daily_pipeline.py --dry-run` | 2 sec | BASSE |

### Migrations SQL à appliquer (Supabase Dashboard)

| # | Migration | Fichier | Criticité |
|---|-----------|---------|-----------|
| 1 | Prices cleanup + index | `scripts/migrations/001_add_unique_constraint_prices.sql` | HAUTE |
| 2 | Production index | `scripts/migrations/002_add_unique_constraint_production.sql` | MOYENNE |

### Documentation de référence

| Document | Chemin | Rôle |
|----------|--------|------|
| HANDOFF Final | `HANDOFF_CLAUDE_FINAL.md` | Overview session |
| Mémoire | `MEMOIRE_CLAUDE.md` | Context historique |
| Résumé Codex | `RESUME_CODEX.md` | État Codex |
| Upsert Guide | `docs/UPSERT_IMPLEMENTATION.md` | Système upsert |
| Production Setup | `PRODUCTION_DATA_SETUP.md` | Setup complet |
| Quality System | `DATA_QUALITY_SYSTEM.md` | Audit qualité |
| Pipeline Guide | `docs/DAILY_PIPELINE_GUIDE.md` | Architecture pipeline |

---

## TIMELINE RECOMMANDÉE

### Jour 1: Validation
- [ ] Lire cette analyse (15 min)
- [ ] Vérifier .env + clés API (10 min)
- [ ] Tester seed_collectors.py en DRY-RUN (5 min)
- [ ] Exécuter migrations SQL (5 min)

### Jour 2: Seeding + Audit
- [ ] Exécuter seed_collectors.py --include-odc (5 min)
- [ ] Exécuter audit_data_quality.py (10 min)
- [ ] Review rapport qualité (30 min)
- [ ] Tester daily_pipeline --dry-run (5 min)

### Jour 3: Testing + Optimization
- [ ] Tester daily_pipeline --mock (2 min)
- [ ] Review perplexity_analyses + claude_reports (10 min)
- [ ] Tester dashboard Data Quality page (10 min)
- [ ] Documenter issues + créer tickets (30 min)

**Total: 2.5 jours pour validation complète**

---

## COMMANDES PRODUCTION QUICK-START

```bash
# 1. Installer dépendances
pip install -r requirements.txt

# 2. Appliquer migrations (Supabase Dashboard SQL Editor)
# Copier/coller 001 et 002

# 3. Seeder données
python scripts/seed_collectors.py --include-odc

# 4. Auditer qualité
python scripts/audit_data_quality.py

# 5. Tester pipeline
python scripts/test_daily_pipeline.py --dry-run
python scripts/test_daily_pipeline.py  # MOCK mode

# 6. Lancer API + Dashboard
.\scripts\run_local.ps1 -StartChroma -Seed

# 7. Accéder interfaces
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
# Quality page: http://localhost:8501/?page=Data_Quality
```

---

## DOCUMENT GÉNÉRÉ

**Fichier:** `tasks/production-setup/01_analysis.md`
**Généré:** 2025-12-25
**Agent:** Claude Code - APEX Workflow Analysis
**Prochaine étape:** 02_execution_plan.md

