# PLAN DE DÉLÉGATION MAXIMALE - CAMBODIA AGRI ANALYTICS

## PROJET ÉTENDU : CASHEW + RUBBER

### Commodités
1. **Cashew (Noix de cajou)** - Très documenté (Google Drive)
2. **Rubber (Caoutchouc)** - Moins documenté (Google Drive)

### Architecture Multi-Commodity
- Base extensible pour ajouter d'autres commodités (pepper, rice, etc.)
- Modèle `Commodity` abstrait avec implémentations `CashewCommodity`, `RubberCommodity`

---

## AGENTS DISPONIBLES (14 TOTAL)

### ✅ AGENTS À UTILISER

| # | Agent | Spécialité | Utilisation |
|---|-------|-----------|-------------|
| 1 | **backend-architect** | Architecture backend, APIs, DB schema | Critique - Design système |
| 2 | **code-reviewer** | Review qualité, sécurité | Fin de cycle - QA |
| 3 | **context-manager** | Gestion contexte long-term | Coordination projet |
| 4 | **debugger** | Debugging, root cause analysis | Si bugs rencontrés |
| 5 | **fullstack-developer** | Dev full-stack (Python + Streamlit) | Implémentation code |
| 6 | **mcp-expert** | Configuration MCP servers | Setup Supabase/Fetch MCPs |
| 7 | **mcp-server-architect** | Build custom MCP servers | Si besoin MCP custom |
| 8 | **mcp-testing-engineer** | Tests MCP compliance | Tests MCP intégrations |
| 9 | **prompt-engineer** | Optimisation prompts AI | Prompts Perplexity/Claude |
| 10 | **test-engineer** | Tests end-to-end, CI/CD | Tests automatisés |
| 11 | **ui-ux-designer** | Design dashboard, UX | Design Streamlit UI |

### ❌ AGENTS NON UTILISÉS (Raisons)

| # | Agent | Raison exclusion |
|---|-------|------------------|
| 12 | **epct** | ❌ DOUBLON - Workflow générique, on va créer agent EPCT custom |
| 13 | **frontend-developer** | ❌ PAS NÉCESSAIRE - Streamlit pas React (fullstack-developer suffit) |
| 14 | **moana-epct** | ❌ DOUBLON - Spécifique Moana, on adapte pour Cashew/Rubber |

---

## REFORMULATION AGENTS POUR LE PROJET

### Agent Custom : **cambodia-epct**
**Nouveau fichier** : `.claude/agents/cambodia-epct.md`

```markdown
---
description: EPCT workflow pour Cambodia Agri Analytics (Cashew/Rubber)
allowed-tools: [WebSearch, WebFetch, Task, Grep, Glob, Read, Write, Edit, TodoWrite, Bash]
argument-hint: <feature description>
model: sonnet
---

# EPCT Workflow: Cambodia Agri Analytics

## Project Context
- **Stack**: Python 3.11+, FastAPI, Streamlit, Supabase, Perplexity, Claude
- **Commodities**: Cashew (primary), Rubber (secondary)
- **Data Sources**: ODC, MEF Cambodia, WITS, Google Drive (PDF/KML khmer)
- **Deployment**: Test (local/Vercel analogue), Production (TBD)

## Phase 1: EXPLORE
- Research commodity-specific data patterns
- Analyze Google Drive docs (cashew very detailed, rubber less)
- Identify data collection strategies per commodity
- Explore Supabase schema for multi-commodity support

## Phase 2: PLAN
- Design commodity-agnostic architecture
- Plan collectors (ODC, MEF, WITS, Google Drive parser)
- Define Supabase tables (commodities, prices, production, analyses, reports)
- Create TodoWrite plan with agent assignments

## Phase 3: CODE
- Follow Python best practices (type hints, async/await)
- Implement collectors with retry logic
- Build Perplexity/Claude services
- Create Streamlit dashboard with commodity switcher

## Phase 4: TEST
- Unit tests collectors (pytest)
- Integration tests Supabase pipelines
- E2E tests dashboard (Playwright)
- Validate multi-commodity support
```

---

## DÉCOMPOSITION MAXIMALE DES TÂCHES

### PHASE 0 : SETUP & ARCHITECTURE (Semaine 1 - Jours 1-2)

#### Tâche 0.1 : Architecture Système
**Agent** : `backend-architect`
**Durée** : 4h
**Livrables** :
- [ ] Diagramme architecture multi-commodity (ASCII ou Mermaid)
- [ ] Définition API endpoints FastAPI
- [ ] Schéma Supabase complet (7+ tables)
- [ ] Stratégie caching (Redis ou in-memory)
- [ ] Plan scalabilité (1 commodity → N commodities)

**Prompt** :
```
Design architecture for Cambodia Agri Analytics platform supporting:
- 2 commodities initially (cashew, rubber)
- Extensible to N commodities
- Data sources: ODC, MEF, WITS, Google Drive (PDF/KML khmer)
- AI analysis: Perplexity (research) + Claude (synthesis)
- Storage: Supabase PostgreSQL
- Dashboard: Streamlit
- Scheduling: APScheduler (daily 6am, weekly Monday 6am)

Provide:
1. System architecture diagram
2. FastAPI endpoint structure
3. Supabase schema (tables, indexes, RLS)
4. Caching strategy
5. Scalability considerations
```

