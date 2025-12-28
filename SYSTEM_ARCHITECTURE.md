# CAMBODIA AGRI ANALYTICS - COMPLETE SYSTEM ARCHITECTURE

**Version:** 1.0
**Date:** 2025-12-24
**Author:** Backend Architect Agent
**Project:** Multi-Commodity Analytics Platform (Cashew Primary, Rubber Secondary)

---

## TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Technology Stack](#3-technology-stack)
4. [Supabase Schema](#4-supabase-schema)
5. [ChromaDB Collections Strategy](#5-chromadb-collections-strategy)
6. [API Endpoints Structure](#6-api-endpoints-structure)
7. [Data Flow Architecture](#7-data-flow-architecture)
8. [Caching Strategy](#8-caching-strategy)
9. [MCP Integration Points](#9-mcp-integration-points)
10. [Scheduling Architecture](#10-scheduling-architecture)
11. [Security & Authentication](#11-security--authentication)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Monitoring & Observability](#13-monitoring--observability)
14. [Scalability Considerations](#14-scalability-considerations)

---

## 1. SYSTEM OVERVIEW

### 1.1 Vision
Real-time analytics platform for Cambodia's agricultural commodities (Cashew & Rubber) with AI-powered geopolitical analysis and price forecasting.

### 1.2 Core Capabilities
- **Multi-Source Data Aggregation**: ODC, MEF Cambodia, WITS, Google Drive (PDF/KML)
- **AI-Powered Analysis**: Perplexity (research) + Claude (synthesis)
- **Semantic Intelligence**: ChromaDB for context-aware search
- **Real-Time Dashboard**: Streamlit with interactive visualizations
- **Automated Reporting**: Daily/Weekly AI-generated insights

### 1.3 Target Users
1. **Exporters/Traders**: Price arbitrage opportunities
2. **Government Agencies**: Policy insights
3. **Investors**: Market entry signals
4. **Producers**: Optimal selling windows

---

## 2. ARCHITECTURE DIAGRAM

### 2.1 High-Level System Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        ODC[Open Development Cambodia]
        MEF[MEF Cambodia API]
        WITS[World Bank WITS]
        GDrive[Google Drive PDFs/KML]
    end

    subgraph "Data Collection Layer"
        ODC_Collector[ODC Collector]
        MEF_Collector[MEF Collector]
        WITS_Collector[WITS Collector]
        GDrive_Parser[Google Drive Parser]

        ODC --> ODC_Collector
        MEF --> MEF_Collector
        WITS --> WITS_Collector
        GDrive --> GDrive_Parser
    end

    subgraph "MCP Layer"
        MCP_Fetch[Fetch MCP<br/>HTTP Requests]
        MCP_Browser[BrowserMCP<br/>Web Scraping]
        MCP_Supabase[Supabase MCP<br/>DB Queries]
        MCP_Context7[Context7 MCP<br/>Long-term Memory]
        MCP_Chroma[ChromaDB MCP<br/>Vector Search]
        MCP_Playwright[Playwright MCP<br/>E2E Tests]

        ODC_Collector --> MCP_Fetch
        MEF_Collector --> MCP_Fetch
        WITS_Collector --> MCP_Fetch
        GDrive_Parser --> MCP_Fetch
        ODC_Collector --> MCP_Browser
    end

    subgraph "Storage Layer"
        Supabase[(Supabase PostgreSQL<br/>Structured Data)]
        ChromaDB[(ChromaDB<br/>Vector Embeddings)]
        Redis[(Redis Cache<br/>Perplexity Responses)]

        ODC_Collector --> Supabase
        MEF_Collector --> Supabase
        WITS_Collector --> Supabase
        GDrive_Parser --> Supabase

        ODC_Collector --> ChromaDB
        MEF_Collector --> ChromaDB
        WITS_Collector --> ChromaDB
        GDrive_Parser --> ChromaDB
    end

    subgraph "AI/Intelligence Layer"
        Perplexity[Perplexity API<br/>Geopolitical Research]
        Claude[Claude API MOCK<br/>Report Synthesis]

        Perplexity --> Redis
        Redis --> Perplexity
        Perplexity --> ChromaDB
        ChromaDB --> Claude
        Supabase --> Claude
        Claude --> Supabase
        Claude --> ChromaDB
    end

    subgraph "Orchestration Layer"
        APScheduler[APScheduler<br/>Cron Jobs]

        APScheduler --> ODC_Collector
        APScheduler --> MEF_Collector
        APScheduler --> WITS_Collector
        APScheduler --> Perplexity
        APScheduler --> Claude
    end

    subgraph "API Layer"
        FastAPI[FastAPI Backend<br/>REST Endpoints]

        Supabase --> FastAPI
        ChromaDB --> FastAPI
        Redis --> FastAPI
        MCP_Supabase --> FastAPI
        MCP_Chroma --> FastAPI
    end

    subgraph "Presentation Layer"
        Streamlit[Streamlit Dashboard<br/>Interactive UI]

        FastAPI --> Streamlit
    end

    subgraph "Testing & Deployment"
        Playwright_Tests[Playwright E2E Tests]
        Railway[Railway.app<br/>Deployment]

        MCP_Playwright --> Playwright_Tests
        Streamlit --> Playwright_Tests
        FastAPI --> Railway
        Streamlit --> Railway
    end

    style Supabase fill:#3ecf8e
    style ChromaDB fill:#ff6b6b
    style Redis fill:#dc382d
    style Perplexity fill:#20808d
    style Claude fill:#cc785c
    style FastAPI fill:#009688
    style Streamlit fill:#ff4b4b
    style Railway fill:#0b0d0e
```

### 2.2 Data Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES LAYER                             │
│  [ODC] [MEF API] [WITS] [Google Drive PDFs/KML]                       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTORS (Python)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
│  │ODC       │  │MEF       │  │WITS      │  │Google Drive  │          │
│  │Collector │  │Collector │  │Collector │  │Parser        │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘          │
│       │             │             │                │                   │
│       └─────────────┴─────────────┴────────────────┘                   │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   DUAL STORAGE (Structured + Semantic)                  │
│                                                                         │
│  ┌─────────────────────┐              ┌──────────────────────┐        │
│  │  SUPABASE (PGSQL)   │              │   CHROMADB (VECTOR)  │        │
│  │  ─────────────────  │              │  ──────────────────  │        │
│  │  • commodities      │              │  • commodity_docs    │        │
│  │  • prices           │◄────────────►│  • perplexity_analyses│       │
│  │  • production       │  Sync IDs    │  • claude_reports    │        │
│  │  • perplexity_analyses│            │  • commodity_prices  │        │
│  │  • claude_reports   │              │  • production_data   │        │
│  │  • geopolitical_events│            │                      │        │
│  │  • data_sources     │              │  [Semantic Search]   │        │
│  └─────────────────────┘              └──────────────────────┘        │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      AI INTELLIGENCE PIPELINE                           │
│                                                                         │
│  ┌──────────────────┐      ┌────────────┐      ┌──────────────────┐  │
│  │  PERPLEXITY API  │─────►│   REDIS    │      │   CONTEXT7 MCP   │  │
│  │  (Research)      │      │   CACHE    │      │  (Long Memory)   │  │
│  └────────┬─────────┘      └────────────┘      └──────────────────┘  │
│           │                                                             │
│           │  Context Retrieval                                         │
│           ▼                                                             │
│  ┌──────────────────────────────────────────┐                         │
│  │         CHROMADB SEMANTIC SEARCH          │                         │
│  │  • Similar market conditions              │                         │
│  │  • Historical patterns                    │                         │
│  │  • Geopolitical precedents                │                         │
│  └──────────────┬───────────────────────────┘                         │
│                 │                                                       │
│                 ▼                                                       │
│  ┌──────────────────────────────────────────┐                         │
│  │         CLAUDE API (MOCK)                 │                         │
│  │  • Daily Reports (6:30 AM)                │                         │
│  │  • Weekly Analysis (Monday 6:00 AM)       │                         │
│  │  • Crisis Alerts (On-Demand)              │                         │
│  └──────────────┬───────────────────────────┘                         │
│                 │                                                       │
│                 └──►  Store Reports (Supabase + ChromaDB)              │
└─────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI REST LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Endpoints:                                                   │     │
│  │  • GET  /api/commodities/{cashew,rubber}                     │     │
│  │  • GET  /api/prices?commodity=cashew&start=2024-01-01        │     │
│  │  • GET  /api/production?province=Kampong_Cham                │     │
│  │  • GET  /api/analyses?type=geopolitics&limit=10              │     │
│  │  • GET  /api/reports/{daily,weekly}?date=2024-12-24          │     │
│  │  • POST /api/search (Semantic ChromaDB Query)                │     │
│  │  • GET  /api/events?impact_level=high                        │     │
│  │  • GET  /api/health                                          │     │
│  └──────────────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STREAMLIT DASHBOARD                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Overview    │  │ Price Trends │  │ Geopolitics  │  │  Reports  │ │
│  │  Page        │  │ Charts       │  │ Timeline     │  │  Archive  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                                         │
│  Features:                                                              │
│  • Real-time price charts (Plotly)                                     │
│  • Geographic heatmaps (KML overlay)                                   │
│  • Semantic search widget (ChromaDB)                                   │
│  • AI-generated insights display                                       │
│  • Export to PDF/CSV                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TECHNOLOGY STACK

### 3.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | FastAPI | 0.109+ | REST API, async operations |
| **Frontend** | Streamlit | 1.30+ | Interactive dashboard |
| **Database** | Supabase (PostgreSQL) | 15+ | Structured data storage |
| **Vector DB** | ChromaDB | 0.4.22+ | Semantic search, embeddings |
| **Cache** | Redis | 7.2+ | Perplexity response cache |
| **Scheduler** | APScheduler | 3.10+ | Cron jobs, automation |
| **AI Research** | Perplexity API | Latest | Geopolitical research |
| **AI Synthesis** | Claude API (MOCK) | Sonnet 4.5 | Report generation |
| **Deployment** | Railway.app | N/A | Cloud hosting |
| **Testing** | Playwright | 1.40+ | E2E tests |

### 3.2 Python Dependencies

```python
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
streamlit==1.30.0
supabase==2.3.0
chromadb==0.4.22
redis==5.0.1
apscheduler==3.10.4
anthropic==0.18.0  # Claude API
requests==2.31.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
pandas==2.1.4
plotly==5.18.0
pdfplumber==0.10.3  # PDF parsing
xmltodict==0.13.0  # WITS XML parsing
beautifulsoup4==4.12.2  # ODC scraping
sqlalchemy==2.0.25
alembic==1.13.1  # Database migrations
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0  # Async HTTP client
```

### 3.3 Node.js Dependencies (MCP Servers)

```json
{
  "dependencies": {
    "@modelcontextprotocol/server-fetch": "latest",
    "@supabase/mcp-server-supabase": "latest",
    "@browsermcp/mcp": "latest",
    "@executeautomation/playwright-mcp-server": "latest",
    "@upstash/context7-mcp": "latest",
    "@modelcontextprotocol/server-chroma": "latest"
  }
}
```

---

## 4. SUPABASE SCHEMA

### 4.1 Database Schema (7 Core Tables)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ============================================================================
-- TABLE 1: COMMODITIES (Master Reference)
-- ============================================================================
CREATE TABLE commodities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL, -- 'cashew', 'rubber'
  display_name TEXT NOT NULL, -- 'Cashew Nut', 'Natural Rubber'
  category TEXT NOT NULL, -- 'nut', 'industrial_crop'
  hs_code TEXT, -- Harmonized System code (e.g., '080130' for cashew)
  unit_of_measure TEXT DEFAULT 'tons', -- 'tons', 'kg'
  global_rank INTEGER, -- Cambodia's global production rank
  is_active BOOLEAN DEFAULT true,
  metadata JSONB, -- Flexible additional data
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initial data
INSERT INTO commodities (name, display_name, category, hs_code, global_rank, metadata) VALUES
('cashew', 'Cashew Nut', 'nut', '080130', 3, '{"primary_destinations": ["Vietnam", "China"], "processing_rate": 0.10}'),
('rubber', 'Natural Rubber', 'industrial_crop', '400110', 7, '{"primary_destinations": ["China", "Malaysia"], "processing_rate": 0.25}');

-- ============================================================================
-- TABLE 2: DATA_SOURCES (Track Data Provenance)
-- ============================================================================
CREATE TABLE data_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_name TEXT UNIQUE NOT NULL, -- 'ODC', 'MEF', 'WITS', 'Google_Drive'
  source_type TEXT NOT NULL, -- 'api', 'scraper', 'manual'
  base_url TEXT,
  update_frequency TEXT, -- 'daily', 'weekly', 'monthly'
  last_successful_fetch TIMESTAMPTZ,
  last_error TEXT,
  is_active BOOLEAN DEFAULT true,
  metadata JSONB, -- API keys (encrypted), rate limits, etc.
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initial data
INSERT INTO data_sources (source_name, source_type, base_url, update_frequency) VALUES
('ODC', 'scraper', 'https://data.opendevelopmentcambodia.net', 'weekly'),
('MEF', 'api', 'https://data.mef.gov.kh/api/v1/public-datasets', 'daily'),
('WITS', 'api', 'http://wits.worldbank.org/API/V1/datasource', 'monthly'),
('Google_Drive', 'manual', 'https://drive.google.com', 'on_demand');

-- ============================================================================
-- TABLE 3: PRICES (Time-Series Price Data)
-- ============================================================================
CREATE TABLE prices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
  source_id UUID NOT NULL REFERENCES data_sources(id),
  date DATE NOT NULL,
  price_usd_per_ton DECIMAL(10,2) NOT NULL,
  volume_tons INTEGER,
  country_destination TEXT, -- 'Vietnam', 'China', 'USA', etc.
  quality_grade TEXT, -- 'W180', 'W240', 'W320' (cashew), 'RSS1', 'RSS3' (rubber)
  currency_original TEXT DEFAULT 'USD',
  price_original DECIMAL(10,2), -- Original price before USD conversion
  market_conditions TEXT[], -- ['high_demand', 'supply_shortage', 'monsoon_delay']
  confidence_score DECIMAL(3,2) DEFAULT 1.0, -- 0.0-1.0 data reliability
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  CONSTRAINT unique_price_record UNIQUE (commodity_id, source_id, date, country_destination, quality_grade),
  CONSTRAINT valid_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Indexes for performance (time-series queries)
CREATE INDEX idx_prices_commodity_date ON prices(commodity_id, date DESC);
CREATE INDEX idx_prices_destination ON prices(country_destination) WHERE country_destination IS NOT NULL;
CREATE INDEX idx_prices_quality_grade ON prices(quality_grade) WHERE quality_grade IS NOT NULL;
CREATE INDEX idx_prices_date_range ON prices(date DESC);
CREATE INDEX idx_prices_market_conditions ON prices USING GIN(market_conditions);

-- ============================================================================
-- TABLE 4: PRODUCTION_DATA (Agricultural Production Statistics)
-- ============================================================================
CREATE TABLE production_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
  source_id UUID NOT NULL REFERENCES data_sources(id),
  year INTEGER NOT NULL,
  province TEXT NOT NULL, -- 'Kampong Cham', 'Ratanakiri', etc.
  area_hectares DECIMAL(12,2), -- Cultivation area
  production_tons DECIMAL(12,2), -- Total production
  yield_kg_per_hectare DECIMAL(10,2), -- Productivity metric
  num_farmers INTEGER, -- Number of farming households
  geolocation JSONB, -- {"lat": 12.5, "lon": 105.4, "kml_file": "kampong_cham.kml"}
  growth_rate_yoy DECIMAL(5,2), -- Year-over-year growth %
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  CONSTRAINT unique_production_record UNIQUE (commodity_id, source_id, year, province),
  CONSTRAINT valid_year CHECK (year >= 2000 AND year <= 2100)
);

-- Indexes
CREATE INDEX idx_production_commodity_year ON production_data(commodity_id, year DESC);
CREATE INDEX idx_production_province ON production_data(province);
CREATE INDEX idx_production_geolocation ON production_data USING GIN(geolocation);

-- ============================================================================
-- TABLE 5: PERPLEXITY_ANALYSES (AI Research Results)
-- ============================================================================
CREATE TABLE perplexity_analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  query_type TEXT NOT NULL, -- 'price_trend', 'geopolitics', 'market_news', 'competitor_analysis'
  query_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  citations JSONB, -- [{"url": "...", "title": "...", "domain": "..."}]
  search_model TEXT DEFAULT 'sonar-pro', -- Perplexity model used
  tokens_used INTEGER,
  cost_usd DECIMAL(6,4), -- Track API costs
  cache_hit BOOLEAN DEFAULT false, -- Was this served from cache?
  relevance_score DECIMAL(3,2), -- 0.0-1.0 human feedback
  keywords TEXT[], -- Extracted key terms
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ -- For cache invalidation
);

-- Indexes
CREATE INDEX idx_perplexity_commodity_created ON perplexity_analyses(commodity_id, created_at DESC);
CREATE INDEX idx_perplexity_query_type ON perplexity_analyses(query_type);
CREATE INDEX idx_perplexity_keywords ON perplexity_analyses USING GIN(keywords);
CREATE INDEX idx_perplexity_cache_expiry ON perplexity_analyses(expires_at) WHERE expires_at IS NOT NULL;

-- Full-text search on query/response
CREATE INDEX idx_perplexity_fulltext ON perplexity_analyses USING GIN(to_tsvector('english', query_text || ' ' || response_text));

-- ============================================================================
-- TABLE 6: CLAUDE_REPORTS (AI-Generated Reports)
-- ============================================================================
CREATE TABLE claude_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  report_type TEXT NOT NULL, -- 'daily', 'weekly', 'crisis', 'custom'
  title TEXT NOT NULL,
  content TEXT NOT NULL, -- Full markdown report
  executive_summary TEXT, -- First 2-3 sentences
  insights JSONB, -- ["Key insight 1", "Key insight 2", ...]
  recommendations JSONB, -- {"exporters": [...], "producers": [...], "government": [...]}
  risk_level TEXT, -- 'low', 'medium', 'high', 'critical'
  sentiment TEXT, -- 'bullish', 'bearish', 'neutral'
  price_range_usd JSONB, -- {"min": 2000, "max": 2500, "avg": 2250}
  data_period_start DATE, -- Report covers data from...
  data_period_end DATE, -- ...to
  perplexity_analyses_used UUID[], -- References to perplexity_analyses.id
  tokens_used INTEGER,
  cost_usd DECIMAL(6,4),
  published_at TIMESTAMPTZ, -- NULL if draft
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reports_commodity_type_created ON claude_reports(commodity_id, report_type, created_at DESC);
CREATE INDEX idx_reports_published ON claude_reports(published_at DESC) WHERE published_at IS NOT NULL;
CREATE INDEX idx_reports_sentiment ON claude_reports(sentiment) WHERE sentiment IS NOT NULL;
CREATE INDEX idx_reports_risk ON claude_reports(risk_level) WHERE risk_level IS NOT NULL;

-- Full-text search
CREATE INDEX idx_reports_fulltext ON claude_reports USING GIN(to_tsvector('english', title || ' ' || content));

-- ============================================================================
-- TABLE 7: GEOPOLITICAL_EVENTS (Manual + AI-Extracted Events)
-- ============================================================================
CREATE TABLE geopolitical_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  commodity_id UUID REFERENCES commodities(id),
  event_date DATE NOT NULL,
  event_type TEXT NOT NULL, -- 'trade_policy', 'tariff_change', 'political_tension', 'natural_disaster'
  title TEXT NOT NULL,
  description TEXT,
  impact_level TEXT NOT NULL, -- 'low', 'medium', 'high', 'critical'
  countries_involved TEXT[], -- ['Cambodia', 'Vietnam', 'USA']
  source_url TEXT,
  source_id UUID REFERENCES data_sources(id),
  sentiment TEXT, -- 'positive', 'negative', 'neutral'
  price_impact_usd DECIMAL(10,2), -- Estimated price movement
  related_perplexity_id UUID REFERENCES perplexity_analyses(id),
  verified BOOLEAN DEFAULT false, -- Human verification flag
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_commodity_date ON geopolitical_events(commodity_id, event_date DESC);
CREATE INDEX idx_events_impact ON geopolitical_events(impact_level);
CREATE INDEX idx_events_countries ON geopolitical_events USING GIN(countries_involved);
CREATE INDEX idx_events_type ON geopolitical_events(event_type);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES (Future Multi-Tenancy)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE commodities ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE perplexity_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE geopolitical_events ENABLE ROW LEVEL SECURITY;

-- Public read access (for now - adjust for multi-tenancy later)
CREATE POLICY "Public read access" ON commodities FOR SELECT USING (is_active = true);
CREATE POLICY "Public read access" ON data_sources FOR SELECT USING (is_active = true);
CREATE POLICY "Public read access" ON prices FOR SELECT USING (true);
CREATE POLICY "Public read access" ON production_data FOR SELECT USING (true);
CREATE POLICY "Public read access" ON perplexity_analyses FOR SELECT USING (true);
CREATE POLICY "Public read access" ON claude_reports FOR SELECT USING (published_at IS NOT NULL);
CREATE POLICY "Public read access" ON geopolitical_events FOR SELECT USING (true);

-- Service role has full access (backend only)
-- Note: Use service_role_key for backend operations, anon_key for frontend

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_commodities_updated_at BEFORE UPDATE ON commodities
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON claude_reports
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MATERIALIZED VIEW: LATEST PRICES (for performance)
-- ============================================================================
CREATE MATERIALIZED VIEW latest_prices AS
SELECT DISTINCT ON (p.commodity_id, p.country_destination, p.quality_grade)
  p.id,
  p.commodity_id,
  c.name AS commodity_name,
  p.date,
  p.price_usd_per_ton,
  p.volume_tons,
  p.country_destination,
  p.quality_grade,
  p.market_conditions
FROM prices p
JOIN commodities c ON p.commodity_id = c.id
ORDER BY p.commodity_id, p.country_destination, p.quality_grade, p.date DESC;

CREATE UNIQUE INDEX idx_latest_prices_unique ON latest_prices(commodity_id, country_destination, quality_grade);

-- Refresh materialized view (run in scheduler)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY latest_prices;
```

### 4.2 Schema Optimization Notes

1. **Time-Series Optimization**: Partitioning by date for `prices` table (future enhancement)
2. **JSONB Indexing**: GIN indexes on JSONB columns for fast queries
3. **Full-Text Search**: PostgreSQL tsvector for semantic text search
4. **Materialized Views**: Pre-aggregated latest prices for dashboard performance
5. **RLS Policies**: Ready for multi-tenancy (organization-based access control)

---

## 5. CHROMADB COLLECTIONS STRATEGY

### 5.1 Collection Architecture

ChromaDB serves as the **semantic intelligence layer** - bridging structured data (Supabase) with AI context retrieval.

```python
# services/chromadb/collections.py
from chromadb import Client, Settings
from chromadb.config import Settings
import chromadb

# Initialize ChromaDB client
client = chromadb.HttpClient(host="localhost", port=8000)

# ============================================================================
# COLLECTION 1: commodity_documents
# ============================================================================
commodity_documents = client.create_collection(
    name="commodity_documents",
    metadata={
        "description": "PDF/KML documents from Google Drive (cashew/rubber)",
        "embedding_model": "all-MiniLM-L6-v2",  # 384-dim multilingual
        "languages": ["en", "km"]  # English + Khmer
    }
)
```

**Schema**:
```python
{
    "id": "doc_uuid_001",
    "document": "Cashew cultivation in Kampong Cham province requires well-drained sandy loam...",
    "metadata": {
        "commodity": "cashew",  # or "rubber"
        "source_file": "cambodia_cashew_manual_2023.pdf",
        "language": "en",  # or "km" (Khmer)
        "page_number": 15,
        "upload_date": "2024-01-01",
        "file_type": "pdf",  # or "kml"
        "province": "Kampong Cham",
        "geolocation": {"lat": 12.5, "lon": 104.9},  # if KML
        "ocr_confidence": 0.95,  # if OCR was used
        "chunk_index": 0  # for large docs split into chunks
    }
}
```

**Query Examples**:
```python
# Multi-language search (Khmer → English embeddings work!)
results = commodity_documents.query(
    query_texts=["ការដាំដំណាំដីឡាំ"],  # "cashew planting" in Khmer
    where={"commodity": "cashew", "language": "km"},
    n_results=5
)

# Geospatial + semantic
results = commodity_documents.query(
    query_texts=["best soil conditions for rubber"],
    where={"file_type": "kml", "province": "Ratanakiri"},
    n_results=10
)
```

---

### 5.2 Collection 2: perplexity_analyses

```python
perplexity_analyses = client.create_collection(
    name="perplexity_analyses",
    metadata={
        "description": "Perplexity API research results with citations",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)
```

**Schema**:
```python
{
    "id": "perplexity_uuid_001",
    "document": "Vietnam's cashew processing industry is experiencing capacity constraints...",
    "metadata": {
        "commodity": "cashew",
        "query_type": "competitor_analysis",  # price|geopolitics|market_trends|competitor_analysis
        "query_date": "2024-12-24T06:15:00Z",
        "citations": [
            {"url": "https://vneconomy.vn/...", "title": "Vietnam Cashew Report", "domain": "vneconomy.vn"}
        ],
        "keywords": ["Vietnam", "processing", "capacity", "export"],
        "supabase_id": "uuid_from_perplexity_analyses_table",
        "relevance_score": 0.92,
        "search_model": "sonar-pro"
    }
}
```

**Query Examples**:
```python
# Find past analyses on similar topics
results = perplexity_analyses.query(
    query_texts=["Vietnam cashew processing bottlenecks"],
    where={"commodity": "cashew", "query_type": "competitor_analysis"},
    n_results=5
)

# Historical geopolitical context
results = perplexity_analyses.query(
    query_texts=["US-China trade war cashew impact"],
    where={"query_type": "geopolitics"},
    where_document={"$contains": "tariff"},
    n_results=10
)
```

---

### 5.3 Collection 3: claude_reports

```python
claude_reports = client.create_collection(
    name="claude_reports",
    metadata={
        "description": "AI-generated market reports (daily/weekly)",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)
```

**Schema**:
```python
{
    "id": "report_uuid_001",
    "document": "**Executive Summary**: Cashew prices dropped 3.2% this week due to oversupply...",
    "metadata": {
        "commodity": "cashew",
        "report_type": "weekly",  # daily|weekly|crisis|custom
        "created_at": "2024-12-24T06:30:00Z",
        "data_period_start": "2024-12-17",
        "data_period_end": "2024-12-24",
        "insights": [
            "Vietnamese demand decreased 15%",
            "Cambodia production up 8% YoY",
            "China stockpiling behavior detected"
        ],
        "sentiment": "bearish",  # bullish|bearish|neutral
        "risk_level": "medium",  # low|medium|high|critical
        "price_range_usd": {"min": 2100, "max": 2450, "avg": 2275},
        "supabase_id": "uuid_from_claude_reports_table"
    }
}
```

**Query Examples**:
```python
# Find similar market conditions in history
results = claude_reports.query(
    query_texts=["price drop oversupply Vietnam demand decrease"],
    where={"commodity": "cashew", "sentiment": "bearish"},
    n_results=5
)

# Crisis precedent search
results = claude_reports.query(
    query_texts=["sudden export ban"],
    where={"report_type": "crisis"},
    n_results=3
)
```

---

### 5.4 Collection 4: commodity_prices

**Purpose**: Semantic search over price data with market context (complements Supabase SQL queries)

```python
commodity_prices = client.create_collection(
    name="commodity_prices",
    metadata={
        "description": "Price data with contextual embeddings",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)
```

**Schema**:
```python
{
    "id": "price_uuid_001",
    "document": "2024-12-20: Cashew W320 $2,450/ton Vietnam high_demand supply_shortage monsoon_delay",
    "metadata": {
        "commodity": "cashew",
        "date": "2024-12-20",
        "price_usd": 2450,
        "volume_tons": 1200,
        "destination": "Vietnam",
        "quality_grade": "W320",
        "market_conditions": ["high_demand", "supply_shortage", "monsoon_delay"],
        "supabase_id": "uuid_from_prices_table"
    }
}
```

**Query Examples**:
```python
# Find analogous price scenarios
results = commodity_prices.query(
    query_texts=["high Vietnam demand with limited supply W320 grade"],
    where={"commodity": "cashew", "quality_grade": "W320"},
    n_results=20
)

# Price forecasting training data
results = commodity_prices.query(
    query_texts=["$2400-2600 range high demand China"],
    where_document={"$contains": "China"},
    n_results=50
)
```

---

### 5.5 Collection 5: production_data

```python
production_data = client.create_collection(
    name="production_data",
    metadata={
        "description": "Agricultural production with geospatial context",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)
```

**Schema**:
```python
{
    "id": "prod_uuid_001",
    "document": "Kampong Cham 2023: 5000ha cashew, 800kg/ha yield, 4000 tons, 15% YoY growth",
    "metadata": {
        "commodity": "cashew",
        "province": "Kampong Cham",
        "year": 2023,
        "area_hectares": 5000,
        "production_tons": 4000,
        "yield_kg_per_ha": 800,
        "growth_rate_yoy": 15.0,
        "geolocation": {"lat": 12.5, "lon": 105.4},
        "supabase_id": "uuid_from_production_data_table"
    }
}
```

**Query Examples**:
```python
# High-yield region discovery
results = production_data.query(
    query_texts=["provinces with highest productivity above 900kg per hectare"],
    where={"commodity": "rubber"},
    n_results=5
)

# Growth trend analysis
results = production_data.query(
    query_texts=["rapid production expansion 2020-2024"],
    where={"year": {"$gte": 2020}},
    n_results=15
)
```

---

### 5.6 ChromaDB Integration Workflow

```python
# services/chromadb/integration.py

class ChromaDBIntegration:
    """Dual-write to Supabase + ChromaDB with sync"""

    async def store_price_data(self, price_data: dict):
        """Example: Store price in both databases"""

        # 1. Write to Supabase (structured)
        supabase_response = await supabase.from_("prices").insert(price_data).execute()
        price_id = supabase_response.data[0]['id']

        # 2. Create semantic document
        semantic_doc = (
            f"{price_data['date']}: {price_data['commodity']} "
            f"{price_data['quality_grade']} ${price_data['price_usd_per_ton']}/ton "
            f"{price_data['country_destination']} "
            f"{' '.join(price_data.get('market_conditions', []))}"
        )

        # 3. Write to ChromaDB (semantic)
        commodity_prices.add(
            documents=[semantic_doc],
            metadatas=[{**price_data, "supabase_id": price_id}],
            ids=[price_id]
        )

        return price_id

    async def semantic_search_with_sql(self, query: str, filters: dict):
        """Hybrid search: ChromaDB semantic + Supabase structured"""

        # 1. Semantic search in ChromaDB
        chroma_results = commodity_prices.query(
            query_texts=[query],
            where=filters,
            n_results=20
        )

        # 2. Extract Supabase IDs
        supabase_ids = [m['supabase_id'] for m in chroma_results['metadatas'][0]]

        # 3. Fetch full structured data from Supabase
        full_data = await supabase.from_("prices") \
            .select("*") \
            .in_("id", supabase_ids) \
            .execute()

        return full_data.data
```

---

## 6. API ENDPOINTS STRUCTURE

### 6.1 FastAPI Application Architecture

```python
# main.py
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="Cambodia Agri Analytics API",
    description="Multi-commodity analytics platform with AI-powered insights",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS for Streamlit dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "supabase": await check_supabase_connection(),
            "chromadb": await check_chromadb_connection(),
            "redis": await check_redis_connection()
        }
    }
```

### 6.2 Core Endpoints

#### 6.2.1 Commodities

```python
# api/commodities.py

@app.get("/api/commodities", tags=["Commodities"])
async def list_commodities(active_only: bool = True):
    """List all available commodities"""
    query = supabase.from_("commodities").select("*")
    if active_only:
        query = query.eq("is_active", True)
    return query.execute().data

@app.get("/api/commodities/{commodity_name}", tags=["Commodities"])
async def get_commodity_details(commodity_name: str):
    """Get detailed commodity information"""
    result = supabase.from_("commodities") \
        .select("*") \
        .eq("name", commodity_name) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Commodity not found")

    return result.data
```

#### 6.2.2 Prices

```python
# api/prices.py

@app.get("/api/prices", tags=["Prices"])
async def get_prices(
    commodity: str = Query(..., description="cashew or rubber"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    destination: Optional[str] = None,
    quality_grade: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get price time-series data with filters"""

    # Get commodity_id
    commodity_data = supabase.from_("commodities") \
        .select("id") \
        .eq("name", commodity) \
        .single() \
        .execute()

    query = supabase.from_("prices") \
        .select("*, commodities(name, display_name), data_sources(source_name)") \
        .eq("commodity_id", commodity_data.data['id']) \
        .order("date", desc=True) \
        .limit(limit)

    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    if destination:
        query = query.eq("country_destination", destination)
    if quality_grade:
        query = query.eq("quality_grade", quality_grade)

    return query.execute().data

@app.get("/api/prices/latest", tags=["Prices"])
async def get_latest_prices(commodity: str = Query(...)):
    """Get latest prices from materialized view"""

    result = supabase.rpc("get_latest_prices", {"commodity_name": commodity}).execute()
    return result.data

@app.get("/api/prices/statistics", tags=["Prices"])
async def get_price_statistics(
    commodity: str,
    start_date: date,
    end_date: date,
    destination: Optional[str] = None
):
    """Get aggregated price statistics (min, max, avg, volatility)"""

    # SQL aggregation query
    query = f"""
    SELECT
        MIN(price_usd_per_ton) as min_price,
        MAX(price_usd_per_ton) as max_price,
        AVG(price_usd_per_ton) as avg_price,
        STDDEV(price_usd_per_ton) as price_volatility,
        COUNT(*) as data_points
    FROM prices p
    JOIN commodities c ON p.commodity_id = c.id
    WHERE c.name = '{commodity}'
    AND p.date BETWEEN '{start_date}' AND '{end_date}'
    """

    if destination:
        query += f" AND p.country_destination = '{destination}'"

    result = supabase.rpc("execute_sql", {"query": query}).execute()
    return result.data[0]
```

#### 6.2.3 Production Data

```python
# api/production.py

@app.get("/api/production", tags=["Production"])
async def get_production_data(
    commodity: str = Query(...),
    year: Optional[int] = None,
    province: Optional[str] = None,
    min_yield: Optional[float] = None
):
    """Get production data with filters"""

    commodity_data = supabase.from_("commodities") \
        .select("id") \
        .eq("name", commodity) \
        .single() \
        .execute()

    query = supabase.from_("production_data") \
        .select("*, commodities(name), data_sources(source_name)") \
        .eq("commodity_id", commodity_data.data['id']) \
        .order("year", desc=True)

    if year:
        query = query.eq("year", year)
    if province:
        query = query.eq("province", province)
    if min_yield:
        query = query.gte("yield_kg_per_hectare", min_yield)

    return query.execute().data

@app.get("/api/production/provinces", tags=["Production"])
async def get_top_provinces(
    commodity: str,
    year: int,
    sort_by: str = "production_tons",  # or "yield_kg_per_hectare"
    limit: int = 10
):
    """Get top producing provinces"""

    commodity_data = supabase.from_("commodities") \
        .select("id") \
        .eq("name", commodity) \
        .single() \
        .execute()

    result = supabase.from_("production_data") \
        .select("province, production_tons, area_hectares, yield_kg_per_hectare") \
        .eq("commodity_id", commodity_data.data['id']) \
        .eq("year", year) \
        .order(sort_by, desc=True) \
        .limit(limit) \
        .execute()

    return result.data
```

#### 6.2.4 AI Analyses

```python
# api/analyses.py

@app.get("/api/analyses", tags=["AI Analyses"])
async def get_perplexity_analyses(
    commodity: Optional[str] = None,
    query_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    limit: int = 20
):
    """Get Perplexity research analyses"""

    query = supabase.from_("perplexity_analyses") \
        .select("*") \
        .order("created_at", desc=True) \
        .limit(limit)

    if commodity:
        commodity_data = supabase.from_("commodities").select("id").eq("name", commodity).single().execute()
        query = query.eq("commodity_id", commodity_data.data['id'])

    if query_type:
        query = query.eq("query_type", query_type)

    if start_date:
        query = query.gte("created_at", start_date)

    return query.execute().data

@app.get("/api/analyses/{analysis_id}", tags=["AI Analyses"])
async def get_analysis_details(analysis_id: str):
    """Get detailed analysis with citations"""

    result = supabase.from_("perplexity_analyses") \
        .select("*") \
        .eq("id", analysis_id) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return result.data
```

#### 6.2.5 Reports

```python
# api/reports.py

@app.get("/api/reports", tags=["Reports"])
async def get_reports(
    commodity: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    published_only: bool = True,
    limit: int = 20
):
    """Get Claude-generated reports"""

    query = supabase.from_("claude_reports") \
        .select("id, title, executive_summary, report_type, sentiment, risk_level, created_at, published_at") \
        .order("created_at", desc=True) \
        .limit(limit)

    if published_only:
        query = query.not_.is_("published_at", "null")

    if commodity:
        commodity_data = supabase.from_("commodities").select("id").eq("name", commodity).single().execute()
        query = query.eq("commodity_id", commodity_data.data['id'])

    if report_type:
        query = query.eq("report_type", report_type)

    if start_date:
        query = query.gte("created_at", start_date)

    return query.execute().data

@app.get("/api/reports/{report_id}", tags=["Reports"])
async def get_report_full(report_id: str):
    """Get full report content"""

    result = supabase.from_("claude_reports") \
        .select("*") \
        .eq("id", report_id) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if published (unless using service_role_key)
    if not result.data['published_at']:
        raise HTTPException(status_code=403, detail="Report not published yet")

    return result.data

@app.get("/api/reports/latest/{report_type}", tags=["Reports"])
async def get_latest_report(
    report_type: str,  # daily or weekly
    commodity: str = Query(...)
):
    """Get most recent published report of specific type"""

    commodity_data = supabase.from_("commodities").select("id").eq("name", commodity).single().execute()

    result = supabase.from_("claude_reports") \
        .select("*") \
        .eq("commodity_id", commodity_data.data['id']) \
        .eq("report_type", report_type) \
        .not_.is_("published_at", "null") \
        .order("published_at", desc=True) \
        .limit(1) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail=f"No published {report_type} report found")

    return result.data[0]
```

#### 6.2.6 Semantic Search (ChromaDB)

```python
# api/search.py

from pydantic import BaseModel

class SemanticSearchRequest(BaseModel):
    query: str
    collection: str  # commodity_documents|perplexity_analyses|claude_reports|commodity_prices|production_data
    filters: Optional[dict] = {}
    n_results: int = 10

@app.post("/api/search", tags=["Semantic Search"])
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search across ChromaDB collections

    Example:
    {
        "query": "Why did cashew prices spike in June 2024?",
        "collection": "claude_reports",
        "filters": {"commodity": "cashew", "sentiment": "bullish"},
        "n_results": 5
    }
    """

    # Get ChromaDB collection
    collection = chromadb_client.get_collection(name=request.collection)

    # Perform semantic search
    results = collection.query(
        query_texts=[request.query],
        where=request.filters if request.filters else None,
        n_results=request.n_results
    )

    # Enrich with Supabase data if supabase_id exists
    if results['metadatas'][0] and 'supabase_id' in results['metadatas'][0][0]:
        supabase_ids = [m['supabase_id'] for m in results['metadatas'][0]]

        # Determine table based on collection
        table_map = {
            "commodity_documents": None,  # No Supabase mapping
            "perplexity_analyses": "perplexity_analyses",
            "claude_reports": "claude_reports",
            "commodity_prices": "prices",
            "production_data": "production_data"
        }

        table = table_map.get(request.collection)
        if table:
            supabase_data = supabase.from_(table) \
                .select("*") \
                .in_("id", supabase_ids) \
                .execute()

            return {
                "query": request.query,
                "results": results,
                "supabase_data": supabase_data.data
            }

    return {
        "query": request.query,
        "results": results
    }

@app.get("/api/search/similar-prices", tags=["Semantic Search"])
async def find_similar_price_scenarios(
    commodity: str,
    market_condition: str,  # e.g., "high demand supply shortage"
    n_results: int = 10
):
    """Find historical price scenarios similar to current market conditions"""

    collection = chromadb_client.get_collection(name="commodity_prices")

    results = collection.query(
        query_texts=[market_condition],
        where={"commodity": commodity},
        n_results=n_results
    )

    return results
```

#### 6.2.7 Geopolitical Events

```python
# api/events.py

@app.get("/api/events", tags=["Geopolitical Events"])
async def get_geopolitical_events(
    commodity: Optional[str] = None,
    impact_level: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[date] = None,
    countries: Optional[List[str]] = Query(None),
    limit: int = 50
):
    """Get geopolitical events affecting commodities"""

    query = supabase.from_("geopolitical_events") \
        .select("*") \
        .order("event_date", desc=True) \
        .limit(limit)

    if commodity:
        commodity_data = supabase.from_("commodities").select("id").eq("name", commodity).single().execute()
        query = query.eq("commodity_id", commodity_data.data['id'])

    if impact_level:
        query = query.eq("impact_level", impact_level)

    if event_type:
        query = query.eq("event_type", event_type)

    if start_date:
        query = query.gte("event_date", start_date)

    if countries:
        # PostgreSQL array overlap operator
        query = query.overlaps("countries_involved", countries)

    return query.execute().data

@app.get("/api/events/timeline", tags=["Geopolitical Events"])
async def get_events_timeline(
    commodity: str,
    start_date: date,
    end_date: date
):
    """Get chronological timeline of events for visualization"""

    commodity_data = supabase.from_("commodities").select("id").eq("name", commodity).single().execute()

    result = supabase.from_("geopolitical_events") \
        .select("event_date, title, impact_level, event_type, sentiment") \
        .eq("commodity_id", commodity_data.data['id']) \
        .gte("event_date", start_date) \
        .lte("event_date", end_date) \
        .order("event_date", desc=False) \
        .execute()

    return result.data
```

### 6.3 Webhook Endpoints (Future Railway.app Integration)

```python
# api/webhooks.py

@app.post("/api/webhooks/trigger-analysis", tags=["Webhooks"])
async def trigger_manual_analysis(
    commodity: str,
    query_type: str,
    background_tasks: BackgroundTasks
):
    """Manually trigger Perplexity analysis (webhook from Railway.app cron)"""

    background_tasks.add_task(run_perplexity_analysis, commodity, query_type)

    return {"status": "triggered", "commodity": commodity, "query_type": query_type}

@app.post("/api/webhooks/generate-report", tags=["Webhooks"])
async def trigger_report_generation(
    commodity: str,
    report_type: str,
    background_tasks: BackgroundTasks
):
    """Manually trigger Claude report generation"""

    background_tasks.add_task(generate_claude_report, commodity, report_type)

    return {"status": "triggered", "commodity": commodity, "report_type": report_type}
```

---

## 7. DATA FLOW ARCHITECTURE

### 7.1 Complete Data Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     STAGE 1: DATA COLLECTION                             │
│                     (Daily 6:00 AM via APScheduler)                      │
└──────────────────────────────────────────────────────────────────────────┘

[ODC Website] ──┐
[MEF API]      ─┤
[WITS API]     ─┼──► [Fetch MCP] ──► [Collectors] ──► [Validation]
[Google Drive] ─┘                         │
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ Data Normalization     │
                              │ • Currency conversion  │
                              │ • Unit standardization │
                              │ • Quality checks       │
                              └────────┬───────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │                                             │
                 ▼                                             ▼
    ┌────────────────────────┐                   ┌────────────────────────┐
    │   SUPABASE INSERT      │                   │   CHROMADB ADD         │
    │   (Structured Data)    │                   │   (Semantic Embedding) │
    │                        │                   │                        │
    │   • prices             │                   │   • commodity_prices   │
    │   • production_data    │                   │   • production_data    │
    │   • data_sources       │                   │   • commodity_docs     │
    └────────────────────────┘                   └────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                  STAGE 2: AI RESEARCH (Perplexity)                       │
│                     (Daily 6:15 AM via APScheduler)                      │
└──────────────────────────────────────────────────────────────────────────┘

[Scheduled Queries] ──► [Redis Cache Check] ──► Cache Hit? ──► Use Cached
                              │                       │
                              │                       └──► Cache Miss
                              ▼                            │
                   [Perplexity API Call]◄─────────────────┘
                              │
                              ├──► [Store in Redis] (TTL: 24h)
                              │
                              ├──► [Supabase: perplexity_analyses]
                              │
                              └──► [ChromaDB: perplexity_analyses]

┌──────────────────────────────────────────────────────────────────────────┐
│              STAGE 3: CONTEXT RETRIEVAL (ChromaDB)                       │
│                     (Daily 6:25 AM via APScheduler)                      │
└──────────────────────────────────────────────────────────────────────────┘

[Prepare Claude Context]
         │
         ├──► Query ChromaDB Collections:
         │    • perplexity_analyses (last 7 days)
         │    • claude_reports (similar market conditions)
         │    • commodity_prices (historical patterns)
         │    • production_data (current season)
         │
         └──► [Aggregate Context] ──► [Context7 MCP] (long-term memory)

┌──────────────────────────────────────────────────────────────────────────┐
│               STAGE 4: REPORT GENERATION (Claude)                        │
│                     (Daily 6:30 AM via APScheduler)                      │
└──────────────────────────────────────────────────────────────────────────┘

[Claude API MOCK]
         │
         ├──► Input:
         │    • Supabase data (prices, production, events)
         │    • ChromaDB context (semantic search results)
         │    • Context7 (long-term patterns)
         │
         ├──► Process:
         │    • Generate daily report
         │    • Extract insights
         │    • Assign sentiment/risk level
         │
         └──► Output:
              ├──► [Supabase: claude_reports]
              └──► [ChromaDB: claude_reports]

┌──────────────────────────────────────────────────────────────────────────┐
│                 STAGE 5: DASHBOARD PRESENTATION                          │
│                     (Real-time via Streamlit)                            │
└──────────────────────────────────────────────────────────────────────────┘

[Streamlit Frontend]
         │
         ├──► [FastAPI Endpoints]
         │    ├──► /api/prices (Supabase)
         │    ├──► /api/reports (Supabase)
         │    └──► /api/search (ChromaDB)
         │
         └──► [Display]
              ├── Price Charts (Plotly)
              ├── AI Reports (Markdown)
              ├── Semantic Search Widget
              └── Geopolitical Timeline
```

### 7.2 Error Handling & Retry Logic

```python
# services/collectors/base_collector.py

from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class BaseCollector:
    """Base class for all data collectors"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def collect(self):
        """Collect data with retry logic"""
        try:
            # 1. Fetch data
            data = await self.fetch_data()

            # 2. Validate
            validated_data = await self.validate(data)

            # 3. Normalize
            normalized_data = await self.normalize(validated_data)

            # 4. Store (dual-write)
            await self.store_supabase(normalized_data)
            await self.store_chromadb(normalized_data)

            # 5. Update source status
            await self.update_source_status(success=True)

            return normalized_data

        except Exception as e:
            logger.error(f"Collection failed: {e}")
            await self.update_source_status(success=False, error=str(e))
            raise

    async def store_supabase(self, data):
        """Override in subclass"""
        raise NotImplementedError

    async def store_chromadb(self, data):
        """Override in subclass"""
        raise NotImplementedError
```

---

## 8. CACHING STRATEGY

### 8.1 Multi-Layer Caching Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                       CACHING LAYERS                                  │
└───────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1: REDIS CACHE (Hot Data - TTL: Hours)                       │
├─────────────────────────────────────────────────────────────────────┤
│ Purpose: Perplexity API response caching                           │
│ Key Pattern: perplexity:{commodity}:{query_hash}                   │
│ TTL: 24 hours (daily queries), 7 days (weekly)                     │
│                                                                     │
│ Example:                                                            │
│   Key: perplexity:cashew:sha256(query_text)                        │
│   Value: {response_text, citations, timestamp}                     │
│   Hit Rate Target: >70%                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 2: CHROMADB SEMANTIC CACHE (Warm Data - Permanent)           │
├─────────────────────────────────────────────────────────────────────┤
│ Purpose: Similar query detection (e.g., "Vietnam demand" ~         │
│          "Vietnamese cashew market")                                │
│ Mechanism: Vector similarity search (cosine distance < 0.1)        │
│ Collections: perplexity_analyses, claude_reports                   │
│                                                                     │
│ Example:                                                            │
│   Query: "Cambodia cashew export trends 2024"                      │
│   Similar: "Cashew export patterns Cambodia" (85% similarity)      │
│   Action: Return cached analysis instead of new Perplexity call    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 3: CONTEXT7 MCP (Cold Data - Long-term Memory)               │
├─────────────────────────────────────────────────────────────────────┤
│ Purpose: Store long-term patterns, seasonal trends                 │
│ Storage: Upstash Redis (persistent)                                │
│ Use Case: "In Q2 2023, similar conditions led to..."               │
│                                                                     │
│ Example:                                                            │
│   Context: monsoon_delay_impact_cashew_prices                      │
│   Data: {year: 2023, price_drop: 15%, recovery_days: 45}          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 4: SUPABASE MATERIALIZED VIEWS (Query Optimization)          │
├─────────────────────────────────────────────────────────────────────┤
│ Purpose: Pre-aggregated dashboard queries                          │
│ Views: latest_prices, monthly_production_summary                   │
│ Refresh: Daily at 7:00 AM (after data collection)                  │
│                                                                     │
│ Example:                                                            │
│   View: latest_prices                                               │
│   Refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY latest_prices;   │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Redis Cache Implementation

```python
# services/cache/redis_cache.py

import redis.asyncio as redis
import hashlib
import json
from datetime import timedelta

class RedisCache:
    def __init__(self):
        self.redis = redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )

    async def get_perplexity_cache(self, commodity: str, query_text: str):
        """Check if Perplexity query was cached"""
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()
        key = f"perplexity:{commodity}:{query_hash}"

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_perplexity_cache(
        self,
        commodity: str,
        query_text: str,
        response_data: dict,
        ttl_hours: int = 24
    ):
        """Cache Perplexity response"""
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()
        key = f"perplexity:{commodity}:{query_hash}"

        await self.redis.setex(
            key,
            timedelta(hours=ttl_hours),
            json.dumps(response_data)
        )

    async def get_price_cache(self, commodity: str, filters: dict):
        """Cache expensive price queries"""
        filter_hash = hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()
        key = f"prices:{commodity}:{filter_hash}"

        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern (e.g., 'prices:cashew:*')"""
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
```

### 8.3 ChromaDB Semantic Cache

```python
# services/cache/semantic_cache.py

class SemanticCache:
    """Use ChromaDB to avoid redundant Perplexity calls"""

    async def find_similar_analysis(
        self,
        query_text: str,
        commodity: str,
        similarity_threshold: float = 0.85
    ):
        """Find cached analysis similar to current query"""

        collection = chromadb_client.get_collection("perplexity_analyses")

        results = collection.query(
            query_texts=[query_text],
            where={"commodity": commodity},
            n_results=1
        )

        if results['distances'][0] and results['distances'][0][0] < (1 - similarity_threshold):
            # Found similar cached analysis
            cached_metadata = results['metadatas'][0][0]

            # Check if cache is still valid (< 7 days old)
            created_at = datetime.fromisoformat(cached_metadata['query_date'])
            if (datetime.utcnow() - created_at).days < 7:
                return {
                    "cached": True,
                    "supabase_id": cached_metadata['supabase_id'],
                    "similarity": 1 - results['distances'][0][0]
                }

        return {"cached": False}
```

### 8.4 Caching Metrics & Monitoring

```python
# services/monitoring/cache_metrics.py

class CacheMetrics:
    """Track cache performance"""

    async def log_cache_hit(self, layer: str, key: str):
        """Record cache hit"""
        await redis_client.hincrby("cache_hits", layer, 1)

    async def log_cache_miss(self, layer: str, key: str):
        """Record cache miss"""
        await redis_client.hincrby("cache_misses", layer, 1)

    async def get_hit_rate(self, layer: str) -> float:
        """Calculate cache hit rate"""
        hits = int(await redis_client.hget("cache_hits", layer) or 0)
        misses = int(await redis_client.hget("cache_misses", layer) or 0)

        if hits + misses == 0:
            return 0.0

        return hits / (hits + misses)

    async def get_cost_savings(self) -> dict:
        """Calculate $ saved from caching Perplexity calls"""
        perplexity_hits = int(await redis_client.hget("cache_hits", "perplexity") or 0)
        cost_per_query = 0.005  # $0.005 per Perplexity query (estimate)

        return {
            "queries_saved": perplexity_hits,
            "cost_saved_usd": perplexity_hits * cost_per_query,
            "hit_rate": await self.get_hit_rate("perplexity")
        }
```

---

## 9. MCP INTEGRATION POINTS

### 9.1 MCP Configuration

```json
// .claude/mcp.json (Claude Desktop)
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "description": "HTTP requests for MEF, WITS APIs"
    },
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase@latest",
        "--project-ref=xqfozbocgyrelznccweh"
      ],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}"
      },
      "description": "Direct Supabase queries"
    },
    "browsermcp": {
      "command": "npx",
      "args": ["@browsermcp/mcp@latest"],
      "description": "ODC website scraping"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "description": "Long-term context storage"
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"],
      "description": "E2E testing for Streamlit"
    },
    "chroma": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-chroma"],
      "env": {
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8000"
      },
      "description": "Semantic search & embeddings"
    }
  }
}
```

### 9.2 MCP Usage Map

| MCP | Primary Use Case | Integration Point | Frequency |
|-----|------------------|-------------------|-----------|
| **fetch** | API calls (MEF, WITS) | Data collectors | Daily 6:00 AM |
| **browsermcp** | ODC scraping | ODC collector | Weekly Monday 6:00 AM |
| **supabase** | Direct DB queries | Dashboard, debugging | On-demand |
| **chroma** | Semantic search | API `/api/search`, Claude context | Real-time |
| **context7** | Long-term memory | Claude report generation | Daily 6:30 AM |
| **playwright** | E2E tests | CI/CD pipeline | On git push |

### 9.3 MCP Integration Code Examples

#### 9.3.1 Fetch MCP (Data Collection)

```python
# services/collectors/mef_collector.py

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def collect_mef_data():
    """Use Fetch MCP to call MEF API"""

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize MCP
            await session.initialize()

            # Call MEF API via Fetch MCP
            result = await session.call_tool(
                "fetch",
                {
                    "url": "https://data.mef.gov.kh/api/v1/public-datasets/pd_68b588a0eb43bd000745b588/json?page=1&page_size=100",
                    "method": "GET"
                }
            )

            # Parse response
            data = json.loads(result.content[0].text)

            return data
```

#### 9.3.2 ChromaDB MCP (Semantic Search)

```python
# api/search.py (using MCP instead of Python client)

async def semantic_search_via_mcp(query: str, collection: str, filters: dict):
    """Use ChromaDB MCP for semantic search"""

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-chroma"],
        env={
            "CHROMA_HOST": "localhost",
            "CHROMA_PORT": "8000"
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Query ChromaDB via MCP
            result = await session.call_tool(
                "query_collection",
                {
                    "collection_name": collection,
                    "query_texts": [query],
                    "where": filters,
                    "n_results": 10
                }
            )

            return json.loads(result.content[0].text)
```

#### 9.3.3 Context7 MCP (Long-term Memory)

```python
# services/ai/context7_service.py

async def store_long_term_pattern(pattern_name: str, pattern_data: dict):
    """Store recurring patterns in Context7"""

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@upstash/context7-mcp"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Store pattern
            await session.call_tool(
                "store_context",
                {
                    "key": f"pattern:{pattern_name}",
                    "value": json.dumps(pattern_data),
                    "ttl": 31536000  # 1 year
                }
            )

async def retrieve_long_term_pattern(pattern_name: str):
    """Retrieve historical pattern for Claude context"""

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@upstash/context7-mcp"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Retrieve pattern
            result = await session.call_tool(
                "get_context",
                {"key": f"pattern:{pattern_name}"}
            )

            return json.loads(result.content[0].text)
```

---

## 10. SCHEDULING ARCHITECTURE

### 10.1 APScheduler Configuration

```python
# services/scheduler/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

logger = logging.getLogger(__name__)

# Job store (persist schedules in Supabase)
jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql://supabase_connection_string')
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    timezone='Asia/Phnom_Penh'  # GMT+7
)

# ============================================================================
# DAILY JOBS (6:00 AM Cambodia Time)
# ============================================================================

@scheduler.scheduled_job(CronTrigger(hour=6, minute=0), id='daily_data_collection')
async def daily_data_collection():
    """Collect data from all sources"""
    logger.info("Starting daily data collection...")

    try:
        # Parallel collection
        tasks = [
            collect_odc_data(),
            collect_mef_data(),
            collect_wits_data()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Collector {i} failed: {result}")
            else:
                logger.info(f"Collector {i} success: {len(result)} records")

        # Refresh materialized views
        await refresh_materialized_views()

        logger.info("Daily data collection complete")

    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        await send_alert("Data collection failed", str(e))

@scheduler.scheduled_job(CronTrigger(hour=6, minute=15), id='daily_perplexity_analysis')
async def daily_perplexity_analysis():
    """Run Perplexity research queries"""
    logger.info("Starting Perplexity analysis...")

    queries = {
        'cashew': [
            "Cambodia cashew nut export prices last 24 hours",
            "Vietnam cashew processing capacity 2024",
            "US-China trade tensions impact cashew market",
            "Cashew demand China December 2024"
        ],
        'rubber': [
            "Cambodia rubber prices latest",
            "Global natural rubber demand trends",
            "Malaysia rubber processing news"
        ]
    }

    for commodity, query_list in queries.items():
        for query_text in query_list:
            try:
                # Check semantic cache first
                cached = await semantic_cache.find_similar_analysis(query_text, commodity)

                if cached['cached']:
                    logger.info(f"Cache hit for: {query_text}")
                    continue

                # Call Perplexity API
                result = await perplexity_service.research(commodity, query_text)

                # Store in Supabase + ChromaDB + Redis
                await store_perplexity_analysis(result)

                # Rate limiting
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Perplexity query failed: {e}")

@scheduler.scheduled_job(CronTrigger(hour=6, minute=30), id='daily_claude_report')
async def daily_claude_report():
    """Generate daily report with Claude"""
    logger.info("Generating daily Claude report...")

    for commodity in ['cashew', 'rubber']:
        try:
            # Gather context from ChromaDB
            context = await gather_claude_context(commodity, report_type='daily')

            # Generate report (MOCK for now)
            report = await claude_service.generate_daily_report(commodity, context)

            # Store report
            await store_claude_report(report)

            logger.info(f"Daily report for {commodity} generated")

        except Exception as e:
            logger.error(f"Report generation failed for {commodity}: {e}")

# ============================================================================
# WEEKLY JOBS (Monday 6:00 AM Cambodia Time)
# ============================================================================

@scheduler.scheduled_job(CronTrigger(day_of_week='mon', hour=6, minute=0), id='weekly_comprehensive_report')
async def weekly_comprehensive_report():
    """Generate comprehensive weekly report"""
    logger.info("Generating weekly comprehensive report...")

    for commodity in ['cashew', 'rubber']:
        try:
            # Gather 7 days of context
            context = await gather_claude_context(commodity, report_type='weekly')

            # Generate long-form report
            report = await claude_service.generate_weekly_report(commodity, context)

            # Store report
            await store_claude_report(report)

            # Optional: Send email to stakeholders
            # await send_email_report(report)

            logger.info(f"Weekly report for {commodity} generated")

        except Exception as e:
            logger.error(f"Weekly report failed for {commodity}: {e}")

@scheduler.scheduled_job(CronTrigger(day_of_week='mon', hour=6, minute=30), id='weekly_google_drive_sync')
async def weekly_google_drive_sync():
    """Sync Google Drive PDFs/KML (weekly to avoid rate limits)"""
    logger.info("Starting Google Drive sync...")

    try:
        new_files = await google_drive_parser.sync()

        for file in new_files:
            # OCR if PDF
            if file['type'] == 'pdf':
                text = await ocr_service.extract_text(file['content'])
                await store_in_chromadb(text, file['metadata'])

            # Parse if KML
            elif file['type'] == 'kml':
                geojson = await kml_parser.parse(file['content'])
                await store_geospatial_data(geojson)

        logger.info(f"Google Drive sync complete: {len(new_files)} new files")

    except Exception as e:
        logger.error(f"Google Drive sync failed: {e}")

# ============================================================================
# MAINTENANCE JOBS
# ============================================================================

@scheduler.scheduled_job(CronTrigger(hour=7, minute=0), id='refresh_materialized_views')
async def refresh_materialized_views():
    """Refresh Supabase materialized views"""
    logger.info("Refreshing materialized views...")

    await supabase.rpc("refresh_materialized_view", {"view_name": "latest_prices"}).execute()

@scheduler.scheduled_job(CronTrigger(hour=2, minute=0), id='cache_cleanup')
async def cache_cleanup():
    """Clean expired cache entries"""
    logger.info("Cleaning expired cache...")

    # Redis TTL handles this automatically, but clean up metrics
    await redis_client.delete("cache_hits")
    await redis_client.delete("cache_misses")

# ============================================================================
# START SCHEDULER
# ============================================================================

def start_scheduler():
    """Start APScheduler"""
    scheduler.start()
    logger.info("Scheduler started - Jobs configured:")
    scheduler.print_jobs()
```

### 10.2 Railway.app Cron Integration

```yaml
# railway.json (Railway.app config)
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  },
  "cron": [
    {
      "schedule": "0 6 * * *",
      "command": "python -m services.scheduler.jobs.daily_data_collection",
      "timezone": "Asia/Phnom_Penh"
    },
    {
      "schedule": "0 6 * * 1",
      "command": "python -m services.scheduler.jobs.weekly_report",
      "timezone": "Asia/Phnom_Penh"
    }
  ],
  "healthcheckPath": "/api/health",
  "healthcheckTimeout": 30
}
```

---

## 11. SECURITY & AUTHENTICATION

### 11.1 Environment Variables

```bash
# .env.production

