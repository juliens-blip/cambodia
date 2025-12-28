# 🚀 KICKOFF EXÉCUTION - CAMBODIA AGRI ANALYTICS

## ÉTAT ACTUEL : 3 AGENTS EN COURS D'EXÉCUTION

### Agents Lancés (Background)

| Agent ID | Agent | Tâche | Tokens | Statut |
|----------|-------|-------|--------|--------|
| a51c9d9 | backend-architect | Architecture système + ChromaDB | 45.8k | ⚙️ Running |
| a496c95 | mcp-expert | Configuration 6 MCP servers | 57.4k | ⚙️ Running |
| a99b916 | fullstack-developer | Structure Python complète | 38.9k | ⚙️ Running |

**Total**: 142k tokens générés (en cours)

---

## PROJET CONFIRMÉ

### Objectifs
✅ **Multi-commodity analytics** : Cashew (très documenté) + Rubber (moins documenté)
✅ **Analyses SÉPARÉES** : Pas de comparaison cashew vs rubber
✅ **Timeline** : Au plus vite possible (optimisé pour parallélisation maximale)
✅ **Deployment** : Railway.app (test gratuit $5 crédit, puis production ~$70/mois)
✅ **Claude API** : MOCK service (pas de clé Anthropic, placeholder system)

---

## MCP SERVERS CONFIRMÉS (6 TOTAL)

### ✅ Configurés (5)
1. **context7** - Stockage contexte long-terme (Upstash)
2. **fetch** - HTTP requests (MEF, WITS APIs)
3. **supabase** - Database queries (projet: xqfozbocgyrelznccweh)
4. **browsermcp** - Scraping sites dynamiques (ODC)
5. **executeautomation-playwright-server** - Tests E2E + scraping avancé

### 🆕 À Ajouter (1)
6. **chroma** - ChromaDB vector database (semantic search layer)

---

## STACK TECHNIQUE FINAL

### Backend
- **Python** 3.11+
- **FastAPI** (REST API)
- **APScheduler** (cron jobs : daily 6am, weekly Monday 6am)
- **Supabase** (PostgreSQL managed)
- **ChromaDB** (vector database, semantic search)
- **Redis** (cache Perplexity responses)

### Frontend
- **Streamlit** (dashboard interactif)
- **Plotly** (charts)
- **Folium** (maps géospatiales KML)

### AI Services
- **Perplexity API** (recherche tendances, actualités)
  - Key: `YOUR_PERPLEXITY_API_KEY_HERE`
  - Rate limit: 1000 req/mois → optimisé avec ChromaDB cache
- **Claude MOCK** (synthèse, rapports)
  - Pas de vraie clé Anthropic
  - Template-based responses
  - Placeholder pour future intégration

### Data Sources
1. **MEF Cambodia** - https://data.mef.gov.kh/api/v1/public-datasets/
2. **WITS World Bank** - http://wits.worldbank.org/API/V1/datasource/trn/country/KHM
3. **Open Development Cambodia** - https://data.opendevelopmentcambodia.net/en/dataset
4. **Google Drive** - PDF/KML (cashew très documenté, rubber moins)
   - API Key: `AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk`

---

## CHROMADB : INTELLIGENCE LAYER 🧠

### 5 Collections Stratégiques

#### 1. `commodity_documents`
**Purpose** : PDFs Google Drive (cashew/rubber) avec OCR khmer
**Queries** : Semantic search multi-langue
**Volume** : ~100-500 documents

#### 2. `perplexity_analyses`
**Purpose** : Archive recherches Perplexity avec citations
**Queries** : Find similar market analyses
**Volume** : ~30/jour = 10k+/an

#### 3. `claude_reports`
**Purpose** : Rapports générés (daily/weekly)
**Queries** : Historical scenario matching
**Volume** : ~2/jour = 700+/an

#### 4. `commodity_prices`
**Purpose** : Prix avec contexte marché
**Queries** : Similar market conditions
**Volume** : ~50/jour = 18k+/an

#### 5. `production_data`
**Purpose** : Stats production + géospatial
**Queries** : High-yield regions, trends
**Volume** : ~500 records (yearly updates)

### Avantages ChromaDB
✅ **Recherche multi-langue** (EN + Khmer)
✅ **Contexte enrichi pour Claude** (smart filtering)
✅ **Dashboard intelligent** (semantic Q&A)
✅ **Cache sémantique Perplexity** (économie 70% API calls)