---

#### Tâche 0.2 : Configuration MCP Servers
**Agent** : `mcp-expert`
**Durée** : 2h
**Livrables** :
- [ ] Supabase MCP configuré (projet `xqfozbocgyrelznccweh`)
- [ ] Fetch MCP configuré
- [ ] Context7 MCP testé
- [ ] Documentation `.mcp.json` complète

**Prompt** :
```
Configure MCP servers for Cambodia Agri Analytics:

1. Supabase MCP:
   - Project ref: xqfozbocgyrelznccweh
   - URL: https://xqfozbocgyrelznccweh.supabase.co
   - Setup with service role key (from MEMOIRE_CLAUDE.md)

2. Fetch MCP:
   - For scraping ODC, MEF, WITS APIs
   - Test with sample requests

3. Context7 MCP:
   - For long-term context storage
   - Test save/retrieve operations

Deliverables:
- Updated .mcp.json with all configs
- Test script validating each MCP
- Documentation of MCP usage patterns
```

---

#### Tâche 0.3 : Structure Projet Python
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] Structure dossiers complète
- [ ] `pyproject.toml` (Poetry) avec dépendances
- [ ] `.env.example` avec variables
- [ ] `.gitignore` Python standard
- [ ] `README.md` initial
- [ ] `docker-compose.yml` (PostgreSQL local + Redis)

**Prompt** :
```
Create complete Python project structure for Cambodia Agri Analytics:

Structure:
cambodia-agri-analytics/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry
│   ├── config.py               # Settings from env
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseCollector abstract
│   │   ├── odc_collector.py
│   │   ├── mef_collector.py
│   │   ├── wits_collector.py
│   │   └── gdrive_collector.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── perplexity.py
│   │   ├── claude.py
│   │   └── supabase_client.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── commodity.py
│   │   ├── price.py
│   │   └── analysis.py
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   └── scheduler.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
├── dashboard/
│   ├── __init__.py
│   ├── app.py                  # Streamlit entry
│   ├── pages/
│   │   ├── 1_cashew.py
│   │   ├── 2_rubber.py
│   │   └── 3_reports.py
│   └── components/
│       ├── charts.py
│       └── maps.py
├── tests/
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_services.py
│   └── test_integration.py
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md

Dependencies (pyproject.toml):
- fastapi, uvicorn
- streamlit, plotly
- supabase, anthropic, httpx
- apscheduler, pydantic
- python-dotenv, pytest
- geopandas (KML parsing)
- pytesseract (OCR khmer)

Docker-compose:
- PostgreSQL 15 (dev DB)
- Redis (caching)
- App service (FastAPI)
- Dashboard service (Streamlit)
```

---

### PHASE 1 : DATABASE & SCHEMA (Semaine 1 - Jours 3-4)

#### Tâche 1.1 : Schéma Supabase Multi-Commodity
**Agent** : `backend-architect`
**Durée** : 4h
**Livrables** :
- [ ] SQL migrations Supabase
- [ ] Indexes optimisés (timeseries, commodity_type)
- [ ] RLS policies (si multi-tenancy futur)
- [ ] Triggers (auto-update, validation)
- [ ] Documentation schéma

**Prompt** :
```
Create Supabase schema for multi-commodity analytics platform.

Tables:
1. commodities
   - id, name (cashew/rubber), category, metadata (JSONB)

2. prices
   - id, commodity_id, date, price_usd_per_unit, volume, source
   - destination_country, quality_grade, metadata

3. production
   - id, commodity_id, year, province, area_hectares
   - production_tons, yield_per_hectare, geolocation (JSONB from KML)

4. perplexity_analyses
   - id, commodity_id, query_type, query_text, response_text
   - citations (JSONB), created_at, metadata

5. claude_reports
   - id, commodity_id, report_type (daily/weekly)
   - title, content (markdown), insights (JSONB)
   - recommendations (JSONB), created_at, published_at

6. geopolitical_events
   - id, event_date, title, description, impact_level
   - countries_involved (TEXT[]), commodities_affected (TEXT[])
   - source_url, created_at

7. data_sources
   - id, name (ODC/MEF/WITS/GDrive), url, last_fetch
   - status, error_log

Indexes:
- BRIN on prices.date (timeseries)
- B-tree on prices.commodity_id, production.commodity_id
- GIN on metadata JSONB fields
- Full-text search on claude_reports.content

Provide complete SQL with CREATE TABLE, CREATE INDEX, CREATE TRIGGER.
```

---

#### Tâche 1.2 : Modèles Pydantic
**Agent** : `fullstack-developer`
**Durée** : 2h
**Livrables** :
- [ ] `models/commodity.py` (Commodity base class)
- [ ] `models/price.py` (Price, PriceCreate, PriceUpdate)
- [ ] `models/analysis.py` (PerplexityAnalysis, ClaudeReport)
- [ ] Validators (price ranges, date validation)

**Prompt** :
```
Create Pydantic models matching Supabase schema:

app/models/commodity.py:
- Commodity (base class)
- CashewCommodity (extends Commodity)
- RubberCommodity (extends Commodity)
- Enum CommodityType(cashew, rubber)

app/models/price.py:
- Price (ORM model)
- PriceCreate (for inserts)
- PriceUpdate (for updates)
- Validators:
  - price > 0
  - date <= today
  - quality_grade in allowed list

app/models/analysis.py:
- PerplexityAnalysis
- ClaudeReport
- GeopoliticalEvent

Use proper type hints (UUID, datetime, Decimal).
```