# Supabase
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...  # Public key for frontend
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Backend only - NEVER expose

# Perplexity
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Claude (MOCK - no real key)
ANTHROPIC_API_KEY=placeholder_mock_key

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Google Drive
GOOGLE_DOCS_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk

# App Config
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://your-streamlit-app.railway.app
```

### 11.2 Supabase RLS Policies (Multi-Tenancy Ready)

```sql
-- Example: Restrict draft reports to service_role only

CREATE POLICY "Service role full access" ON claude_reports
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Public read published reports only" ON claude_reports
FOR SELECT
TO anon
USING (published_at IS NOT NULL);

-- Example: User-based access (future)
-- Assumes `user_id` column added to tables

CREATE POLICY "Users see their organization's data" ON prices
FOR SELECT
TO authenticated
USING (
  organization_id IN (
    SELECT organization_id FROM user_organizations
    WHERE user_id = auth.uid()
  )
);
```

### 11.3 API Rate Limiting

```python
# middleware/rate_limit.py

from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/search")
@limiter.limit("10/minute")  # 10 semantic searches per minute
async def semantic_search(request: Request, ...):
    ...

@app.get("/api/prices")
@limiter.limit("100/minute")  # 100 price queries per minute
async def get_prices(request: Request, ...):
    ...
```

---

## 12. DEPLOYMENT ARCHITECTURE

### 12.1 Railway.app Deployment

```
┌────────────────────────────────────────────────────────────────┐
│                     RAILWAY.APP SERVICES                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐       ┌──────────────────┐             │
│  │  FastAPI Backend │       │ Streamlit Frontend│             │
│  │  Port: 8000      │◄──────┤  Port: 8501      │             │
│  └────────┬─────────┘       └──────────────────┘             │
│           │                                                    │
│           ├──► [Supabase PostgreSQL] (External)               │
│           ├──► [ChromaDB Container] (Internal - Port 8000)    │
│           └──► [Redis Container] (Internal - Port 6379)       │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  APScheduler (Embedded in FastAPI)                       │ │
│  │  • Daily Jobs (6:00 AM Cambodia Time)                    │ │
│  │  • Weekly Jobs (Monday 6:00 AM)                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘

External Services:
• Supabase: https://xqfozbocgyrelznccweh.supabase.co
• Perplexity API: https://api.perplexity.ai
• Claude API: MOCK (placeholder)
```

### 12.2 Docker Compose (Local Development)

```yaml
# docker-compose.yml

version: '3.8'

services:
  fastapi:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env.local
    depends_on:
      - redis
      - chromadb
    volumes:
      - ./backend:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  streamlit:
    build: ./dashboard
    ports:
      - "8501:8501"
    env_file:
      - .env.local
    depends_on:
      - fastapi
    volumes:
      - ./dashboard:/app
    command: streamlit run app.py --server.port 8501

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"  # Avoid conflict with FastAPI
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE

volumes:
  redis_data:
  chroma_data:
```

### 12.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml

name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run tests
        run: pytest tests/ -v

      - name: Run E2E tests (Playwright)
        run: |
          npx playwright install
          pytest tests/e2e/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        uses: railway/deploy-action@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: cambodia-agri-analytics
```

---

## 13. MONITORING & OBSERVABILITY

### 13.1 Logging Strategy

```python
# utils/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
import json

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for Railway.app"""

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        RotatingFileHandler("logs/app.log", maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()  # Railway.app captures stdout
    ]
)

logger = logging.getLogger("cambodia_agri_analytics")
logger.handlers[0].setFormatter(JSONFormatter())
```

