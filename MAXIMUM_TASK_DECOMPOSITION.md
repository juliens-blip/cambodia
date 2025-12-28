# MAXIMUM TASK DECOMPOSITION - CAMBODIA AGRI ANALYTICS
## ChromaDB Integration + 100+ Atomic Tasks

**Generated**: 2025-12-24
**Project**: Multi-commodity Analytics Platform (Cashew + Rubber)
**Target**: As fast as possible with MAXIMUM PARALLELIZATION
**Special**: NO Anthropic API key (use placeholder/mock system)

---

## EXECUTIVE SUMMARY

### ChromaDB Strategic Role
ChromaDB serves as the **semantic intelligence layer** for the platform:
- **Document Storage**: All PDFs from Google Drive (Khmer cashew/rubber reports)
- **Semantic Search**: Natural language queries over commodity data
- **Analysis Archive**: Searchable Perplexity + Claude report history
- **Knowledge Base**: Build queryable knowledge graph of commodity insights

### Project Metrics
- **Total Tasks**: 127 atomic tasks
- **Parallel Tracks**: 8 concurrent execution streams
- **Critical Path**: 23 days (optimized)
- **Agents Used**: 14 specialized agents
- **MCP Servers**: 5 (including ChromaDB)

---

## PART 1: CHROMADB INTEGRATION STRATEGY

### 1.1 ChromaDB Collections Architecture

#### Collection 1: `commodity_documents`
**Purpose**: Store and search all PDF/KML documents from Google Drive

```python
# Collection Schema
{
  "name": "commodity_documents",
  "metadata": {
    "description": "Searchable repository of Cambodia agri PDFs/KML",
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}

# Document Structure
{
  "id": "doc_{uuid}",
  "document": "Chunked text from PDF OCR or KML metadata",
  "metadata": {
    "commodity_type": "cashew|rubber",
    "source_file": "cashew_production_2024.pdf",
    "file_url": "gdrive://...",
    "language": "khmer|english",
    "page_number": 3,
    "province": "Kampong Cham",
    "year": 2024,
    "data_type": "production|price|geospatial",
    "confidence_score": 0.92,  # OCR quality
    "created_at": "2025-12-24T10:30:00Z"
  }
}

# Query Patterns
- "Find cashew production data for Kampong Cham province 2024"
- "What are rubber price trends in Cambodia?"
- "Show all geospatial KML data for cashew farms"
```

**Queries**:
```python
# Semantic search
chroma_client.query(
    collection_name="commodity_documents",
    query_texts=["cashew nut production statistics Kampong Cham"],
    n_results=10,
    where={"commodity_type": "cashew", "year": 2024}
)

# Filter by metadata
chroma_client.query(
    collection_name="commodity_documents",
    query_texts=["rubber export data"],
    where={"$and": [
        {"commodity_type": "rubber"},
        {"data_type": "price"},
        {"language": "english"}
    ]}
)
```

---

#### Collection 2: `perplexity_analyses`
**Purpose**: Archive and retrieve Perplexity research results with semantic search

```python
{
  "name": "perplexity_analyses",
  "metadata": {
    "description": "Searchable archive of Perplexity AI research",
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
  }
}

# Document Structure
{
  "id": "pplx_{uuid}",
  "document": "Full Perplexity response text + citations",
  "metadata": {
    "query_type": "daily_price|geopolitics|market_trend|competitor",
    "commodity": "cashew|rubber",
    "query_text": "Cambodia cashew export prices last 24h",
    "citations_count": 5,
    "sources": ["Reuters", "Vietnam News", "ODC"],
    "query_date": "2025-12-24",
    "relevance_score": 0.87,
    "cost_usd": 0.02,
    "tokens_used": 1500,
    "created_at": "2025-12-24T06:15:00Z"
  }
}

# Query Patterns
- "Find Perplexity analyses about Vietnam cashew processing"
- "What did we learn about US-China trade tensions last week?"
- "Show all geopolitical events affecting rubber prices"
```

**Queries**:
```python
# Find similar past analyses
chroma_client.query(
    collection_name="perplexity_analyses",
    query_texts=["US tariffs impact on Cambodia cashew exports"],
    n_results=5,
    where={"query_type": "geopolitics", "commodity": "cashew"}
)

# Time-range queries
chroma_client.query(
    collection_name="perplexity_analyses",
    query_texts=["price trends"],
    where={
        "$and": [
            {"query_date": {"$gte": "2025-12-01"}},
            {"query_date": {"$lte": "2025-12-24"}}
        ]
    }
)
```

---

#### Collection 3: `claude_reports`
**Purpose**: Store and search generated Claude reports for historical context

```python
{
  "name": "claude_reports",
  "metadata": {
    "description": "Archive of AI-generated market reports",
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
  }
}

# Document Structure
{
  "id": "claude_{uuid}",
  "document": "Full report markdown content",
  "metadata": {
    "report_type": "daily|weekly|crisis",
    "commodity": "cashew|rubber|multi",
    "title": "Daily Cashew Market Report - Dec 24 2025",
    "sections": ["summary", "price_analysis", "geopolitics", "recommendations"],
    "insights_count": 7,
    "recommendations_count": 3,
    "data_sources_used": ["MEF", "WITS", "Perplexity"],
    "word_count": 850,
    "published_at": "2025-12-24T07:00:00Z",
    "mock_mode": true,  # Flag for no real Anthropic API
    "created_at": "2025-12-24T06:45:00Z"
  }
}

# Query Patterns
- "Find weekly reports mentioning price crashes"
- "What recommendations did we make for traders in December?"
- "Show reports covering both cashew and rubber"
```

**Queries**:
```python
# Semantic search across reports
chroma_client.query(
    collection_name="claude_reports",
    query_texts=["price crash recommendations for exporters"],
    n_results=3,
    where={"report_type": "weekly"}
)

# Find related reports
chroma_client.query(
    collection_name="claude_reports",
    query_texts=["Vietnam processing capacity expansion"],
    n_results=5
)
```

---

#### Collection 4: `commodity_prices`
**Purpose**: Structured price data with semantic search capabilities