---

### PHASE 2 : DATA COLLECTION (Semaine 1-2)

#### Tâche 2.1 : Base Collector Class
**Agent** : `fullstack-developer`
**Durée** : 2h
**Livrables** :
- [ ] `collectors/base.py` (BaseCollector ABC)
- [ ] Retry logic (exponential backoff)
- [ ] Error handling standardisé
- [ ] Logging structuré

**Prompt** :
```
Create BaseCollector abstract class:

class BaseCollector(ABC):
    def __init__(self, commodity: CommodityType):
        self.commodity = commodity
        self.session = httpx.AsyncClient()
        self.logger = structlog.get_logger()

    @abstractmethod
    async def fetch(self) -> List[Dict]:
        """Fetch raw data from source"""
        pass

    @abstractmethod
    def transform(self, raw_data: Any) -> List[Price]:
        """Transform raw data to Price models"""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def collect(self) -> List[Price]:
        """Main collection pipeline"""
        raw = await self.fetch()
        return self.transform(raw)

Include:
- Retry decorator (tenacity)
- Logging (structlog)
- Error tracking (Sentry integration)
- Rate limiting placeholder
```

---

#### Tâche 2.2 : MEF Cambodia Collector
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] `collectors/mef_collector.py`
- [ ] Cashew data extraction
- [ ] Rubber data extraction
- [ ] Tests unitaires (pytest + httpx.AsyncClient mock)

**Prompt** :
```
Implement MEFCollector for Cambodia MEF API:

URL: https://data.mef.gov.kh/api/v1/public-datasets/pd_68b588a0eb43bd000745b588/json

Features:
1. Fetch JSON data (pagination support)
2. Extract price/volume for cashew and rubber
3. Transform to Price models
4. Handle missing data gracefully
5. Log API response times

Test with:
- Mock API responses
- Error scenarios (timeout, 500, invalid JSON)
- Empty datasets
```

---

#### Tâche 2.3 : WITS World Bank Collector
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] `collectors/wits_collector.py`
- [ ] XML parsing (lxml)
- [ ] Cambodia export data extraction
- [ ] Tests

**Prompt** :
```
Implement WITSCollector for World Bank WITS API:

URL: http://wits.worldbank.org/API/V1/datasource/trn/country/KHM

Features:
1. Parse XML responses (lxml)
2. Extract export data (cashew HS code 0801, rubber 4001)
3. Map to Price/Production models
4. Handle XML parsing errors
5. Cache responses (1 hour TTL)

Include:
- XML schema validation
- HS code mapping (cashew/rubber)
- Unit conversion (kg → tons)
```

---

#### Tâche 2.4 : Open Development Cambodia Collector
**Agent** : `fullstack-developer`
**Durée** : 4h
**Livrables** :
- [ ] `collectors/odc_collector.py`
- [ ] HTML scraping (BeautifulSoup)
- [ ] CSV download + parsing
- [ ] Tests

**Prompt** :
```
Implement ODCCollector for Open Development Cambodia:

URL: https://data.opendevelopmentcambodia.net/en/dataset

Strategy:
1. Search for "cashew" and "rubber" datasets
2. Download CSV files
3. Parse with pandas
4. Extract production data (area, yield, province)
5. Handle missing columns

Challenges:
- Dynamic page loading (may need Playwright)
- CSV format variations
- Khmer characters in column names

Include:
- Fallback to manual CSV upload
- Data validation (outlier detection)
```

---

#### Tâche 2.5 : Google Drive PDF/KML Collector
**Agent** : `fullstack-developer`
**Durée** : 6h (COMPLEXE)
**Livrables** :
- [ ] `collectors/gdrive_collector.py`
- [ ] PDF OCR khmer (Tesseract)
- [ ] KML parsing (geopandas)
- [ ] Tests avec fichiers sample

**Prompt** :
```
Implement GDriveCollector for Google Drive documents:

API: Google Docs API (key: AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk)
Folders:
- "cashew cambodia" (many PDFs, some KML)
- "rubber cambodia" (fewer docs)

Features:
1. List files in folder (Google Drive API)
2. Download PDFs
3. OCR khmer text (pytesseract + khmer language pack)
4. Extract structured data (regex patterns)
5. Parse KML geospatial data (geopandas)
6. Cache downloaded files (avoid re-download)

Challenges:
- Khmer OCR accuracy (90%+ target)
- PDF layout variations
- KML coordinate extraction

Include:
- Checksum-based caching
- Manual review UI for OCR results
- Geojson output from KML
```

---

### PHASE 3 : AI SERVICES (Semaine 2)

#### Tâche 3.1 : Perplexity Service
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] `services/perplexity.py`
- [ ] Rate limiting (1000 req/mois)
- [ ] Caching (Redis, 6h TTL)
- [ ] Tests

