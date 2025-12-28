# 🌾 Cambodia Agri Analytics Platform

Multi-commodity analytics platform for **Cashew** and **Rubber** markets in Cambodia, powered by AI-driven insights and semantic search.

---

## 🎯 Features

### Data Collection
- ✅ **MEF Cambodia** - Ministry of Economy export data
- ✅ **WITS World Bank** - International trade flows (XML API)
- ✅ **Open Development Cambodia** - Production statistics
- ✅ **Google Drive** - PDF/KML documents with OCR (Khmer → English)

### AI Analysis
- 🧠 **Perplexity API** - Daily market research & geopolitical analysis
- 📝 **Claude MOCK** - Template-based report generation (daily/weekly)
- 🔍 **ChromaDB** - Semantic search across documents, reports, and price history

### Storage
- 📊 **Supabase** - Structured data (7 tables: prices, production, reports, etc.)
- 🗄️ **ChromaDB** - Vector database (5 collections for semantic search)

### Dashboard
- 📈 **Streamlit** - Interactive dashboard with 5 pages:
  - Cashew Analytics
  - Rubber Analytics
  - Price Trends (Plotly charts)
  - Production Maps (Folium geospatial)
  - Semantic Search (ChromaDB queries)

### Automation
- ⏰ **Daily Pipeline** (6:00 AM Cambodia Time) - Data collection + price analysis
- 📅 **Weekly Pipeline** (Monday 6:00 AM) - Comprehensive market reports

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 EXTERNAL SOURCES                         │
│  MEF API │ WITS XML │ ODC HTML │ Google Drive PDF/KML   │
└────┬──────────┬─────────┬─────────────┬─────────────────┘
     │          │         │             │
     ▼ (httpx)  ▼ (httpx) ▼ (browsermcp)▼ (GDrive API + OCR)
┌─────────────────────────────────────────────────────────┐
│              DATA COLLECTORS (Python async)              │
│   MEF    │   WITS   │   ODC   │  GDrive (pytesseract)   │
└────┬──────────┬─────────┬─────────────┬─────────────────┘
     │          │         │             │
     ▼          ▼         ▼             ▼
┌─────────────────────────────────────────────────────────┐
│              DUAL STORAGE LAYER                          │
│                                                           │
│  ┌──────────────────┐      ┌────────────────────────┐   │
│  │   SUPABASE       │      │     CHROMADB           │   │
│  │ (PostgreSQL)     │◄────►│ (Vector DB)            │   │
│  │                  │      │                        │   │
│  │ • prices         │      │ • commodity_documents  │   │
│  │ • production     │      │ • perplexity_analyses  │   │
│  │ • reports        │      │ • claude_reports       │   │
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
│  └──────────────────┘      └────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              STREAMLIT DASHBOARD                         │
│                                                           │
│  📊 Cashew Analytics  │  🌱 Rubber Analytics            │
│  📈 Price Trends      │  🗺️ Production Maps             │
│  🔍 Semantic Search (ChromaDB powered)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### New: Production Data Collection (2025-12-25)

```powershell
# 1. Apply migrations (Supabase Dashboard > SQL Editor)
# Copy/paste: scripts/migrations/002_add_unique_constraint_production.sql

# 2. Test collectors
.\.venv311\Scripts\python.exe scripts\test_production_seeding.py

# 3. Seed production data (ODC + GDrive)
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

**Quick Guide:** [QUICKSTART_PRODUCTION.md](QUICKSTART_PRODUCTION.md)
**Full Documentation:** [PRODUCTION_DATA_SETUP.md](PRODUCTION_DATA_SETUP.md)

### Prerequisites

- Python 3.11+
- Docker (for ChromaDB, optional PostgreSQL/Redis)
- Poetry (recommended) or pip
- Tesseract OCR (for PDF extraction)
- Poppler (for PDF processing)

### 1. Clone Repository

```bash
git clone <repo_url>
cd cambodia-agri-analytics
```

### 2. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (see .env.example for details)
```

**Required API Keys:**
- Supabase: `SUPABASE_URL`, `SUPABASE_KEY`
- Perplexity: `PERPLEXITY_API_KEY`
- Google Drive: `GOOGLE_DRIVE_API_KEY`
- ChromaDB host (default: localhost:8000)

### 4. Start Services

```bash
# Start ChromaDB (Docker)
docker run -d -p 8000:8000 chromadb/chroma

# Optional: Start PostgreSQL + Redis (if not using Supabase managed)
docker-compose up -d
```

### 5. Initialize Databases

```bash
# Initialize Supabase schema (7 tables)
python scripts/init_db.py

# Initialize ChromaDB collections (5 collections)
python scripts/init_chromadb.py
```

### 6. Run Application

```bash
# Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# Start Streamlit dashboard (separate terminal)
streamlit run dashboard/app.py --server.port 8501
```

### 7. Access Dashboard

Open browser:
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

---

## 📁 Project Structure