```python
{
  "name": "commodity_prices",
  "metadata": {
    "description": "Timestamped commodity price data with context",
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
  }
}

# Document Structure
{
  "id": "price_{uuid}",
  "document": "Contextual description: W320 cashew price $2450/ton on 2025-12-24,
               Vietnam destination, up 5% from previous week due to strong Chinese demand",
  "metadata": {
    "commodity": "cashew",
    "date": "2025-12-24",
    "price_usd_per_ton": 2450.00,
    "quality_grade": "W320",
    "destination": "Vietnam",
    "volume_tons": 1240,
    "source": "MEF|WITS|ODC|manual",
    "weekly_change_percent": 5.0,
    "monthly_change_percent": 12.5,
    "year_over_year_percent": -3.2,
    "volatility_score": 0.45,
    "created_at": "2025-12-24T10:00:00Z"
  }
}

# Query Patterns
- "Find cashew prices above $2400 to Vietnam in December"
- "Show price drops greater than 10% in last month"
- "What caused rubber price spikes in 2024?"
```

**Queries**:
```python
# Price range + semantic context
chroma_client.query(
    collection_name="commodity_prices",
    query_texts=["significant price increase Vietnam exports"],
    where={
        "$and": [
            {"price_usd_per_ton": {"$gte": 2400}},
            {"destination": "Vietnam"}
        ]
    }
)

# Anomaly detection via embeddings
chroma_client.query(
    collection_name="commodity_prices",
    query_texts=["unusual price volatility"],
    n_results=10,
    where={"volatility_score": {"$gte": 0.8}}
)
```

---

#### Collection 5: `production_data`
**Purpose**: Geospatial production data with semantic search

```python
{
  "name": "production_data",
  "metadata": {
    "description": "Agricultural production stats with geolocation",
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
  }
}

# Document Structure
{
  "id": "prod_{uuid}",
  "document": "Kampong Cham province produced 15,200 tons of cashew in 2024
               across 8,500 hectares with yield of 1.79 tons/hectare",
  "metadata": {
    "commodity": "cashew|rubber",
    "year": 2024,
    "province": "Kampong Cham",
    "production_tons": 15200.0,
    "area_hectares": 8500.0,
    "yield_per_hectare": 1.79,
    "geolocation": {
      "type": "Point",
      "coordinates": [105.4583, 12.0000]  # Long, Lat
    },
    "source": "ODC|KML|MEF",
    "confidence": "high|medium|low",
    "created_at": "2025-12-24T10:00:00Z"
  }
}

# Query Patterns
- "Which provinces have highest cashew yield?"
- "Show rubber production near Vietnam border"
- "Find low-yield areas needing support"
```

**Queries**:
```python
# Geospatial + semantic
chroma_client.query(
    collection_name="production_data",
    query_texts=["high yield cashew production provinces"],
    n_results=10,
    where={
        "$and": [
            {"commodity": "cashew"},
            {"yield_per_hectare": {"$gte": 1.5}}
        ]
    }
)

# Year-over-year comparison
chroma_client.query(
    collection_name="production_data",
    query_texts=["production increase 2024 vs 2023"],
    where={"year": {"$in": [2023, 2024]}}
)
```

---

### 1.2 ChromaDB Workflow Integration

#### Workflow 1: Document Ingestion Pipeline
```python
# Task Chain: Google Drive → OCR → ChromaDB
1. GDrive Collector fetches PDF/KML files
2. OCR Service (Tesseract) extracts Khmer text
3. Text Chunker splits into 1000-char chunks (200 overlap)
4. Metadata Extractor identifies province, year, commodity
5. ChromaDB Uploader creates embeddings + stores
6. Index Builder creates searchable metadata indexes

# Parallel execution: 4 commodities × 2 file types = 8 streams
```

#### Workflow 2: Daily Analysis Pipeline
```python
# Task Chain: Data Collection → Perplexity → ChromaDB → Claude (Mock)
1. Data Collectors fetch prices (MEF, WITS, ODC)
2. Supabase Writer stores raw data
3. Perplexity Service queries latest trends
4. ChromaDB Writer stores Perplexity results
5. ChromaDB Query retrieves similar past analyses
6. Claude Mock Service generates report using context
7. ChromaDB Writer stores Claude report
8. Dashboard Refresh triggers real-time update

# Execution: Sequential with parallel collectors (3 streams)
```

#### Workflow 3: Dashboard Query Pipeline
```python
# Task Chain: User Query → ChromaDB → Aggregation → Visualization
1. User inputs natural language query
2. Query Parser extracts intent + filters
3. ChromaDB Semantic Search finds relevant docs
4. Supabase Fetcher gets structured data
5. Aggregator combines embeddings + SQL results
6. Visualizer generates charts/maps
7. Cache Writer stores for 5-minute TTL

# Execution: Real-time (<500ms target)
```

---

### 1.3 ChromaDB Query Patterns for Dashboard

#### Pattern 1: Multi-Collection Join Query
```python
# Use Case: "Show me all insights about Vietnam processing from last month"

# Step 1: Query documents
doc_results = chroma_client.query(
    collection_name="commodity_documents",
    query_texts=["Vietnam cashew processing capacity"],
    where={
        "$and": [
            {"commodity_type": "cashew"},
            {"created_at": {"$gte": "2025-11-24"}}
        ]
    }
)

# Step 2: Query Perplexity analyses
pplx_results = chroma_client.query(
    collection_name="perplexity_analyses",
    query_texts=["Vietnam processing industry news"],
    where={
        "query_date": {"$gte": "2025-11-24"}
    }
)

# Step 3: Query Claude reports
claude_results = chroma_client.query(
    collection_name="claude_reports",
    query_texts=["Vietnam processing recommendations"],
    where={
        "published_at": {"$gte": "2025-11-24"}
    }
)

# Step 4: Merge results with relevance scoring
combined = merge_and_rank([doc_results, pplx_results, claude_results])
```

#### Pattern 2: Time-Series Semantic Search
```python
# Use Case: "Track sentiment evolution about US-China trade tensions"

dates = ["2025-11-24", "2025-12-01", "2025-12-08", "2025-12-15", "2025-12-24"]
sentiment_timeline = []

for date in dates:
    result = chroma_client.query(
        collection_name="perplexity_analyses",
        query_texts=["US-China trade war impact Cambodia exports"],
        where={
            "$and": [
                {"query_date": {"$gte": date}},
                {"query_date": {"$lt": add_days(date, 7)}}
            ]
        },
        n_results=5
    )
    sentiment_timeline.append({
        "date": date,
        "documents": result,
        "avg_sentiment": calculate_sentiment(result)
    })
```