### 13.2 Health Check Endpoint

```python
# api/health.py

@app.get("/api/health")
async def health_check():
    """Comprehensive health check for Railway.app"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check Supabase
    try:
        await supabase.from_("commodities").select("id").limit(1).execute()
        health_status["services"]["supabase"] = "healthy"
    except Exception as e:
        health_status["services"]["supabase"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check ChromaDB
    try:
        chromadb_client.heartbeat()
        health_status["services"]["chromadb"] = "healthy"
    except Exception as e:
        health_status["services"]["chromadb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check scheduler
    health_status["services"]["scheduler"] = "healthy" if scheduler.running else "stopped"

    return health_status
```

### 13.3 Metrics Dashboard

```python
# api/metrics.py

@app.get("/api/metrics")
async def get_metrics():
    """System metrics for monitoring"""

    return {
        "database": {
            "total_prices": await count_records("prices"),
            "total_reports": await count_records("claude_reports"),
            "total_analyses": await count_records("perplexity_analyses")
        },
        "cache": {
            "perplexity_hit_rate": await cache_metrics.get_hit_rate("perplexity"),
            "redis_memory_usage": await redis_client.info("memory"),
            "cost_savings": await cache_metrics.get_cost_savings()
        },
        "ai_usage": {
            "perplexity_calls_today": await count_ai_calls("perplexity", today()),
            "claude_tokens_used_today": await sum_tokens_used("claude", today()),
            "total_ai_cost_usd_today": await calculate_daily_ai_cost()
        },
        "scheduler": {
            "next_jobs": scheduler.get_jobs()[:5],
            "last_run_status": await get_last_job_status()
        }
    }
```