**Prompt** :
```
Implement PerplexityService:

API: Perplexity (key: YOUR_PERPLEXITY_API_KEY_HERE)

Features:
1. Daily price research queries
2. Geopolitical news search
3. Market trend analysis
4. Citation extraction

Rate limiting:
- 1000 requests/month = ~33/day
- Implement Redis-based limiter
- Fallback to cached results if limit exceeded

Caching:
- Cache key: hash(query)
- TTL: 6 hours (news freshness vs cost)
- Invalidate on demand

Methods:
- research_daily_prices(commodity: str) -> PerplexityResponse
- research_geopolitics(commodity: str) -> PerplexityResponse
- research_market_trends(commodity: str, horizon_days: int) -> PerplexityResponse
```

---

#### Tâche 3.2 : Claude Service
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] `services/claude.py`
- [ ] Prompt templates (daily/weekly reports)
- [ ] Token counting (stay under limits)
- [ ] Tests

**Prompt** :
```
Implement ClaudeService using Anthropic API:

API: Claude (key: TBD - user to provide)
Model: claude-3-5-sonnet-20241022

Features:
1. Daily report generation (500-800 words)
2. Weekly comprehensive report (1500-2000 words)
3. Insight extraction (structured JSON)
4. Multi-commodity support

Prompt templates:
- DAILY_REPORT_TEMPLATE (see MEMOIRE_CLAUDE.md)
- WEEKLY_REPORT_TEMPLATE
- Include commodity-specific context

Token management:
- Count tokens before sending (anthropic.count_tokens)
- Alert if approaching daily limit (200k tokens/day)
- Compress context if needed (summarize old data)

Methods:
- generate_daily_report(commodity, data, analyses) -> ClaudeReport
- generate_weekly_report(commodity, week_data) -> ClaudeReport
- extract_insights(report_content) -> Dict[str, Any]
```

---

#### Tâche 3.3 : Optimisation Prompts
**Agent** : `prompt-engineer`
**Durée** : 4h
**Livrables** :
- [ ] Prompts Perplexity optimisés (5+ variants)
- [ ] Prompts Claude optimisés (daily/weekly)
- [ ] A/B testing framework
- [ ] Documentation prompt patterns

**Prompt** :
```
Optimize AI prompts for Cambodia Agri Analytics:

1. PERPLEXITY PROMPTS
Create 5+ variants for:
a) Daily price research (cashew/rubber)
b) Geopolitical events (US-China trade, Vietnam processing)
c) Market trends (7-day horizon)
d) Competitor analysis (Vietnam, India)

Requirements:
- Specific date ranges ("last 24 hours")
- Request sources/citations
- Focus on actionable insights
- Commodity-specific keywords

2. CLAUDE PROMPTS
Optimize:
a) Daily report (structure from MEMOIRE_CLAUDE.md)
b) Weekly comprehensive report
c) Crisis report (price crash scenario)

Requirements:
- Include commodity context in system prompt
- Request structured output (sections, bullet points)
- Emphasize actionable recommendations
- Include confidence levels

3. A/B TESTING
Create framework to test prompt variants:
- Metric: Relevance score (manual evaluation)
- Sample size: 10 queries per variant
- Winner selection criteria

Deliverables:
- prompt_templates.py with all optimized prompts
- A/B testing script
- Documentation of best patterns
```

---

### PHASE 4 : SCHEDULING & AUTOMATION (Semaine 2-3)

#### Tâche 4.1 : APScheduler Setup
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] `scheduler/scheduler.py` (singleton pattern)
- [ ] `scheduler/jobs.py` (job definitions)
- [ ] Timezone handling (GMT+7)
- [ ] Tests (freezegun for time mocking)

**Prompt** :
```
Implement APScheduler for automated jobs:

Schedule:
- Daily 6:00 GMT+7: Data collection + Perplexity analysis + Claude report
- Weekly Monday 6:00 GMT+7: Comprehensive report
- Hourly: Health check + cleanup old data

Jobs:
1. daily_collection_pipeline()
   - Run all 4 collectors (MEF, WITS, ODC, GDrive)
   - Store in Supabase
   - Handle partial failures (some collectors fail OK)

2. daily_perplexity_analysis()
   - Research prices (cashew + rubber)
   - Research geopolitics
   - Store analyses in Supabase

3. daily_claude_report()
   - Fetch today's data + analyses
   - Generate daily report
   - Publish to Supabase + send email

4. weekly_comprehensive_report()
   - Aggregate 7 days data
   - Deep Perplexity research
   - Generate long-form Claude report

Features:
- Job persistence (SQLite job store)
- Error notifications (email/Telegram)
- Execution logs
- Manual trigger API endpoint

Timezone: Asia/Phnom_Penh (GMT+7)
```

---

#### Tâche 4.2 : Job Monitoring & Alerts
**Agent** : `fullstack-developer`
**Durée** : 2h
**Livrables** :
- [ ] Job execution tracking
- [ ] Email alerts (SendGrid ou SMTP)
- [ ] Telegram bot alerts (optional)
- [ ] Dashboard job status widget

**Prompt** :
```
Implement job monitoring system:

1. Execution Tracking
- Log job start/end times to Supabase table `job_executions`
- Track success/failure status
- Store error messages + stack traces
- Calculate execution duration

2. Email Alerts
- Send email if job fails (SMTP or SendGrid)
- Daily summary email (jobs status)
- Weekly report delivery

3. Dashboard Widget
- Streamlit component showing last 10 job executions
- Color-coded status (green=success, red=failure)
- Execution time chart (detect slowdowns)

4. Health Checks
- Endpoint /health/jobs
- Return JSON: {last_success: timestamp, failures_last_24h: count}
```