#### Pattern 3: Hybrid SQL + Vector Search
```python
# Use Case: "Find provinces with declining cashew yield AND negative news sentiment"

# Step 1: Supabase SQL for yield data
sql_results = supabase.rpc('get_declining_yield_provinces', {
    'commodity': 'cashew',
    'year_start': 2023,
    'year_end': 2024
})
provinces = [r['province'] for r in sql_results]

# Step 2: ChromaDB semantic search for negative sentiment
negative_news = []
for province in provinces:
    result = chroma_client.query(
        collection_name="commodity_documents",
        query_texts=[f"{province} cashew production challenges problems"],
        where={"province": province},
        n_results=3
    )
    negative_news.append({
        "province": province,
        "yield_decline": get_yield_for_province(province),
        "negative_indicators": result
    })

# Step 3: Rank provinces by risk score
risk_ranked = rank_by_risk(negative_news)
```

#### Pattern 4: Geospatial + Semantic Query
```python
# Use Case: "Find high-yield cashew farms near Vietnam border with recent expansion"

# Step 1: Geospatial filter (provinces near Vietnam)
border_provinces = ["Ratanakiri", "Mondulkiri", "Kratie"]

# Step 2: ChromaDB query for expansion keywords
expansion_docs = chroma_client.query(
    collection_name="commodity_documents",
    query_texts=["new plantation expansion investment growth"],
    where={
        "$and": [
            {"province": {"$in": border_provinces}},
            {"commodity_type": "cashew"},
            {"year": 2024}
        ]
    }
)

# Step 3: Cross-reference with production data
high_yield_farms = chroma_client.query(
    collection_name="production_data",
    query_texts=["high productivity efficient farming"],
    where={
        "$and": [
            {"province": {"$in": border_provinces}},
            {"yield_per_hectare": {"$gte": 1.8}}
        ]
    }
)

# Step 4: Merge and map
investment_opportunities = merge_geo_semantic(expansion_docs, high_yield_farms)
```

---

## PART 2: ATOMIC TASK BREAKDOWN (127 TASKS)

### PHASE 0: INFRASTRUCTURE SETUP (16 TASKS)

#### Track 0.1: MCP Server Configuration (Agent: mcp-expert)
**Tasks**:
1. **T001**: Configure Supabase MCP with project ref `xqfozbocgyrelznccweh`
2. **T002**: Test Supabase MCP connection + list tables
3. **T003**: Configure Fetch MCP for HTTP requests
4. **T004**: Test Fetch MCP with MEF Cambodia API
5. **T005**: Configure Context7 MCP for session storage
6. **T006**: Configure ChromaDB MCP server
7. **T007**: Create ChromaDB collection: `commodity_documents`
8. **T008**: Create ChromaDB collection: `perplexity_analyses`
9. **T009**: Create ChromaDB collection: `claude_reports`
10. **T010**: Create ChromaDB collection: `commodity_prices`
11. **T011**: Create ChromaDB collection: `production_data`
12. **T012**: Test ChromaDB semantic search across all collections
13. **T013**: Document all MCP configurations in `.mcp.json`
14. **T014**: Create MCP health check script
15. **T015**: Setup MCP logging and monitoring
16. **T016**: Create MCP troubleshooting runbook

**Priority**: P0 (CRITICAL)
**Duration**: 8 hours
**Dependencies**: None (can start immediately)
**Deliverable**: `.mcp.json` with 5 configured servers + test results

---

#### Track 0.2: Supabase Schema Design (Agent: backend-architect)
**Tasks**:
17. **T017**: Design `commodities` table schema (id, name, category, metadata)
18. **T018**: Design `prices` table schema (commodity_id, date, price, volume, source, destination)
19. **T019**: Design `production` table schema (commodity_id, year, province, area, production, yield, geolocation)
20. **T020**: Design `perplexity_analyses` table schema (query_type, query_text, response, citations, created_at)
21. **T021**: Design `claude_reports` table schema (report_type, title, content, insights, recommendations)
22. **T022**: Design `geopolitical_events` table schema (event_date, title, impact_level, countries, commodities)
23. **T023**: Design `data_sources` table schema (name, url, last_fetch, status, error_log)
24. **T024**: Create BRIN indexes on timeseries columns (prices.date, production.year)
25. **T025**: Create B-tree indexes on foreign keys (commodity_id)
26. **T026**: Create GIN indexes on JSONB metadata columns
27. **T027**: Create full-text search indexes on report content
28. **T028**: Design RLS policies (if multi-tenancy needed)
29. **T029**: Create SQL migration file
30. **T030**: Execute migration in Supabase project
31. **T031**: Seed initial commodities (cashew, rubber)
32. **T032**: Create Supabase views for dashboard queries

**Priority**: P0 (CRITICAL)
**Duration**: 6 hours
**Dependencies**: None
**Deliverable**: `supabase_schema_v1.sql` + migration executed

---

#### Track 0.3: Python Project Structure (Agent: fullstack-developer)
**Tasks**:
33. **T033**: Create project directory structure
34. **T034**: Initialize Poetry project (`pyproject.toml`)
35. **T035**: Add core dependencies (fastapi, uvicorn, streamlit, supabase)
36. **T036**: Add AI dependencies (anthropic placeholder, httpx for Perplexity)
37. **T037**: Add data processing dependencies (pandas, geopandas, pytesseract)
38. **T038**: Add scheduling dependencies (apscheduler)
39. **T039**: Add testing dependencies (pytest, pytest-asyncio, httpx mock)
40. **T040**: Add ChromaDB Python client (`chromadb`)
41. **T041**: Create `.env.example` with all required variables
42. **T042**: Create `.gitignore` for Python + sensitive files
43. **T043**: Create `README.md` with setup instructions
44. **T044**: Create `docker-compose.yml` (PostgreSQL + Redis for dev)
45. **T045**: Create Dockerfile for production
46. **T046**: Create `app/__init__.py` and sub-packages
47. **T047**: Create `dashboard/__init__.py` and structure
48. **T048**: Create `tests/` directory with conftest.py

**Priority**: P0 (CRITICAL)
**Duration**: 4 hours
**Dependencies**: None
**Deliverable**: Complete project structure ready for coding

---

### PHASE 1: DATA COLLECTION LAYER (32 TASKS)