---

## ARCHITECTURE DATA FLOW

```
┌─────────────────────────────────────────────────────────┐
│                 EXTERNAL SOURCES                         │
│  MEF API │ WITS XML │ ODC HTML │ Google Drive PDF/KML   │
└────┬──────────┬─────────┬─────────────┬─────────────────┘
     │          │         │             │
     ▼ (fetch) ▼ (fetch) ▼ (browsermcp)▼ (fetch + OCR)
┌─────────────────────────────────────────────────────────┐
│              DATA COLLECTORS (Python)                    │
│   MEF    │   WITS   │   ODC   │  GDrive (pytesseract)   │
└────┬──────────┬─────────┬─────────────┬─────────────────┘
     │          │         │             │
     ▼          ▼         ▼             ▼
┌─────────────────────────────────────────────────────────┐
│              DUAL STORAGE LAYER                          │
│                                                           │
│  ┌──────────────────┐      ┌────────────────────────┐   │
│  │   SUPABASE       │      │     CHROMADB           │   │
│  │ (Structured SQL) │◄────►│ (Semantic Search)      │   │
│  │                  │      │                        │   │
│  │ • prices         │      │ • commodity_documents  │   │
│  │ • production     │      │ • perplexity_analyses  │   │
│  │ • commodities    │      │ • claude_reports       │   │
│  └──────────────────┘      │ • commodity_prices     │   │
│                             │ • production_data      │   │
│                             └────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
     │                              │
     ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                  AI ANALYSIS LAYER                       │
│                                                           │
│  ┌──────────────────┐      ┌────────────────────────┐   │
│  │  PERPLEXITY      │      │   CLAUDE MOCK          │   │
│  │  (Research)      │─────►│   (Synthesis)          │   │
│  │                  │      │                        │   │
│  │ • Daily trends   │      │ • Daily reports        │   │
│  │ • Geopolitics    │      │ • Weekly deep-dive     │   │
│  │ • Market news    │      │ • Crisis alerts        │   │
│  └──────────────────┘      └────────────────────────┘   │
│         │                           │                    │
│         └─────────┬─────────────────┘                    │
│                   ▼ (results stored in ChromaDB)         │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              STREAMLIT DASHBOARD                         │
│                                                           │
│  📊 Cashew Analytics  │  🌱 Rubber Analytics            │
│  📈 Price Trends      │  🗺️ Production Maps             │
│  📰 Latest Reports    │  🔍 Semantic Search (ChromaDB)  │
└─────────────────────────────────────────────────────────┘
```

---

## SUPABASE SCHEMA (7 TABLES)

### 1. `commodities`
```sql
CREATE TABLE commodities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL, -- 'cashew' | 'rubber'
  category TEXT NOT NULL,    -- 'nut' | 'latex'
  metadata JSONB
);
```

### 2. `prices`
```sql
CREATE TABLE prices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  date DATE NOT NULL,
  price_usd_per_unit DECIMAL(10,2) NOT NULL,
  volume_tons INTEGER,
  source TEXT NOT NULL, -- 'MEF' | 'WITS' | 'ODC' | 'manual'
  destination_country TEXT,
  quality_grade TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_prices_date ON prices(date DESC);
CREATE INDEX idx_prices_commodity ON prices(commodity_id);
```

### 3. `production`
```sql
CREATE TABLE production (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  year INTEGER NOT NULL,
  province TEXT NOT NULL,
  area_hectares DECIMAL(12,2),
  production_tons DECIMAL(12,2),
  yield_kg_per_ha DECIMAL(10,2),
  geolocation JSONB, -- {lat, lon} from KML
  source TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_production_year ON production(year DESC);
CREATE INDEX idx_production_province ON production(province);
```

### 4. `perplexity_analyses`
```sql
CREATE TABLE perplexity_analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  query_type TEXT NOT NULL, -- 'price' | 'geopolitics' | 'market'
  query_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  citations JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB
);
CREATE INDEX idx_analyses_created ON perplexity_analyses(created_at DESC);
```

### 5. `claude_reports`
```sql
CREATE TABLE claude_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  report_type TEXT NOT NULL, -- 'daily' | 'weekly' | 'crisis'
  title TEXT NOT NULL,
  content TEXT NOT NULL, -- Markdown
  insights JSONB,
  recommendations JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  published_at TIMESTAMPTZ
);
CREATE INDEX idx_reports_type_created ON claude_reports(report_type, created_at DESC);
```