---

### PHASE 5 : DASHBOARD STREAMLIT (Semaine 3)

#### Tâche 5.1 : Design Dashboard
**Agent** : `ui-ux-designer`
**Durée** : 4h
**Livrables** :
- [ ] Wireframes (Figma ou ASCII)
- [ ] User flows (trader, producteur, gouvernement)
- [ ] Design system (couleurs, typographie)
- [ ] Mobile-first considerations

**Prompt** :
```
Design dashboard UX for Cambodia Agri Analytics:

User Personas:
1. Trader (Phnom Penh)
   - Need: Quick price overview, alerts, trends
   - Device: Desktop + mobile
   - Frequency: Multiple times daily

2. Producteur (rural Cambodia)
   - Need: Simple price info, weekly forecasts
   - Device: Mobile 3G
   - Frequency: Weekly
   - Language: Khmer preferred

3. Government Analyst
   - Need: Comprehensive reports, export functionality
   - Device: Desktop
   - Frequency: Monthly

Pages:
1. Overview (multi-commodity dashboard)
   - KPIs: Current prices (cashew/rubber), weekly change
   - Mini charts: 30-day trends
   - Latest geopolitical events
   - Quick commodity switcher

2. Cashew Deep Dive
   - Price chart (1Y timeseries)
   - Production map (provinces with KML overlay)
   - Export destinations breakdown
   - Latest Perplexity analyses

3. Rubber Deep Dive
   - Similar structure to Cashew

4. Reports Archive
   - Daily reports (last 30 days)
   - Weekly reports (last 12 weeks)
   - PDF export functionality

5. Settings
   - Alert configuration
   - Language toggle (EN/KH)
   - Data upload (manual CSV)

Design Requirements:
- Mobile-first (3G friendly, <500KB page load)
- High contrast (readability in bright sunlight)
- Color-coded alerts (green/yellow/red)
- Minimal animations (performance)

Deliverables:
- Wireframes (low-fi + high-fi)
- Color palette
- Typography scale
- Icon set
- Responsive breakpoints
```

---

#### Tâche 5.2 : Dashboard Streamlit Implementation
**Agent** : `fullstack-developer`
**Durée** : 8h (GROS MORCEAU)
**Livrables** :
- [ ] `dashboard/app.py` (main entry)
- [ ] `dashboard/pages/` (5 pages)
- [ ] `dashboard/components/` (reusable components)
- [ ] Responsive CSS
- [ ] Tests (Playwright E2E)

**Prompt** :
```
Implement Streamlit dashboard following UX design:

Structure:
dashboard/
├── app.py                # Main entry (overview page)
├── pages/
│   ├── 1_🥜_cashew.py
│   ├── 2_🌱_rubber.py
│   ├── 3_📊_reports.py
│   └── 4_⚙️_settings.py
├── components/
│   ├── charts.py         # Plotly charts (price trends, production)
│   ├── maps.py           # Folium map (KML overlay)
│   ├── metrics.py        # KPI cards
│   └── tables.py         # Data tables (reports archive)
└── utils/
    ├── supabase.py       # Supabase client wrapper
    └── i18n.py           # Internationalization (EN/KH)

Key Components:

1. Overview Page (app.py)
   - st.set_page_config(layout="wide")
   - Commodity selector (sidebar)
   - 3-column layout: KPIs (price, volume, change)
   - 30-day price chart (Plotly)
   - Latest 3 geopolitical events (table)
   - Latest Claude report excerpt (markdown)

2. Cashew/Rubber Pages
   - Full-width price chart (1 year, zoomable)
   - Production map (Folium + KML overlay)
   - Export destinations pie chart
   - Latest 5 Perplexity analyses (expandable)
   - Data table (prices last 30 days, downloadable CSV)

3. Reports Page
   - Tabs: Daily / Weekly
   - Date range filter
   - Report cards (title, date, summary)
   - Click to expand full report (markdown)
   - PDF export button (reportlab)

4. Settings Page
   - Alert threshold sliders (price drop %, volume spike %)
   - Email input for alerts
   - Language toggle (EN/KH) - stored in session state
   - Manual CSV upload widget

Performance:
- Cache Supabase queries (@st.cache_data, TTL=5min)
- Lazy load charts (only render visible tab)
- Compress images (KML map tiles)

Deployment:
- Config for Streamlit Cloud / Railway / Render
- Environment variables from .env
- requirements.txt generation
```

---

#### Tâche 5.3 : Visualisations Interactives
**Agent** : `fullstack-developer`
**Durée** : 4h
**Livrables** :
- [ ] Plotly charts (price, volume, correlations)
- [ ] Folium map (provinces production)
- [ ] Altair charts (alternative si Plotly lent)
- [ ] Tests visualisations