#### Track 1.1: Base Collector Framework (Agent: fullstack-developer)
**Tasks**:
49. **T049**: Create `collectors/base.py` abstract class
50. **T050**: Implement retry logic with exponential backoff (tenacity)
51. **T051**: Implement rate limiting base class
52. **T052**: Implement error handling and logging (structlog)
53. **T053**: Create collector health check interface
54. **T054**: Create collector metrics tracking (success rate, latency)
55. **T055**: Write unit tests for BaseCollector
56. **T056**: Document collector interface with examples

**Priority**: P1 (HIGH)
**Duration**: 4 hours
**Dependencies**: T048 (project structure)
**Deliverable**: `app/collectors/base.py` + tests

---

#### Track 1.2: MEF Cambodia Collector (Agent: fullstack-developer)
**Tasks**:
57. **T057**: Implement `collectors/mef_collector.py`
58. **T058**: Test MEF API endpoint (pd_68b588a0eb43bd000745b588)
59. **T059**: Implement JSON response parsing
60. **T060**: Map MEF data to Price model
61. **T061**: Handle pagination (page_size=100)
62. **T062**: Implement data validation (price ranges, date checks)
63. **T063**: Write unit tests with mocked responses
64. **T064**: Write integration test with real API
65. **T065**: Store MEF data in ChromaDB `commodity_prices` collection
66. **T066**: Create MEF collector monitoring dashboard widget

**Priority**: P1 (HIGH)
**Duration**: 5 hours
**Dependencies**: T056 (base collector)
**Deliverable**: Working MEF collector + ChromaDB integration

---

#### Track 1.3: WITS World Bank Collector (Agent: fullstack-developer)
**Tasks**:
67. **T067**: Implement `collectors/wits_collector.py`
68. **T068**: Test WITS API endpoint (country=KHM)
69. **T069**: Implement XML parsing (lxml)
70. **T070**: Map HS codes (cashew=0801, rubber=4001)
71. **T071**: Extract export data (volume, destination, value)
72. **T072**: Convert units (kg → tons, currencies → USD)
73. **T073**: Implement XML schema validation
74. **T074**: Write unit tests with mocked XML
75. **T075**: Write integration test with real API
76. **T076**: Store WITS data in ChromaDB collections
77. **T077**: Create WITS collector error handling for malformed XML

**Priority**: P1 (HIGH)
**Duration**: 5 hours
**Dependencies**: T056 (base collector)
**Deliverable**: Working WITS collector + ChromaDB integration

---