### 6. `geopolitical_events`
```sql
CREATE TABLE geopolitical_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_date DATE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  impact_level TEXT, -- 'low' | 'medium' | 'high' | 'critical'
  countries_involved TEXT[],
  commodities_affected TEXT[],
  source_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_date ON geopolitical_events(event_date DESC);
```

### 7. `data_sources`
```sql
CREATE TABLE data_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL, -- 'MEF' | 'WITS' | 'ODC' | 'GDrive'
  url TEXT NOT NULL,
  last_fetch TIMESTAMPTZ,
  status TEXT, -- 'active' | 'error' | 'disabled'
  error_log JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## SCHEDULE JOBS (APScheduler)

### Daily (6:00 AM Cambodia Time = GMT+7)
```python
@scheduler.scheduled_job('cron', hour=6, minute=0, timezone='Asia/Phnom_Penh')
async def daily_pipeline():
    # 1. Collect data (all 4 collectors)
    await run_collectors()  # MEF, WITS, ODC, GDrive

    # 2. Perplexity analysis
    cashew_analysis = await perplexity.research_daily_prices("cashew")
    rubber_analysis = await perplexity.research_daily_prices("rubber")

    # 3. Store in ChromaDB + Supabase
    await chromadb.store_analyses([cashew_analysis, rubber_analysis])

    # 4. Claude MOCK reports
    cashew_report = await claude_mock.generate_daily_report("cashew")
    rubber_report = await claude_mock.generate_daily_report("rubber")

    # 5. Publish to dashboard
    await publish_reports([cashew_report, rubber_report])
```

### Weekly (Monday 6:00 AM)
```python
@scheduler.scheduled_job('cron', day_of_week='mon', hour=6, minute=0)
async def weekly_pipeline():
    # 1. Aggregate 7 days data
    week_data = await supabase.get_week_data()

    # 2. Deep Perplexity research
    cashew_deep = await perplexity.research_comprehensive("cashew")
    rubber_deep = await perplexity.research_comprehensive("rubber")

    # 3. Claude MOCK long-form reports
    cashew_weekly = await claude_mock.generate_weekly_report("cashew", week_data)
    rubber_weekly = await claude_mock.generate_weekly_report("rubber", week_data)

    # 4. Email to stakeholders
    await email_service.send_weekly_digest([cashew_weekly, rubber_weekly])
```

---

## DEPLOYMENT PLAN

### Phase 1 : Local Test (Jour 1-2)
```bash
# 1. Clone repo
git clone <repo_url>
cd cambodia-agri-analytics

# 2. Install dependencies
poetry install

# 3. Setup .env
cp .env.example .env
# Edit .env with real API keys (from MEMOIRE_CLAUDE.md)

# 4. Start services
docker-compose up -d  # PostgreSQL, Redis, ChromaDB

# 5. Init databases
python scripts/init_db.py        # Supabase migrations
python scripts/init_chromadb.py  # ChromaDB collections

# 6. Run API
uvicorn app.main:app --reload --port 8000

# 7. Run Dashboard (separate terminal)
streamlit run dashboard/app.py --server.port 8501

# 8. Test locally
open http://localhost:8501
```

### Phase 2 : Railway.app Test (Jour 3)
```bash
# 1. Create Railway account (free $5 credit)
railway login

# 2. Create project
railway init

# 3. Add services
railway add  # PostgreSQL
railway add  # Redis
# ChromaDB via Docker custom service

# 4. Configure env vars
railway variables set SUPABASE_URL=...
railway variables set PERPLEXITY_API_KEY=...
# (copy all from .env)

# 5. Deploy
git push  # Railway auto-deploys