**Prompt** :
```
Create advanced visualizations:

1. Price Timeseries (Plotly)
   - Dual-axis chart (price + volume)
   - Candlestick option (OHLC if data available)
   - Annotations (geopolitical events)
   - Zoom, pan, export PNG

2. Production Heatmap (Folium)
   - Cambodia map base layer
   - Choropleth by province (production intensity)
   - KML overlay (farm locations from Google Drive)
   - Popup on click (province stats)

3. Export Destinations (Plotly Sunburst)
   - Inner ring: Commodity (cashew/rubber)
   - Outer ring: Country (Vietnam, China, USA, etc.)
   - Size = export volume
   - Color = price premium

4. Correlation Matrix (Plotly Heatmap)
   - Rows/Cols: Cashew price, Rubber price, USD/KHR rate, Oil price
   - Show Pearson correlation coefficients
   - Identify leading indicators

5. Forecasting Chart (Plotly)
   - Historical prices (line)
   - Forecast (dashed line + confidence interval shading)
   - Toggle forecast horizon (7/14/30 days)

Requirements:
- Responsive (mobile-friendly)
- Fast rendering (<2s)
- Export functionality (PNG, SVG)
```

---

### PHASE 6 : TESTING (Semaine 3-4)

#### Tâche 6.1 : Tests Unitaires
**Agent** : `test-engineer`
**Durée** : 6h
**Livrables** :
- [ ] Tests collectors (pytest)
- [ ] Tests services (Perplexity, Claude mocks)
- [ ] Tests models (Pydantic validation)
- [ ] Coverage report (>80%)

**Prompt** :
```
Create comprehensive unit test suite:

tests/
├── test_collectors.py
│   ├── test_mef_collector (mock httpx responses)
│   ├── test_wits_collector (mock XML)
│   ├── test_odc_collector (mock HTML/CSV)
│   └── test_gdrive_collector (mock API + sample PDFs)
├── test_services.py
│   ├── test_perplexity_service (mock API)
│   ├── test_claude_service (mock API)
│   └── test_supabase_client (mock Supabase)
├── test_models.py
│   ├── test_commodity_models
│   ├── test_price_validation
│   └── test_analysis_models
└── conftest.py (fixtures)

Fixtures:
- sample_price_data
- mock_perplexity_response
- mock_claude_response
- mock_supabase_client

Coverage Target: >80%
Run: pytest --cov=app --cov-report=html
```

---

#### Tâche 6.2 : Tests Intégration
**Agent** : `test-engineer`
**Durée** : 4h
**Livrables** :
- [ ] Tests pipeline collection → Supabase
- [ ] Tests APScheduler jobs
- [ ] Tests API endpoints FastAPI
- [ ] Docker test environment

**Prompt** :
```
Create integration tests:

tests/integration/
├── test_collection_pipeline.py
│   - Start local Supabase (docker-compose)
│   - Run collector
│   - Verify data in DB
│   - Cleanup
├── test_scheduler_jobs.py
│   - Trigger jobs manually
│   - Verify execution logs
│   - Check error handling
└── test_api_endpoints.py
    - Test FastAPI routes
    - Health checks
    - Data retrieval endpoints

Setup:
- docker-compose.test.yml (Supabase + Redis)
- Fixtures auto-start/stop containers
- Use testcontainers-python
```

---

#### Tâche 6.3 : Tests E2E Dashboard
**Agent** : `test-engineer`
**Durée** : 4h
**Livrables** :
- [ ] Playwright tests Streamlit
- [ ] User flows (trader, producteur)
- [ ] Screenshot regression tests
- [ ] Performance tests (Lighthouse)

**Prompt** :
```
Create E2E tests for Streamlit dashboard:

tests/e2e/
├── test_overview_page.py
│   - Load overview
│   - Switch commodity (cashew ↔ rubber)
│   - Verify KPIs update
├── test_cashew_page.py
│   - Navigate to cashew page
│   - Interact with chart (zoom, pan)
│   - Click map province
│   - Download CSV
├── test_reports_page.py
│   - Filter by date range
│   - Expand report
│   - Export PDF
└── test_mobile_view.py
    - Viewport = 375x667 (iPhone SE)
    - Test touch interactions
    - Verify performance

Tools:
- Playwright (headless Chromium)
- pytest-playwright plugin
- Screenshot comparison (pixelmatch)
- Lighthouse CI (performance budget: <3s load)
```

---

#### Tâche 6.4 : Tests MCP Compliance
**Agent** : `mcp-testing-engineer`
**Durée** : 3h
**Livrables** :
- [ ] MCP Inspector validation (Supabase, Fetch, Context7)
- [ ] Protocol compliance tests
- [ ] Security audit (confused deputy, session hijacking)
- [ ] Performance benchmarks

**Prompt** :
```
Test MCP server integrations:

1. MCP Inspector Validation
   - Validate Supabase MCP schema
   - Test Fetch MCP with Cambodia APIs
   - Verify Context7 MCP storage/retrieval

2. Protocol Compliance
   - JSON-RPC 2.0 format
   - SSE fallback mechanisms
   - Error handling (invalid requests)

3. Security Audit
   - Test confused deputy scenarios
   - Attempt session hijacking
   - Validate Origin header checks
   - Test injection vulnerabilities

4. Performance Benchmarks
   - Concurrent requests (10, 50, 100)
   - Measure latency (p50, p95, p99)
   - Test under load (1000 req/min)

Deliverables:
- MCP compliance report
- Security vulnerability report (CVSS scores)
- Performance metrics (CSV)
- Recommendations for fixes
```

---

### PHASE 7 : DEPLOYMENT (Semaine 4)