```
cambodia-agri-analytics/
├── app/
│   ├── config.py                  # Pydantic settings
│   ├── models/
│   │   ├── commodity.py           # Commodity models
│   │   ├── price.py               # Price models
│   │   └── production.py          # Production models
│   ├── collectors/
│   │   ├── base_collector.py      # Abstract collector
│   │   ├── mef_collector.py       # MEF API
│   │   ├── wits_collector.py      # WITS World Bank
│   │   ├── odc_collector.py       # Open Development Cambodia
│   │   └── gdrive_collector.py    # Google Drive PDFs/KML
│   ├── services/
│   │   ├── perplexity_service.py  # Perplexity API
│   │   ├── claude_mock_service.py # Template reports
│   │   ├── chromadb_service.py    # Vector DB
│   │   └── supabase_service.py    # PostgreSQL
│   ├── scheduler/
│   │   ├── jobs.py                # Cron jobs
│   │   └── scheduler.py           # APScheduler
│   ├── api/
│   │   └── routes/                # FastAPI endpoints
│   └── utils/
├── dashboard/
│   ├── app.py                     # Streamlit main
│   └── pages/
│       ├── 1_📊_Cashew_Analytics.py
│       ├── 2_🌱_Rubber_Analytics.py
│       ├── 3_📈_Price_Trends.py
│       ├── 4_🗺️_Production_Maps.py
│       └── 5_🔍_Semantic_Search.py
├── scripts/
│   ├── init_db.py                 # Supabase migrations
│   ├── init_chromadb.py           # ChromaDB setup
│   └── test_collectors.py         # Test data sources
├── tests/
│   ├── test_collectors.py
│   └── test_services.py
├── .mcp.json                      # MCP servers config
├── .env.example                   # Environment template
├── pyproject.toml                 # Poetry dependencies
├── docker-compose.yml             # Local services
├── claudememoire                  # Project memory
└── README.md                      # This file
```

---

## 🗄️ Database Schema

### Supabase (7 Tables)

1. **commodities** - Cashew & Rubber metadata
2. **prices** - Export prices with destinations
3. **production** - Provincial production stats
4. **perplexity_analyses** - AI research results
5. **claude_reports** - Generated market reports
6. **geopolitical_events** - Events affecting markets
7. **data_sources** - Collector status tracking

### ChromaDB (5 Collections)

1. **commodity_documents** - PDFs/KML from Google Drive
2. **perplexity_analyses** - Cached research (saves 70% API calls)
3. **claude_reports** - Historical reports for pattern matching
4. **commodity_prices** - Prices with market context
5. **production_data** - Production with geospatial context

---

## 🔌 MCP Servers (6 Configured)

1. **context7** - Long-term context storage (Upstash)
2. **fetch** - HTTP requests for APIs
3. **supabase** - Direct database queries
4. **browsermcp** - JavaScript-rendered scraping
5. **playwright** - E2E tests & advanced scraping
6. **chroma** - Vector database queries

See `.mcp.json` for full configuration.

---

## ⏰ Automation Schedule

### Daily Pipeline (6:00 AM Cambodia Time)
1. Collect data from all 4 sources (MEF, WITS, ODC, GDrive)
2. Dual-write to Supabase + ChromaDB
3. Perplexity daily price research (cashew + rubber)
4. Claude MOCK daily reports
5. Publish to dashboard

### Weekly Pipeline (Monday 6:00 AM)
1. Aggregate 7-day data
2. Perplexity comprehensive market analysis
3. Claude MOCK weekly deep-dive reports
4. Email stakeholders

---

## 📊 API Endpoints

### Prices
- `GET /api/prices?commodity=cashew&limit=10`
- `GET /api/prices/latest?commodity=rubber`
- `GET /api/prices/range?start=2024-01-01&end=2024-12-31`

### Production
- `GET /api/production?commodity=cashew&year=2024`
- `GET /api/production/province?name=Kampong Cham`

### Reports
- `GET /api/reports?commodity=cashew&type=daily`
- `GET /api/reports/latest?commodity=rubber`

### Semantic Search
- `POST /api/search` - Search across all ChromaDB collections

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_collectors.py

# Test MCP servers
pytest tests/mcp/

# Test with coverage
pytest --cov=app tests/
```

---

## 🚢 Deployment

### Railway.app (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add services (PostgreSQL, Redis)
railway add

# Set environment variables
railway variables set SUPABASE_URL=...
railway variables set PERPLEXITY_API_KEY=...

# Deploy
git push
```

**Estimated Cost**: ~$60/month
- Railway.app: $15 (1GB RAM + services)
- Supabase Pro: $25 (if >500MB data)
- Perplexity API: $20 (1000 req/month)

---

## 🛠️ Development

### Add New Collector

1. Create `app/collectors/new_collector.py` extending `BaseCollector`
2. Implement `collect()` and `validate()` methods
3. Register in main pipeline

### Add New Service

1. Create `app/services/new_service.py`
2. Add configuration to `app/config.py`
3. Use in jobs or API routes

### Add Dashboard Page

1. Create `dashboard/pages/N_PageName.py`
2. Streamlit will auto-discover it
3. Use Plotly for charts, Folium for maps

---

## 🐛 Troubleshooting

### ChromaDB Connection Error
```bash
# Ensure ChromaDB is running
docker ps | grep chroma

# Restart if needed
docker run -d -p 8000:8000 chromadb/chroma
```

### Supabase Auth Error
- Verify `SUPABASE_KEY` in `.env`
- Check project ref matches: `xqfozbocgyrelznccweh`
- Get keys from: https://supabase.com/dashboard/project/xqfozbocgyrelznccweh/settings/api

### Perplexity Rate Limit
- Check usage: `PerplexityService.get_stats()`
- Increase ChromaDB caching to reduce API calls

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Contact

For questions or support, see `claudememoire` for detailed project documentation.

---

**Built with ❤️ for Cambodia's agricultural sector**
#   c a m b o d i a  
 #   c a m b o d i a  
 