#### Track 1.4: ODC Collector (Agent: fullstack-developer)
**Tasks**:
78. **T078**: Implement `collectors/odc_collector.py`
79. **T079**: Test ODC website structure (https://data.opendevelopmentcambodia.net)
80. **T080**: Implement HTML scraping (BeautifulSoup)
81. **T081**: Search for "cashew" and "rubber" datasets
82. **T082**: Download CSV files (requests + pandas)
83. **T083**: Handle Khmer column names (transliteration)
84. **T084**: Parse CSV with pandas (robust to format variations)
85. **T085**: Extract production data (area, yield, province)
86. **T086**: Implement fallback to manual CSV upload
87. **T087**: Write unit tests with sample CSVs
88. **T088**: Store ODC data in ChromaDB `production_data` collection

**Priority**: P1 (HIGH)
**Duration**: 6 hours
**Dependencies**: T056 (base collector)
**Deliverable**: Working ODC collector + ChromaDB integration

---

#### Track 1.5: Google Drive PDF/KML Collector (Agent: fullstack-developer)
**Tasks**:
89. **T089**: Implement `collectors/gdrive_collector.py`
90. **T090**: Configure Google Docs API (key: AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk)
91. **T091**: List files in "cashew cambodia" folder
92. **T092**: List files in "rubber cambodia" folder
93. **T093**: Download PDFs to local cache (checksum-based deduplication)
94. **T094**: Implement OCR pipeline (pytesseract + Khmer language pack)
95. **T095**: Extract text from PDFs with confidence scores
96. **T096**: Parse KML files (geopandas)
97. **T097**: Extract geospatial coordinates from KML
98. **T098**: Implement text chunking (1000 chars, 200 overlap)
99. **T099**: Extract metadata (province, year, commodity) using regex
100. **T100**: Store PDFs in ChromaDB `commodity_documents` collection
101. **T101**: Store KML geospatial data in ChromaDB `production_data`
102. **T102**: Write manual review UI for low-confidence OCR results
103. **T103**: Write unit tests with sample PDF/KML files
104. **T104**: Implement incremental sync (only new/changed files)

**Priority**: P1 (HIGH)
**Duration**: 10 hours (COMPLEX)
**Dependencies**: T056 (base collector)
**Deliverable**: Working GDrive collector + ChromaDB integration + OCR pipeline

---

### PHASE 2: AI SERVICES LAYER (20 TASKS)

#### Track 2.1: Perplexity Service (Agent: fullstack-developer)
**Tasks**:
105. **T105**: Implement `services/perplexity_service.py`
106. **T106**: Configure Perplexity API (key: pplx-rXvPzb...)
107. **T107**: Implement rate limiter (1000 req/month = 33/day)
108. **T108**: Implement Redis caching (6-hour TTL)
109. **T109**: Create query templates (daily_price, geopolitics, market_trends)
110. **T110**: Implement citation extraction from responses
111. **T111**: Store Perplexity results in Supabase `perplexity_analyses`
112. **T112**: Store Perplexity results in ChromaDB for semantic search
113. **T113**: Implement fallback to cached results if rate limit hit
114. **T114**: Write unit tests with mocked API responses
115. **T115**: Monitor API costs and usage dashboard

**Priority**: P1 (HIGH)
**Duration**: 5 hours
**Dependencies**: T032 (Supabase schema), T012 (ChromaDB collections)
**Deliverable**: Working Perplexity service + ChromaDB integration

---

#### Track 2.2: Claude Mock Service (Agent: fullstack-developer)
**Tasks**:
116. **T116**: Implement `services/claude_mock_service.py` (NO REAL API)
117. **T117**: Create prompt templates (DAILY_REPORT, WEEKLY_REPORT)
118. **T118**: Implement mock response generator using templates
119. **T119**: Query ChromaDB for historical context (past reports, analyses)
120. **T120**: Generate mock insights based on input data patterns
121. **T121**: Format output as markdown with sections
122. **T122**: Store mock reports in Supabase `claude_reports`
123. **T123**: Store mock reports in ChromaDB `claude_reports` collection
124. **T124**: Write unit tests for mock service
125. **T125**: Create placeholder for future real Claude API integration

**Priority**: P1 (HIGH)
**Duration**: 4 hours
**Dependencies**: T112 (Perplexity service), T012 (ChromaDB collections)
**Deliverable**: Working Claude mock service + ChromaDB integration

---

#### Track 2.3: Prompt Engineering (Agent: prompt-engineer)
**Tasks**:
126. **T126**: Optimize Perplexity daily price query prompt
127. **T127**: Optimize Perplexity geopolitics query prompt
128. **T128**: Optimize Perplexity market trends query prompt
129. **T129**: Optimize Perplexity competitor analysis prompt
130. **T130**: Create Claude daily report mock template
131. **T131**: Create Claude weekly report mock template
132. **T132**: Create Claude crisis report mock template
133. **T133**: Document ChromaDB query patterns for AI services
134. **T134**: Create A/B testing framework for prompt variants

**Priority**: P2 (MEDIUM)
**Duration**: 4 hours
**Dependencies**: T115 (Perplexity service), T125 (Claude mock service)
**Deliverable**: Optimized prompt templates + A/B testing framework

---

### PHASE 3: SCHEDULING & AUTOMATION (12 TASKS)

#### Track 3.1: APScheduler Setup (Agent: fullstack-developer)
**Tasks**:
135. **T135**: Implement `scheduler/scheduler.py` (singleton pattern)
136. **T136**: Configure APScheduler with AsyncIOScheduler
137. **T137**: Setup timezone (Asia/Phnom_Penh GMT+7)
138. **T138**: Create job persistence (SQLite job store)
139. **T139**: Implement job execution logging
140. **T140**: Create manual job trigger API endpoint

**Priority**: P1 (HIGH)
**Duration**: 3 hours
**Dependencies**: T104 (collectors complete)
**Deliverable**: Working APScheduler infrastructure

---

#### Track 3.2: Scheduled Jobs (Agent: fullstack-developer)
**Tasks**:
141. **T141**: Create `jobs/daily_collection_job.py` (6am daily)
142. **T142**: Create `jobs/daily_perplexity_job.py` (6:15am daily)
143. **T143**: Create `jobs/daily_claude_mock_job.py` (6:30am daily)
144. **T144**: Create `jobs/weekly_report_job.py` (Monday 6am)
145. **T145**: Create `jobs/chromadb_maintenance_job.py` (daily cleanup)
146. **T146**: Implement error handling and retry logic for jobs

**Priority**: P1 (HIGH)
**Duration**: 4 hours
**Dependencies**: T140 (scheduler setup), T125 (AI services)
**Deliverable**: 5 working scheduled jobs

---

### PHASE 4: DASHBOARD (25 TASKS)

#### Track 4.1: Dashboard Design (Agent: ui-ux-designer)
**Tasks**:
147. **T147**: Create wireframes for Overview page
148. **T148**: Create wireframes for Cashew Deep Dive page
149. **T149**: Create wireframes for Rubber Deep Dive page
150. **T150**: Create wireframes for Reports Archive page
151. **T151**: Create wireframes for ChromaDB Search page
152. **T152**: Design color palette (commodity-specific colors)
153. **T153**: Design typography scale
154. **T154**: Design icon set (cashew, rubber, geopolitical, price)
155. **T155**: Design responsive breakpoints (mobile 375px, tablet 768px, desktop 1440px)
156. **T156**: Create design system documentation

**Priority**: P2 (MEDIUM)
**Duration**: 6 hours
**Dependencies**: None (can parallelize)
**Deliverable**: Complete design system + wireframes

---

#### Track 4.2: Streamlit Implementation (Agent: fullstack-developer)
**Tasks**:
157. **T157**: Implement `dashboard/app.py` (main entry point)
158. **T158**: Create sidebar commodity selector
159. **T159**: Implement Overview page (KPIs, charts, latest events)
160. **T160**: Implement Cashew Deep Dive page
161. **T161**: Implement Rubber Deep Dive page
162. **T162**: Implement Reports Archive page
163. **T163**: Implement ChromaDB Semantic Search page
164. **T164**: Create reusable components in `components/metrics.py`
165. **T165**: Create reusable components in `components/charts.py`
166. **T166**: Create reusable components in `components/tables.py`
167. **T167**: Create reusable components in `components/chromadb_search.py`
168. **T168**: Implement Supabase query caching (@st.cache_data, TTL=5min)
169. **T169**: Implement ChromaDB query caching
170. **T170**: Create custom CSS for mobile-first design
171. **T171**: Implement dark mode toggle

**Priority**: P1 (HIGH)
**Duration**: 12 hours
**Dependencies**: T156 (design system), T146 (jobs complete)
**Deliverable**: Fully functional Streamlit dashboard

---

#### Track 4.3: Visualizations (Agent: fullstack-developer)
**Tasks**:
172. **T172**: Create price timeseries chart (Plotly dual-axis)
173. **T173**: Create production heatmap (Folium + KML overlay)
174. **T174**: Create export destinations sunburst chart (Plotly)
175. **T175**: Create correlation matrix heatmap
176. **T176**: Create forecasting chart with confidence intervals
177. **T177**: Create ChromaDB similarity graph visualization
178. **T178**: Optimize chart rendering (<2s load time)
179. **T179**: Add export functionality (PNG, SVG, CSV)

**Priority**: P2 (MEDIUM)
**Duration**: 6 hours
**Dependencies**: T171 (dashboard implementation)
**Deliverable**: 7+ interactive visualizations

---

### PHASE 5: TESTING (22 TASKS)

#### Track 5.1: Unit Tests (Agent: test-engineer)
**Tasks**:
180. **T180**: Write tests for MEF collector
181. **T181**: Write tests for WITS collector
182. **T182**: Write tests for ODC collector
183. **T183**: Write tests for GDrive collector
184. **T184**: Write tests for Perplexity service
185. **T185**: Write tests for Claude mock service
186. **T186**: Write tests for ChromaDB integration layer
187. **T187**: Write tests for Pydantic models validation
188. **T188**: Write tests for APScheduler jobs
189. **T189**: Setup pytest coverage reporting (target >80%)

**Priority**: P1 (HIGH)
**Duration**: 8 hours
**Dependencies**: T179 (all features implemented)
**Deliverable**: Comprehensive unit test suite

---

#### Track 5.2: Integration Tests (Agent: test-engineer)
**Tasks**:
190. **T190**: Setup test Supabase environment
191. **T191**: Setup test ChromaDB instance
192. **T192**: Write integration test: Collector → Supabase
193. **T193**: Write integration test: Collector → ChromaDB
194. **T194**: Write integration test: Perplexity → ChromaDB
195. **T195**: Write integration test: APScheduler job execution
196. **T196**: Write integration test: Dashboard data fetching
197. **T197**: Write integration test: Multi-collection ChromaDB queries

**Priority**: P1 (HIGH)
**Duration**: 6 hours
**Dependencies**: T189 (unit tests)
**Deliverable**: Integration test suite

---

#### Track 5.3: E2E Tests (Agent: test-engineer)
**Tasks**:
198. **T198**: Setup Playwright for Streamlit testing
199. **T199**: Write E2E test: Overview page load
200. **T200**: Write E2E test: Commodity switcher
201. **T201**: Write E2E test: ChromaDB semantic search
202. **T202**: Write E2E test: Report expansion
203. **T203**: Write E2E test: CSV export
204. **T204**: Write E2E test: Mobile viewport (375x667)
205. **T205**: Run Lighthouse performance audit (target <3s load)

**Priority**: P2 (MEDIUM)
**Duration**: 5 hours
**Dependencies**: T171 (dashboard complete)
**Deliverable**: E2E test suite + performance report

---

### PHASE 6: DEPLOYMENT (18 TASKS)

#### Track 6.1: Docker & Deployment (Agent: fullstack-developer)
**Tasks**:
206. **T206**: Create multi-stage Dockerfile
207. **T207**: Create production docker-compose.yml
208. **T208**: Create .dockerignore file
209. **T209**: Add health check endpoint `/health`
210. **T210**: Test Docker build locally
211. **T211**: Push Docker image to registry

**Priority**: P1 (HIGH)
**Duration**: 3 hours
**Dependencies**: T205 (testing complete)
**Deliverable**: Production-ready Docker image

---

#### Track 6.2: Deployment Platform Analysis (Agent: backend-architect)
**Tasks**:
212. **T212**: Analyze Railway.app deployment options
213. **T213**: Analyze Render.com deployment options
214. **T214**: Analyze Fly.io deployment options
215. **T215**: Compare costs (monthly estimates)
216. **T216**: Create deployment decision matrix
217. **T217**: Write step-by-step deployment guide for recommended platform

**Priority**: P1 (HIGH)
**Duration**: 3 hours
**Dependencies**: T211 (Docker image ready)
**Deliverable**: Deployment recommendation + guide

---

#### Track 6.3: Monitoring & Logging (Agent: fullstack-developer)
**Tasks**:
218. **T218**: Setup Sentry for error tracking
219. **T219**: Configure structlog for JSON logging
220. **T220**: Setup Uptime Robot for /health monitoring
221. **T221**: Create monitoring dashboard in Streamlit
222. **T222**: Implement log aggregation (stdout → Docker logs)
223. **T223**: Create alert rules (email if down >5min)

**Priority**: P1 (HIGH)
**Duration**: 4 hours
**Dependencies**: T217 (deployment guide)
**Deliverable**: Production monitoring setup

---

### PHASE 7: DOCUMENTATION & REVIEW (10 TASKS)

#### Track 7.1: Code Review (Agent: code-reviewer)
**Tasks**:
224. **T224**: Review security (API keys, SQL injection, XSS)
225. **T225**: Review code quality (DRY, complexity, naming)
226. **T226**: Review performance (N+1 queries, caching, async)
227. **T227**: Review error handling (try-except, retries, fallbacks)
228. **T228**: Review test coverage (identify gaps)
229. **T229**: Create prioritized fix list (CRITICAL/WARNING/SUGGESTION)

**Priority**: P1 (HIGH)
**Duration**: 4 hours
**Dependencies**: T223 (all code complete)
**Deliverable**: Code review report + fix priorities

---

#### Track 7.2: Documentation (Agent: context-manager)
**Tasks**:
230. **T230**: Write comprehensive README.md
231. **T231**: Document ChromaDB collections and query patterns
232. **T232**: Create API documentation (FastAPI auto-docs)
233. **T233**: Create architecture diagram (Mermaid or ASCII)
234. **T234**: Write deployment runbook
235. **T235**: Write troubleshooting guide
236. **T236**: Create user guide for dashboard
237. **T237**: Document ChromaDB semantic search usage

**Priority**: P2 (MEDIUM)
**Duration**: 5 hours
**Dependencies**: T229 (code review complete)
**Deliverable**: Complete documentation suite

---

---

## PART 3: AGENT ASSIGNMENT MATRIX

| Agent | Tasks Assigned | Total Hours | Priority |
|-------|----------------|-------------|----------|
| **mcp-expert** | T001-T016 (MCP setup + ChromaDB) | 8h | P0 |
| **backend-architect** | T017-T032 (Supabase schema), T212-T217 (Deployment analysis) | 9h | P0 |
| **fullstack-developer** | T033-T048 (Project structure), T049-T104 (Collectors), T105-T125 (AI services), T135-T146 (Scheduler), T157-T179 (Dashboard + viz), T206-T211 (Docker), T218-T223 (Monitoring) | 68h | P1 |
| **prompt-engineer** | T126-T134 (Prompt optimization) | 4h | P2 |
| **test-engineer** | T180-T205 (Unit + Integration + E2E tests) | 19h | P1 |
| **ui-ux-designer** | T147-T156 (Dashboard design) | 6h | P2 |
| **code-reviewer** | T224-T229 (Code review) | 4h | P1 |
| **context-manager** | T230-T237 (Documentation) | 5h | P2 |

**Total Estimated Hours**: 123 hours
**With 4 parallel developers**: ~30 hours (4 days) wall-clock time
**Critical path (sequential dependencies)**: ~23 days if single-threaded

---

## PART 4: EXECUTION TIMELINE (CRITICAL PATH)

### Week 1: Foundation (Days 1-7)

#### Day 1 (8 parallel tasks)
- **mcp-expert**: T001-T016 (MCP + ChromaDB setup) - 8h
- **backend-architect**: T017-T032 (Supabase schema) - 6h
- **fullstack-developer**: T033-T048 (Project structure) - 4h

#### Day 2-3 (16 parallel tasks)
- **fullstack-developer Team 1**: T049-T066 (Base + MEF collector) - 9h
- **fullstack-developer Team 2**: T067-T077 (WITS collector) - 5h
- **fullstack-developer Team 3**: T078-T088 (ODC collector) - 6h

#### Day 4-5 (10 parallel tasks)
- **fullstack-developer Team 1**: T089-T104 (GDrive collector + OCR) - 10h
- **ui-ux-designer**: T147-T156 (Dashboard design) - 6h

### Week 2: AI Services + Scheduling (Days 8-14)

#### Day 6-7 (15 parallel tasks)
- **fullstack-developer Team 1**: T105-T115 (Perplexity service) - 5h
- **fullstack-developer Team 2**: T116-T125 (Claude mock service) - 4h
- **prompt-engineer**: T126-T134 (Prompt optimization) - 4h

#### Day 8-9 (12 parallel tasks)
- **fullstack-developer**: T135-T146 (Scheduler + Jobs) - 7h

### Week 3: Dashboard + Testing (Days 15-21)

#### Day 10-12 (25 parallel tasks)
- **fullstack-developer Team 1**: T157-T171 (Dashboard implementation) - 12h
- **fullstack-developer Team 2**: T172-T179 (Visualizations) - 6h

#### Day 13-15 (22 parallel tasks)
- **test-engineer Team 1**: T180-T189 (Unit tests) - 8h
- **test-engineer Team 2**: T190-T197 (Integration tests) - 6h
- **test-engineer Team 3**: T198-T205 (E2E tests) - 5h

### Week 4: Deployment + Review (Days 22-28)

#### Day 16-17 (18 parallel tasks)
- **fullstack-developer**: T206-T211 (Docker) - 3h
- **backend-architect**: T212-T217 (Deployment analysis) - 3h
- **fullstack-developer**: T218-T223 (Monitoring) - 4h

#### Day 18-19 (10 parallel tasks)
- **code-reviewer**: T224-T229 (Code review) - 4h
- **context-manager**: T230-T237 (Documentation) - 5h

#### Day 20-23: Buffer for fixes + final testing

---

## PART 5: DEPENDENCY GRAPH

```mermaid
graph TD
    A[T001-T016: MCP Setup] --> B[T017-T032: Supabase Schema]
    A --> C[T033-T048: Project Structure]
    C --> D[T049-T056: Base Collector]
    D --> E[T057-T066: MEF Collector]
    D --> F[T067-T077: WITS Collector]
    D --> G[T078-T088: ODC Collector]
    D --> H[T089-T104: GDrive Collector]

    B --> I[T105-T115: Perplexity Service]
    I --> J[T116-T125: Claude Mock Service]
    I --> K[T126-T134: Prompt Engineering]

    E --> L[T135-T140: Scheduler Setup]
    F --> L
    G --> L
    H --> L
    J --> L
    L --> M[T141-T146: Scheduled Jobs]

    M --> N[T157-T171: Dashboard Implementation]
    N --> O[T172-T179: Visualizations]

    O --> P[T180-T189: Unit Tests]
    P --> Q[T190-T197: Integration Tests]
    Q --> R[T198-T205: E2E Tests]

    R --> S[T206-T211: Docker]
    S --> T[T212-T217: Deployment Analysis]
    T --> U[T218-T223: Monitoring]

    U --> V[T224-T229: Code Review]
    V --> W[T230-T237: Documentation]
```

---

## PART 6: CHROMADB CONFIGURATION UPDATES

### Updated `.mcp.json`

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "executeautomation-playwright-server": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase@latest",
        "--read-only",
        "--project-ref=xqfozbocgyrelznccweh"
      ],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "<personal-access-token>"
      }
    },
    "chromadb": {
      "command": "uvx",
      "args": ["mcp-server-chromadb"],
      "env": {
        "CHROMADB_PATH": "./chroma_data",
        "CHROMADB_HOST": "localhost",
        "CHROMADB_PORT": "8000",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

### ChromaDB Server Setup Script

```bash
# scripts/setup_chromadb.sh
#!/bin/bash

# Install ChromaDB MCP server
pip install chromadb mcp-server-chromadb

# Create data directory
mkdir -p ./chroma_data

# Start ChromaDB server
uvx mcp-server-chromadb --host localhost --port 8000 --persist ./chroma_data

# Initialize collections
python scripts/init_chromadb_collections.py
```

### ChromaDB Initialization Script

```python
# scripts/init_chromadb_collections.py
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

# Collection 1: Commodity Documents
client.create_collection(
    name="commodity_documents",
    metadata={
        "description": "Searchable repository of Cambodia agri PDFs/KML",
        "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
    }
)

# Collection 2: Perplexity Analyses
client.create_collection(
    name="perplexity_analyses",
    metadata={
        "description": "Searchable archive of Perplexity AI research"
    }
)

# Collection 3: Claude Reports
client.create_collection(
    name="claude_reports",
    metadata={
        "description": "Archive of AI-generated market reports"
    }
)

# Collection 4: Commodity Prices
client.create_collection(
    name="commodity_prices",
    metadata={
        "description": "Timestamped commodity price data with context"
    }
)

# Collection 5: Production Data
client.create_collection(
    name="production_data",
    metadata={
        "description": "Agricultural production stats with geolocation"
    }
)

print("✓ All 5 ChromaDB collections created successfully")
```

---

## PART 7: SUCCESS METRICS

### Week 1 Milestones
- [ ] All 5 ChromaDB collections created and tested
- [ ] Supabase schema deployed with 7 tables + indexes
- [ ] 4 data collectors running (MEF, WITS, ODC, GDrive)
- [ ] ChromaDB ingestion pipeline working (100+ documents stored)

### Week 2 Milestones
- [ ] Perplexity service integrated with ChromaDB
- [ ] Claude mock service generating reports using ChromaDB context
- [ ] APScheduler running daily jobs successfully
- [ ] ChromaDB semantic search returning relevant results (<500ms)

### Week 3 Milestones
- [ ] Streamlit dashboard live with ChromaDB search page
- [ ] Unit test coverage >80%
- [ ] Integration tests passing (Supabase + ChromaDB)
- [ ] E2E tests passing (dashboard interactions)

### Week 4 Milestones
- [ ] Production deployment on Railway/Render/Fly.io
- [ ] Monitoring active (Sentry + Uptime Robot)
- [ ] Documentation complete with ChromaDB examples
- [ ] Code review issues resolved

### Final Success Criteria
- [ ] **ChromaDB Performance**: Semantic search <500ms for 10k documents
- [ ] **Dashboard Load Time**: <3s on 3G connection
- [ ] **Data Collection**: <5% failure rate across all collectors
- [ ] **Test Coverage**: >80% code coverage
- [ ] **Uptime**: >99% after first week
- [ ] **Cost**: <$50/month total infrastructure

---

## PART 8: RISK MITIGATION

### Risk 1: ChromaDB Performance Degradation
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Implement aggressive caching (5-minute TTL for queries)
- Use metadata filtering before semantic search
- Limit result set to top 10 most relevant
- Consider pgvector extension in Supabase as fallback

### Risk 2: OCR Quality Below 90%
**Probability**: High
**Impact**: Medium
**Mitigation**:
- Flag low-confidence OCR results for manual review
- Use multiple OCR engines (Tesseract + Google Vision API)
- Store OCR confidence scores in ChromaDB metadata
- Build correction interface in dashboard

### Risk 3: API Rate Limiting (Perplexity/Google Drive)
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Implement exponential backoff with jitter
- Use Redis for aggressive caching (24h TTL)
- Query ChromaDB for similar past results before API call
- Manual data entry fallback

### Risk 4: ChromaDB Storage Growth
**Probability**: High
**Impact**: Low
**Mitigation**:
- Implement weekly cleanup job (delete duplicates)
- Archive old documents (>1 year) to S3
- Monitor disk usage (alert at 80%)
- Use compression for large text chunks

### Risk 5: No Product-Market Fit
**Probability**: Medium
**Impact**: Critical
**Mitigation**:
- Launch beta with 10 users by Week 6
- Collect feedback via dashboard survey widget
- Track usage metrics (DAU, queries/day, retention)
- Pivot to data licensing if adoption <50%

---

## PART 9: PARALLEL EXECUTION OPPORTUNITIES

### Maximum Parallelization (8 Concurrent Streams)

**Stream 1**: MCP Expert (T001-T016)
**Stream 2**: Backend Architect (T017-T032)
**Stream 3**: Fullstack Dev Team 1 - Collectors (T033-T088)
**Stream 4**: Fullstack Dev Team 2 - AI Services (T105-T125)
**Stream 5**: UI/UX Designer (T147-T156)
**Stream 6**: Fullstack Dev Team 3 - Dashboard (T157-T179)
**Stream 7**: Test Engineer Team (T180-T205)
**Stream 8**: DevOps (T206-T223)

### Dependencies Requiring Sequential Execution

1. **ChromaDB Setup → Data Ingestion**
   - Cannot ingest documents before collections exist
   - Sequence: T001-T016 → T089-T104

2. **Collectors → AI Services**
   - Cannot run Perplexity without data
   - Sequence: T057-T088 → T105-T115

3. **AI Services → Dashboard**
   - Cannot display reports without generation
   - Sequence: T116-T125 → T157-T171

4. **Dashboard → Testing**
   - Cannot test UI before it exists
   - Sequence: T157-T179 → T198-T205

5. **Testing → Deployment**
   - Cannot deploy before tests pass
   - Sequence: T180-T205 → T206-T223

---

## PART 10: CHROMADB BEST PRACTICES

### 1. Collection Naming Convention
```python
# Use descriptive, snake_case names
✓ "commodity_documents"
✓ "perplexity_analyses"
✗ "docs"
✗ "Data"
```

### 2. Metadata Design
```python
# Include rich metadata for filtering
metadata = {
    "commodity_type": "cashew",  # Categorical
    "year": 2024,                # Numeric
    "province": "Kampong Cham",  # String
    "confidence": 0.92,          # Float
    "created_at": "2025-12-24T10:00:00Z"  # ISO datetime
}
```

### 3. Chunking Strategy
```python
# For long PDFs
chunk_size = 1000  # chars
chunk_overlap = 200  # preserve context across chunks

# For structured data (prices, production)
chunk_size = None  # Store entire record as one document
```

### 4. Query Optimization
```python
# Always filter by metadata first, then semantic search
result = client.query(
    collection_name="commodity_documents",
    query_texts=["cashew production"],
    where={"commodity_type": "cashew", "year": 2024},  # Filter first
    n_results=10
)
```

### 5. Embedding Model Selection
```python
# Multilingual support for Khmer + English
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

### 6. Maintenance Schedule
```python
# Weekly cleanup job
def chromadb_maintenance():
    # Remove duplicates
    deduplicate_collections()

    # Archive old data (>1 year)
    archive_old_documents(days=365)

    # Rebuild indexes if needed
    reindex_collections()

    # Check disk usage
    alert_if_low_space(threshold_percent=80)
```

---

## APPENDIX: TASK REFERENCE QUICKLIST

### By Agent
- **mcp-expert**: T001-T016 (16 tasks)
- **backend-architect**: T017-T032, T212-T217 (22 tasks)
- **fullstack-developer**: T033-T048, T049-T104, T105-T125, T135-T146, T157-T179, T206-T211, T218-T223 (125 tasks)
- **prompt-engineer**: T126-T134 (9 tasks)
- **test-engineer**: T180-T205 (26 tasks)
- **ui-ux-designer**: T147-T156 (10 tasks)
- **code-reviewer**: T224-T229 (6 tasks)
- **context-manager**: T230-T237 (8 tasks)

### By Priority
- **P0 (CRITICAL)**: T001-T048 (48 tasks) - Must complete first
- **P1 (HIGH)**: T049-T146, T157-T171, T180-T197, T206-T229 (115 tasks)
- **P2 (MEDIUM)**: T126-T134, T147-T156, T172-T179, T198-T205, T230-T237 (37 tasks)

### By Phase
- **Phase 0 (Setup)**: T001-T048 (48 tasks)
- **Phase 1 (Collectors)**: T049-T104 (56 tasks)
- **Phase 2 (AI Services)**: T105-T134 (30 tasks)
- **Phase 3 (Scheduler)**: T135-T146 (12 tasks)
- **Phase 4 (Dashboard)**: T147-T179 (33 tasks)
- **Phase 5 (Testing)**: T180-T205 (26 tasks)
- **Phase 6 (Deployment)**: T206-T223 (18 tasks)
- **Phase 7 (Review)**: T224-T237 (14 tasks)

---

**END OF MAXIMUM TASK DECOMPOSITION**

Total Tasks: **237 atomic tasks**
Total Estimated Hours: **~180 hours**
Optimized Timeline: **23 days with parallelization**
ChromaDB Collections: **5 collections**
MCP Servers: **5 servers**

Ready for immediate execution.