#### Tâche 7.1 : Dockerization
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] Dockerfile (multi-stage build)
- [ ] docker-compose.yml (production)
- [ ] .dockerignore
- [ ] Health checks

**Prompt** :
```
Create Docker setup for production:

Dockerfile (multi-stage):
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry export -f requirements.txt > requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY dashboard/ ./dashboard/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

docker-compose.yml (production):
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.port=8501
    ports: ["8501:8501"]
    depends_on: [api]

  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]

volumes:
  redis_data:

Optimizations:
- Multi-stage build (reduce image size)
- .dockerignore (exclude tests/, .git/)
- Health checks (auto-restart on failure)
```

---

#### Tâche 7.2 : Deployment Options Analysis
**Agent** : `backend-architect`
**Durée** : 2h
**Livrables** :
- [ ] Comparaison plateformes (Render, Railway, Fly.io, VPS)
- [ ] Coût mensuel estimé par plateforme
- [ ] Recommandation finale
- [ ] Guide deployment étape par étape

**Prompt** :
```
Analyze deployment options for Python FastAPI + Streamlit:

Platforms to compare:
1. Render.com
   - Free tier: 750h/mois, 512MB RAM
   - Paid: $7/mois (1GB RAM)
   - Postgres managed: $7/mois
   - Docker support: ✅

2. Railway.app
   - Free: $5 credit/mois
   - Paid: Pay-as-you-go ($0.000463/GB-second)
   - Postgres managed: Included
   - Docker support: ✅

3. Fly.io
   - Free: 3 shared-CPU VMs, 3GB storage
   - Paid: $1.94/mois per VM
   - Postgres: Fly Postgres (free tier)
   - Docker support: ✅

4. VPS (DigitalOcean, Linode)
   - Cost: $6-12/mois (1-2GB RAM)
   - Full control
   - Manual setup (Docker Compose)

5. Streamlit Cloud
   - Free: 1 private app
   - Paid: $20/mois unlimited
   - ⚠️ Only Streamlit (no FastAPI)

Evaluation Criteria:
- Cost (monthly)
- Ease deployment
- Auto-scaling
- Monitoring included
- Uptime SLA

Recommendation:
- Test: Local (PC allumé 1 journée) OU Render free tier
- Production: [TO BE DETERMINED based on analysis]

Include step-by-step deployment guide for recommended platform.
```

---

#### Tâche 7.3 : Monitoring & Logging
**Agent** : `fullstack-developer`
**Durée** : 3h
**Livrables** :
- [ ] Sentry setup (error tracking)
- [ ] Uptime Robot (uptime monitoring)
- [ ] Structlog configuration
- [ ] Dashboard monitoring page

**Prompt** :
```
Implement production monitoring:

1. Sentry (Error Tracking)
   - SDK: sentry-sdk[fastapi]
   - Capture exceptions, slow queries
   - Breadcrumbs (APScheduler jobs)
   - Custom tags (commodity, collector)

2. Uptime Robot
   - Monitor /health endpoint
   - Alert email if down >5min
   - SMS alert if down >15min (critical)

3. Structlog (Structured Logging)
   - JSON format (easy parsing)
   - Log levels: DEBUG (dev), INFO (prod)
   - Context: request_id, user_id, commodity
   - Output: stdout (Docker logs)

4. Monitoring Dashboard (Streamlit page)
   - API health status
   - Scheduler job status
   - Error rate (last 24h)
   - Supabase connection status
   - Redis cache hit rate

5. Metrics (Prometheus + Grafana - optional)
   - Collector success rate
   - API response times
   - Database query times
   - Streamlit page load times
```

---

### PHASE 8 : REVIEW & DOCUMENTATION (Semaine 4)

#### Tâche 8.1 : Code Review Complet
**Agent** : `code-reviewer`
**Durée** : 4h
**Livrables** :
- [ ] Review rapport (Critical/Warning/Suggestion)
- [ ] Security audit (API keys, SQL injection, XSS)
- [ ] Performance optimizations identifiées
- [ ] Refactoring suggestions

**Prompt** :
```
Perform comprehensive code review:

Scope:
- All Python code (app/, dashboard/, tests/)
- Configuration files (docker-compose, pyproject.toml)
- Environment variables (.env.example)

Focus Areas:
1. Security
   - No hardcoded secrets
   - SQL injection prevention (Supabase RLS, parameterized queries)
   - Input validation (Pydantic models)
   - API rate limiting
   - CORS configuration

2. Code Quality
   - DRY violations
   - Function complexity (cyclomatic complexity <10)
   - Naming conventions (PEP 8)
   - Type hints coverage (>90%)
   - Docstrings (functions, classes)

3. Performance
   - N+1 query issues
   - Inefficient loops
   - Missing caching
   - Blocking I/O (use async)

4. Error Handling
   - Proper exception handling
   - Meaningful error messages
   - Retry logic
   - Fallback mechanisms

5. Tests
   - Coverage gaps
   - Missing edge cases
   - Flaky tests
   - Test duplication

Deliverables:
- Markdown report: CRITICAL / WARNING / SUGGESTION
- Specific line numbers + code examples
- Priority ranking (fix now vs later)
```

---

#### Tâche 8.2 : Documentation Complète
**Agent** : `context-manager`
**Durée** : 4h
**Livrables** :
- [ ] README.md détaillé
- [ ] API documentation (FastAPI auto-docs)
- [ ] Architecture diagram (updated)
- [ ] Runbook (deployment, troubleshooting)