---

## 14. SCALABILITY CONSIDERATIONS

### 14.1 Current Architecture Limits

| Component | Current Limit | Scale-Up Strategy |
|-----------|---------------|-------------------|
| **Supabase** | 500MB (free tier) | Upgrade to Pro ($25/mo) = 8GB |
| **ChromaDB** | 1M vectors (single node) | Multi-node cluster or Pinecone migration |
| **Redis** | 25MB (Railway free) | Upstash Redis (persistent, serverless) |
| **Perplexity** | $20/mo budget | Semantic caching (70% hit rate target) |
| **Railway.app** | 500h/mo (Hobby) | Pro plan $20/mo = always-on |

### 14.2 Optimization Roadmap

**Phase 1 (Weeks 1-4)**: MVP
- Single commodity (cashew)
- Basic caching (Redis)
- Daily reports only

**Phase 2 (Months 2-3)**: Scale to Multi-Commodity
- Add rubber
- Implement ChromaDB semantic cache
- Weekly reports

**Phase 3 (Months 4-6)**: Performance Optimization
- Supabase table partitioning (by date)
- ChromaDB query optimization
- Context7 long-term patterns

**Phase 4 (Months 7-12)**: Multi-Tenancy
- User authentication (Supabase Auth)
- Organization-based RLS policies
- Custom report scheduling

---

## CONCLUSION

This architecture provides a **production-ready**, **scalable**, and **cost-efficient** foundation for the Cambodia Agri Analytics platform with:

1. **Dual Storage**: Supabase (structured) + ChromaDB (semantic)
2. **AI Pipeline**: Perplexity → Context7 → Claude with intelligent caching
3. **MCP Integration**: 6 MCPs for seamless Claude Code development
4. **Automation**: APScheduler for daily/weekly jobs
5. **Deployment**: Railway.app with Docker containerization

**Estimated Monthly Costs**:
- Supabase: $0 (free tier initially)
- Railway.app: $20 (Pro plan)
- Perplexity: $20 (with 70% cache savings)
- Redis/ChromaDB: $0 (self-hosted)
- **Total**: ~$40/month

**Next Steps**:
1. Initialize Supabase schema (run SQL script)
2. Set up ChromaDB collections (Python init script)
3. Implement first collector (MEF API)
4. Test Perplexity + Claude pipeline
5. Build Streamlit MVP dashboard

---

**Document Status**: ✅ Complete
**Ready for**: Implementation Phase