# 6. Test production
open https://your-app.railway.app
```

### Phase 3 : Production (Semaine 2+)
- Monitor uptime (Uptime Robot)
- Setup alerts (Sentry)
- Optimize costs
- Scale if needed

---

## COÛTS ESTIMÉS

### Développement (Gratuit)
- Railway : $5 crédit gratuit
- Supabase : Free tier (500MB DB)
- ChromaDB : Self-hosted Docker (gratuit)

### Production (Mensuel)
| Service | Coût/Mois |
|---------|-----------|
| Railway.app | $15 (1GB RAM + Postgres + Redis) |
| Supabase Pro | $25 (si >500MB data) |
| Perplexity API | $20 (1000 req/mois optimisé ChromaDB) |
| Claude MOCK | $0 (pas de vraie API) |
| **TOTAL** | **$60/mois** (vs $70 initial estimate) |

---

## PROCHAINES ÉTAPES IMMÉDIATES

### ✅ EN COURS (Agents background)
1. **backend-architect** (a51c9d9) → Architecture complète
2. **mcp-expert** (a496c95) → Configuration 6 MCPs
3. **fullstack-developer** (a99b916) → Structure Python

### 🔜 APRÈS AGENTS (Automatique)
4. Valider MCP ChromaDB ajouté
5. Exécuter scripts init (Supabase + ChromaDB)
6. Créer modèles Pydantic
7. Implémenter BaseCollector
8. Lancer collecteurs en parallèle (MEF, WITS, ODC, GDrive)

### 📅 TIMELINE ACCÉLÉRÉE
- **Semaine 1** : Setup + Collectors + AI services
- **Semaine 2** : Dashboard + Tests + Deployment Railway
- **Semaine 3** : Production + Monitoring + Optimisations

**Timeline révisée** : 3 semaines (vs 4 semaines initial) grâce à parallélisation maximale

---

## DOCUMENTS CRÉÉS (8)

1. ✅ **MEMOIRE_CLAUDE.md** - Clés API sensibles, prompts, contexte
2. ✅ **ULTRA_THINK_ANALYSIS.md** - Analyse stratégique approfondie
3. ✅ **AGENT_DELEGATION_PLAN.md** - 27 tâches, 11 agents
4. ✅ **DEPLOYMENT_OPTIONS.md** - Railway vs alternatives
5. ✅ **MCP_INTEGRATION_STRATEGY.md** - 6 MCPs + ChromaDB (5 collections)
6. ✅ **KICKOFF_EXECUTION.md** - Ce document (état actuel)
7. 🔄 **ARCHITECTURE.md** - En cours (agent a51c9d9)
8. 🔄 **MCP_SETUP_GUIDE.md** - En cours (agent a496c95)

---

## MÉTRIQUES DE SUCCÈS

### Semaine 1
- [ ] 6 MCPs configurés et testés
- [ ] ChromaDB 5 collections créées
- [ ] 4 collecteurs fonctionnels
- [ ] Perplexity API intégré
- [ ] Claude MOCK service opérationnel

### Semaine 2
- [ ] Dashboard Streamlit complet (5 pages)
- [ ] Tests E2E passing
- [ ] Deploy Railway.app OK
- [ ] First automated daily report (6am)

### Semaine 3
- [ ] Production monitoring actif
- [ ] >100 documents ChromaDB indexés
- [ ] Cache Perplexity >50% hit rate
- [ ] User feedback positif

---

## AGENTS DISPONIBLES (CONSOLIDÉS)

### Agents Principaux (Utilisés)
1. **backend-architect** - Architecture, DB schema, API design
2. **fullstack-developer** - Implémentation Python/Streamlit
3. **mcp-expert** - Configuration MCPs
4. **test-engineer** - Tests unitaires/E2E
5. **prompt-engineer** - Optimisation prompts AI
6. **ui-ux-designer** - Design dashboard
7. **code-reviewer** - QA finale
8. **context-manager** - Documentation
9. **debugger** - Debugging final

### Agents Spécialisés (Disponibles si besoin)
10. **mcp-server-architect** - Custom MCP si besoin
11. **mcp-testing-engineer** - Tests MCP compliance
12. **task-decomposition-expert** - Décomposition ultra-fine (UTILISÉ ✅)
13. **architect-reviewer** - Review architecture patterns

### Agents Non Utilisés (Supprimés doublons)
- ❌ epct, moana-epct → Remplacés par agents spécifiques projet
- ❌ frontend-developer → Streamlit pas React
- ❌ typescript-pro → Projet 100% Python

---

## CONTACT & SUPPORT

**Questions** : Voir MEMOIRE_CLAUDE.md pour détails techniques
**Bugs** : Utiliser debugger agent
**Optimisations** : Utiliser backend-architect agent

---

**🚀 PROJET LANCÉ - AGENTS EN COURS D'EXÉCUTION**

*Dernière mise à jour : 2024-12-24 00:XX GMT+1*