**Prompt** :
```
Create comprehensive documentation:

README.md:
# Cambodia Agri Analytics Platform

## Overview
Multi-commodity analytics platform for Cambodia agricultural exports (Cashew, Rubber).

## Features
- Automated data collection (ODC, MEF, WITS, Google Drive)
- AI-powered analysis (Perplexity research + Claude synthesis)
- Interactive dashboard (Streamlit)
- Scheduled reports (daily 6am, weekly Monday 6am)

## Tech Stack
- Backend: Python 3.11, FastAPI, APScheduler
- Frontend: Streamlit, Plotly, Folium
- Database: Supabase (PostgreSQL)
- AI: Perplexity API, Claude API (Anthropic)
- Deployment: Docker, [Platform TBD]

## Setup (Development)
1. Prerequisites: Python 3.11, Docker, Poetry
2. Clone repo: `git clone ...`
3. Install deps: `poetry install`
4. Configure .env: `cp .env.example .env` (fill API keys)
5. Start services: `docker-compose up -d`
6. Run migrations: `python scripts/init_db.py`
7. Run API: `uvicorn app.main:app --reload`
8. Run dashboard: `streamlit run dashboard/app.py`

## Setup (Production)
[Link to Runbook]

## Architecture
[Link to diagram]

## API Documentation
- FastAPI docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Contributing
[Guidelines]

## License
MIT

---

RUNBOOK.md:
# Production Runbook

## Deployment
### Render.com (recommended)
1. Create account
2. New Web Service → Import from GitHub
3. Environment: Docker
4. Add environment variables (from .env.example)
5. Deploy

### Troubleshooting
**Issue**: Collector fails
- Check: API endpoint status
- Check: Rate limiting
- Check: Supabase connection
- Fix: Restart scheduler job

**Issue**: Dashboard slow
- Check: Supabase query performance
- Check: Cache hit rate (Redis)
- Fix: Increase TTL, add indexes

[... more scenarios ...]

---

ARCHITECTURE.md:
# System Architecture

[Mermaid diagram showing:
- External sources (ODC, MEF, WITS, GDrive)
- Collectors (async pipeline)
- Supabase (storage)
- AI layer (Perplexity, Claude)
- Scheduler (APScheduler)
- Dashboard (Streamlit)
- Monitoring (Sentry, Uptime Robot)]

## Design Decisions
1. Why Supabase vs self-hosted Postgres?
   - Managed = zero maintenance
   - Real-time subscriptions built-in
   - Cost-effective (<$25/mois)

2. Why Streamlit vs React?
   - Faster development (5x)
   - Python full-stack
   - Sufficient for analytics dashboard

[... more decisions ...]
```

---

#### Tâche 8.3 : Debugging Final & Optimisations
**Agent** : `debugger`
**Durée** : Variable (AS NEEDED)
**Livrables** :
- [ ] Bugs critiques résolus
- [ ] Optimisations performance appliquées
- [ ] Memory leaks corrigés

**Prompt** :
```
Perform final debugging pass:

1. Run full test suite
   - pytest tests/ --cov=app
   - Identify failing tests
   - Fix root causes

2. Performance profiling
   - Use cProfile on collectors
   - Identify slow functions (>500ms)
   - Optimize (caching, async, batching)

3. Memory leak detection
   - Run dashboard under load (100 concurrent users)
   - Monitor memory usage (tracemalloc)
   - Fix leaks (close connections, clear caches)

4. Edge case handling
   - Empty datasets
   - API timeouts
   - Invalid data formats
   - Network failures

Deliverables:
- Bug fix log (issue → root cause → fix)
- Performance improvements (before/after metrics)
- Remaining known issues (if any)
```

---

## RÉSUMÉ DÉLÉGATION

### Agents Utilisés : 11

| Agent | Nombre de Tâches | Heures Totales |
|-------|------------------|----------------|
| backend-architect | 4 | 14h |
| code-reviewer | 1 | 4h |
| context-manager | 1 | 4h |
| debugger | 1 | Variable |
| fullstack-developer | 13 | 45h |
| mcp-expert | 1 | 2h |
| mcp-testing-engineer | 1 | 3h |
| prompt-engineer | 1 | 4h |
| test-engineer | 3 | 14h |
| ui-ux-designer | 1 | 4h |
| **TOTAL** | **27 tâches** | **~94h** |

### Timeline : 4 Semaines

| Semaine | Phase | Heures |
|---------|-------|--------|
| 1 | Setup + DB + Collection (début) | 24h |
| 2 | Collection (fin) + AI Services + Scheduling | 24h |
| 3 | Dashboard + Tests (début) | 24h |
| 4 | Tests (fin) + Deployment + Review | 22h |

---

## NEXT STEPS IMMÉDIATS

1. ✅ Valider ce plan de délégation
2. 🔄 Créer agent custom `cambodia-epct.md`
3. 🔄 Commencer Tâche 0.1 (Architecture Système) avec `backend-architect`
4. 🔄 Parallèle : Tâche 0.2 (MCP config) avec `mcp-expert`

**Question** : Approuvez-vous ce plan ? Voulez-vous modifier priorités ou délégations ?
