# Phase 4: System Architecture

**Project:** Cambodia Agricultural Intelligence Platform
**Phase:** 4 - UI & API Architecture
**Date:** December 27, 2024

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Integration Points](#integration-points)
6. [Database Schema](#database-schema)
7. [API Design](#api-design)
8. [Caching Strategy](#caching-strategy)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Farmer  │  │ Analyst │  │  Admin  │  │   API   │           │
│  │ (Mobile)│  │(Desktop)│  │(Desktop)│  │ Client  │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│       │            │            │            │                   │
│       └────────────┴────────────┴────────────┘                   │
│                          │                                       │
│                          ▼ HTTPS                                 │
└──────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Streamlit Application                       │  │
│  │              (Port 8501)                                 │  │
│  │                                                          │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │  │
│  │  │Search  │  │  Chat  │  │History │  │ Admin  │       │  │
│  │  │ Page   │  │  Page  │  │  Page  │  │  Page  │       │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘       │  │
│  │                                                          │  │
│  │  Components:                                             │  │
│  │  • Multilingual UI (Khmer/English/Vietnamese)           │  │
│  │  • Responsive layout (mobile/desktop)                   │  │
│  │  • Real-time updates                                    │  │
│  │  • Session state management                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTP/JSON
┌──────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                         │  │
│  │              (Port 8000)                                 │  │
│  │                                                          │  │
│  │  Middleware Stack:                                       │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ 1. CORS Handler                                    │ │  │
│  │  │ 2. Rate Limiter (3-tier)                          │ │  │
│  │  │ 3. Request Logger                                  │ │  │
│  │  │ 4. Error Handler                                   │ │  │
│  │  │ 5. Response Time Tracker                          │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  API Routes:                                             │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ /api/v1/search           (Semantic search)        │ │  │
│  │  │ /api/v1/rag/query        (RAG Q&A)                │ │  │
│  │  │ /api/v1/history          (Conversation history)   │ │  │
│  │  │ /api/v1/stats            (Usage statistics)       │ │  │
│  │  │ /api/v1/stats/budget     (Budget monitoring)      │ │  │
│  │  │ /api/v1/cache/clear      (Cache management)       │ │  │
│  │  │ /api/v1/health           (Health check)           │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Semantic   │  │ Perplexity   │  │    Cache     │         │
│  │   Search     │  │     RAG      │  │   Service    │         │
│  │   Service    │  │   Service    │  │   (Redis)    │         │
│  │              │  │              │  │              │         │
│  │ • Embed      │  │ • Context    │  │ • Get        │         │
│  │ • Search     │  │ • Query API  │  │ • Set        │         │
│  │ • Format     │  │ • Parse      │  │ • Stats      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Budget     │  │ Conversation │  │   Export     │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  │              │  │              │  │              │         │
│  │ • Track      │  │ • Save       │  │ • PDF        │         │
│  │ • Alert      │  │ • Load       │  │ • Markdown   │         │
│  │ • Report     │  │ • Search     │  │ • CSV        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Supabase PostgreSQL (Primary Database)         │  │
│  │                                                          │  │
│  │  Tables:                                                 │  │
│  │  • document_embeddings    (146 chunks, Phase 3)         │  │
│  │  • conversation_history   (New, Phase 4)                │  │
│  │  • usage_logs            (New, Phase 4)                 │  │
│  │                                                          │  │
│  │  Views:                                                  │  │
│  │  • v_monthly_budget      (Budget aggregations)          │  │
│  │  • v_top_queries         (Popular queries)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Redis Cache (Ephemeral Storage)                │  │
│  │                                                          │  │
│  │  Keys:                                                   │  │
│  │  • rag:response:{hash}   (24h TTL)                      │  │
│  │  • search:result:{hash}  (1h TTL)                       │  │
│  │  • rate_limit:month:*    (32d TTL)                      │  │
│  │  • rate_limit:day:*      (2d TTL)                       │  │
│  │  • rate_limit:hour:*     (2h TTL)                       │  │
│  │  • session:{id}          (7d TTL)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Perplexity   │  │   Supabase   │  │    Email     │         │
│  │     API      │  │   Backend    │  │    SMTP      │         │
│  │              │  │              │  │              │         │
│  │ • RAG LLM    │  │ • Database   │  │ • Alerts     │         │
│  │ • Citations  │  │ • Storage    │  │ • Reports    │         │
│  │ • $0.005/q   │  │ • Free tier  │  │ • Free       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Presentation Layer (Streamlit)

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit Application                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Main App (streamlit_app.py)                           │
│  ├─ Configuration                                       │
│  ├─ Session State Management                           │
│  ├─ Page Router                                         │
│  └─ Global Components (Header, Footer)                 │
│                                                         │
│  Pages (ui/pages/)                                      │
│  ├─ 1_search.py          (Semantic search UI)          │
│  ├─ 2_chat.py            (RAG chat interface)          │
│  ├─ 3_history.py         (Conversation history)        │
│  └─ 4_admin.py           (Admin dashboard)             │
│                                                         │
│  Components (ui/components/)                            │
│  ├─ search_box.py        (Search input)                │
│  ├─ result_card.py       (Result display)              │
│  ├─ chat_message.py      (Chat bubble)                 │
│  ├─ source_citation.py   (Citation display)            │
│  ├─ export_button.py     (Export functionality)        │
│  ├─ stats_chart.py       (Usage charts)                │
│  └─ language_selector.py (i18n switcher)               │
│                                                         │
│  Internationalization (ui/i18n/)                        │
│  ├─ translations.py      (Khmer/English/Vietnamese)    │
│  └─ utils.py             (Translation helpers)         │
│                                                         │
│  Utilities (ui/utils/)                                  │
│  ├─ api_client.py        (FastAPI client)              │
│  ├─ session.py           (Session management)          │
│  ├─ formatting.py        (Text formatting)             │
│  └─ validation.py        (Input validation)            │
│                                                         │
│  State Management                                       │
│  ├─ st.session_state.messages      (Chat history)     │
│  ├─ st.session_state.session_id    (User session)     │
│  ├─ st.session_state.language      (UI language)      │
│  ├─ st.session_state.budget_stats  (Budget info)      │
│  └─ st.session_state.cache_stats   (Cache metrics)    │
└─────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

1. **Single-Page Architecture:** Each page is independent, loaded via Streamlit's multi-page app
2. **Stateless Components:** Components are pure functions, state managed at page level
3. **API-First:** All data fetching through FastAPI endpoints (no direct DB access)
4. **Responsive Design:** CSS media queries for mobile/desktop layouts
5. **Progressive Enhancement:** Basic functionality works without JS

---

### 2. Application Layer (FastAPI)

```
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Main App (app/main.py)                                │
│  ├─ Application Factory                                │
│  ├─ Middleware Configuration                           │
│  ├─ Router Registration                                │
│  ├─ Startup/Shutdown Hooks                             │
│  └─ Exception Handlers                                 │
│                                                         │
│  Middleware Stack (app/middleware/)                     │
│  ├─ cors.py              (CORS handling)               │
│  ├─ rate_limiter.py      (3-tier rate limiting)        │
│  ├─ logger.py            (Request/response logging)    │
│  ├─ error_handler.py     (Global error handling)       │
│  └─ metrics.py           (Response time tracking)      │
│                                                         │
│  API Routes (app/api/routes/)                          │
│  ├─ semantic.py          (Search & RAG endpoints)      │
│  ├─ history.py           (Conversation history)        │
│  ├─ stats.py             (Usage statistics)            │
│  └─ admin.py             (Admin actions)               │
│                                                         │
│  Request/Response Models (app/models/)                  │
│  ├─ rag.py               (RAG request/response)        │
│  ├─ search.py            (Search request/response)     │
│  ├─ conversation.py      (Conversation models)         │
│  └─ stats.py             (Statistics models)           │
│                                                         │
│  Dependency Injection                                   │
│  ├─ get_db()             (Database connection)         │
│  ├─ get_cache()          (Redis client)                │
│  ├─ get_rate_limiter()   (Rate limiter)                │
│  └─ get_current_user()   (Auth - future)               │
└─────────────────────────────────────────────────────────┘
```

**Middleware Order (Important!):**

1. **CORS Middleware** - Must be first to handle preflight requests
2. **Rate Limiter** - Early rejection of over-limit requests
3. **Request Logger** - Log all requests (even rate-limited)
4. **Error Handler** - Catch and format errors
5. **Metrics Tracker** - Measure response times

---

### 3. Service Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Service Components                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Search Services                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SemanticSearchService                            │  │
│  │  • search(query, filters)                        │  │
│  │  • search_with_context(query)                    │  │
│  │  • get_similar_chunks(text)                      │  │
│  │                                                  │  │
│  │  Dependencies:                                    │  │
│  │  - EmbeddingService (Phase 3)                   │  │
│  │  - SupabaseService (Phase 3)                    │  │
│  │                                                  │  │
│  │  Performance: <100ms                             │  │
│  │  Cost: $0                                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ PerplexityService                                │  │
│  │  • rag_query(query, context, commodity)         │  │
│  │  • get_stats()                                   │  │
│  │  • reset_counter()                               │  │
│  │                                                  │  │
│  │  Performance: 2-5s                               │  │
│  │  Cost: $0.005/query                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Cache Services                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ CacheService                                     │  │
│  │  • get_cached_response(query_hash)              │  │
│  │  • cache_response(query_hash, data, ttl)        │  │
│  │  • get_cache_stats()                            │  │
│  │  • clear_cache()                                 │  │
│  │                                                  │  │
│  │  Redis Keys:                                     │  │
│  │  - rag:response:{hash}    (24h TTL)             │  │
│  │  - search:result:{hash}   (1h TTL)              │  │
│  │  - cache:hits             (counter)             │  │
│  │  - cache:misses           (counter)             │  │
│  │                                                  │  │
│  │  Expected Hit Rate: 50-60%                       │  │
│  │  Cost Savings: 40-60%                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Budget Services                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ BudgetService                                    │  │
│  │  • check_budget()                                │  │
│  │  • log_usage(query_type, cost)                  │  │
│  │  • get_monthly_stats()                          │  │
│  │  • send_alert(threshold)                        │  │
│  │                                                  │  │
│  │  Alert Thresholds: 50%, 80%, 90%, 95%          │  │
│  │  Budget Limit: 1000 queries/month                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ RateLimiterService                               │  │
│  │  • check_limits(session_id)                     │  │
│  │  • increment(session_id)                        │  │
│  │  • get_remaining(session_id)                    │  │
│  │                                                  │  │
│  │  Limits:                                         │  │
│  │  - Monthly: 1000 queries                        │  │
│  │  - Daily: 50 queries                            │  │
│  │  - Hourly: 5 queries (per session)              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Conversation Services                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ConversationService                              │  │
│  │  • save_message(session_id, query, response)    │  │
│  │  • get_history(session_id, limit, offset)       │  │
│  │  • search_history(session_id, query)            │  │
│  │  • delete_conversation(conversation_id)         │  │
│  │                                                  │  │
│  │  Storage: Supabase (conversation_history)       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Export Services                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ExportService                                    │  │
│  │  • to_pdf(conversation_id)                      │  │
│  │  • to_markdown(conversation_id)                 │  │
│  │  • to_csv(search_results)                       │  │
│  │                                                  │  │
│  │  Libraries:                                      │  │
│  │  - ReportLab (PDF)                              │  │
│  │  - Markdown (MD)                                │  │
│  │  - Pandas (CSV)                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Service Initialization:**

```python
# app/main.py (lifespan context)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global semantic_search, perplexity, cache, budget, rate_limiter

    # Initialize services
    semantic_search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(api_key=settings.perplexity_api_key)
    cache = CacheService(redis_client)
    budget = BudgetService(supabase, cache, email_config)
    rate_limiter = RateLimiterService(redis_client)

    # Store in app state
    app.state.semantic_search = semantic_search
    app.state.perplexity = perplexity
    app.state.cache = cache
    app.state.budget = budget
    app.state.rate_limiter = rate_limiter

    yield

    # Shutdown
    await redis_client.close()
```

---

## Data Flow

### Flow 1: Semantic Search (Free, Fast)

```
User Input
   │
   ▼
Streamlit Search Page
   │
   ▼ HTTP POST /api/v1/search
FastAPI Endpoint
   │
   ├─ Validate Request (Pydantic)
   ├─ Check Cache (Redis)
   │  ├─ Cache Hit ──────────────────┐
   │  └─ Cache Miss                  │
   │     │                            │
   │     ▼                            │
   │  Embed Query                     │
   │  (EmbeddingService)              │
   │     │                            │
   │     ▼                            │
   │  pgvector Search                 │
   │  (Supabase RPC)                  │
   │     │                            │
   │     ▼                            │
   │  Format Results                  │
   │     │                            │
   │     ▼                            │
   │  Cache Results (1h)              │
   │     │                            │
   │     └────────────────────────────┤
   │                                  │
   ▼                                  ▼
Log Usage                    Return Results
(usage_logs)                         │
   │                                  │
   └──────────────────────────────────┘
                    │
                    ▼
           Display in Streamlit
                    │
                    ▼
           User sees results
           + "Get AI Answer" button

Timeline:
- Cache hit: <50ms
- Cache miss: <150ms
  - Embed: 20ms
  - Search: 30ms
  - Format: 5ms
  - Cache: 5ms
```

---

### Flow 2: RAG Q&A (Paid, Slow)

```
User Clicks "Get AI Answer"
   │
   ▼
Streamlit Chat Page
   │
   ▼ HTTP POST /api/v1/rag/query
FastAPI Endpoint
   │
   ├─ Validate Request
   ├─ Check Budget Limit ───────────┐
   │  (BudgetService)                │ Over limit?
   │                                 ▼
   ├─ Check Rate Limit ─────────┐   Error 402
   │  (RateLimiterService)       │   (Budget exceeded)
   │                             ▼
   │                         Error 429
   │                         (Rate limited)
   │
   ├─ Check Cache (Redis)
   │  ├─ Cache Hit (query similarity >0.95)
   │  │  │
   │  │  └────────────────────────────┐
   │  │                                │
   │  └─ Cache Miss                    │
   │     │                             │
   │     ▼                             │
   │  Semantic Search                  │
   │  (get top 5 chunks)               │
   │     │                             │
   │     ▼                             │
   │  Format Context                   │
   │  (5 chunks → string)              │
   │     │                             │
   │     ▼                             │
   │  Perplexity API Call              │
   │  (sonar-pro model)                │
   │  2-5 seconds ⏱                    │
   │     │                             │
   │     ▼                             │
   │  Parse Response                   │
   │  (answer + citations)             │
   │     │                             │
   │     ▼                             │
   │  Cache Response (24h)             │
   │     │                             │
   │     ▼                             │
   │  Log Usage ($0.005)               │
   │  (conversation_history)           │
   │     │                             │
   │     ▼                             │
   │  Increment Counters               │
   │  (rate_limiter)                   │
   │     │                             │
   │     └─────────────────────────────┤
   │                                   │
   │                                   ▼
   └───────────────────────────> Return Answer
                                       │
                                       ▼
                              Display in Streamlit
                              (chat message + citations)

Timeline:
- Cache hit: <100ms
- Cache miss: 2-5 seconds
  - Search: 50ms
  - Context: 5ms
  - Perplexity: 2-5s
  - Parse: 10ms
  - Cache: 10ms
  - Log: 20ms
```

---

### Flow 3: Budget Monitoring (Background)

```
Every Query (Search or RAG)
   │
   ▼
Log Usage
(usage_logs table)
   │
   ▼
Check Budget
(BudgetService.check_budget)
   │
   ├─ Get current month usage
   ├─ Calculate utilization %
   └─ Compare to thresholds
      │
      ├─ <50% ──────> No action
      │
      ├─ 50-79% ────> Check if alert sent
      │                  │
      │                  ├─ Yes ──> No action
      │                  └─ No ──> Send email
      │                             "50% budget used"
      │
      ├─ 80-89% ────> Send alert
      │                "80% budget used"
      │
      ├─ 90-94% ────> Send alert
      │                "90% budget used"
      │
      └─ 95-100% ───> Send alert
                       "95% budget used"
                       + Notify in UI

Alert Storage:
- Redis: alert:sent:{threshold}
- TTL: End of month
- Prevents duplicate alerts
```

---

## Technology Stack

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **UI Framework** | Streamlit | 1.29+ | Web interface |
| **Navigation** | streamlit-option-menu | 0.3+ | Page navigation |
| **Charts** | Plotly | 5.18+ | Usage charts |
| **Data Grids** | streamlit-aggrid | 0.3+ | Table display |
| **HTTP Client** | httpx | 0.25+ | API calls |

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.104+ | API layer |
| **ASGI Server** | Uvicorn | 0.24+ | HTTP server |
| **Validation** | Pydantic | 2.5+ | Request validation |
| **Database Client** | Supabase Python | 2.0+ | Database access |
| **Cache** | Redis | 7.0+ | Caching layer |
| **Cache Client** | redis-py | 5.0+ | Redis client |

### AI/ML Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Embedding Model** | multilingual-e5-large | - | Text embeddings |
| **Embedding Library** | sentence-transformers | 2.2+ | Model inference |
| **RAG LLM** | Perplexity sonar-pro | API | Q&A generation |
| **Vector Search** | pgvector (Supabase) | 0.5+ | Similarity search |

### DevOps Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Containerization** | Docker | 24+ | Deployment |
| **Orchestration** | Docker Compose | 2.23+ | Multi-container |
| **Reverse Proxy** | Nginx | 1.24+ | HTTP routing |
| **CI/CD** | GitHub Actions | - | Auto-deploy |

---

## Integration Points

### 1. Streamlit ↔ FastAPI

**Protocol:** HTTP/JSON

**Authentication:** Session ID (for now)

**Request Format:**
```python
# Streamlit calls FastAPI
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/search",
        json={
            "query": "cashew production",
            "top_k": 5,
            "session_id": st.session_state.session_id
        }
    )

    data = response.json()
```

**Error Handling:**
```python
try:
    response = await client.post(...)
    response.raise_for_status()
    data = response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        st.error("Rate limit exceeded. Please try again later.")
    elif e.response.status_code == 402:
        st.error("Budget limit reached. Contact administrator.")
    else:
        st.error(f"Error: {e}")
```

---

### 2. FastAPI ↔ Supabase

**Protocol:** PostgREST + pgvector RPC

**Connection:**
```python
from supabase import create_client

supabase = create_client(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_key
)
```

**Read (SELECT):**
```python
# Get conversation history
result = await supabase.table("conversation_history") \
    .select("*") \
    .eq("session_id", session_id) \
    .order("created_at", desc=True) \
    .limit(20) \
    .execute()

conversations = result.data
```

**Write (INSERT):**
```python
# Save conversation
await supabase.table("conversation_history") \
    .insert({
        "session_id": session_id,
        "query_text": query,
        "query_type": "rag",
        "response_text": response,
        "cost_usd": 0.005
    }) \
    .execute()
```

**RPC (pgvector search):**
```python
# Semantic search
result = await supabase.rpc(
    "match_documents",
    {
        "query_embedding": embedding,
        "match_count": 5,
        "match_threshold": 0.7
    }
).execute()

chunks = result.data
```

---

### 3. FastAPI ↔ Redis

**Protocol:** Redis protocol (RESP)

**Connection:**
```python
import redis.asyncio as redis

redis_client = await redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)
```

**Cache Operations:**
```python
# Set with TTL
await redis_client.setex(
    key="rag:response:abc123",
    time=86400,  # 24 hours
    value=json.dumps(response)
)

# Get
cached = await redis_client.get("rag:response:abc123")
if cached:
    response = json.loads(cached)

# Increment counter
await redis_client.incr("rate_limit:month:2024-12")

# Get with expiry
count = await redis_client.get("rate_limit:month:2024-12")
ttl = await redis_client.ttl("rate_limit:month:2024-12")
```

---

### 4. FastAPI ↔ Perplexity API

**Protocol:** HTTPS/JSON

**Authentication:** Bearer token

**Request:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are..."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "return_citations": True
        }
    )

    data = response.json()
    answer = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
```

---

## Database Schema

### Table: conversation_history

**Purpose:** Store all user queries and responses

```sql
CREATE TABLE conversation_history (
    -- Primary key
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification
    session_id TEXT NOT NULL,
    user_id TEXT,

    -- Query details
    query_text TEXT NOT NULL,
    query_language TEXT CHECK (query_language IN ('en', 'km', 'vi')),
    query_type TEXT NOT NULL CHECK (query_type IN ('search', 'rag')),
    commodity TEXT CHECK (commodity IN ('cashew', 'rubber')),

    -- Response details
    response_text TEXT,
    sources JSONB,
    context_chunks JSONB,

    -- Performance metrics
    search_time_ms INTEGER,
    rag_time_ms INTEGER,
    total_time_ms INTEGER,

    -- Cost tracking
    cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    cache_hit BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_conversation_session ON conversation_history(session_id);
CREATE INDEX idx_conversation_created ON conversation_history(created_at DESC);
CREATE INDEX idx_conversation_type ON conversation_history(query_type);
CREATE INDEX idx_conversation_cost ON conversation_history(cost_usd) WHERE cost_usd > 0;
```

**Row Size:** ~1-5 KB (depending on response length)

**Estimated Growth:** 1000 queries/month × 3 KB = 3 MB/month

---

### Table: usage_logs

**Purpose:** Track API usage for analytics

```sql
CREATE TABLE usage_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    log_date DATE GENERATED ALWAYS AS (logged_at::DATE) STORED,

    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    session_id TEXT,
    query_hash TEXT,

    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,

    cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    cache_hit BOOLEAN DEFAULT FALSE,

    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_usage_date ON usage_logs(log_date DESC);
CREATE INDEX idx_usage_endpoint ON usage_logs(endpoint);
CREATE INDEX idx_usage_session ON usage_logs(session_id);
```

---

### View: v_monthly_budget

**Purpose:** Aggregate budget statistics

```sql
CREATE VIEW v_monthly_budget AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*) AS total_queries,
    COUNT(*) FILTER (WHERE query_type = 'rag') AS rag_queries,
    COUNT(*) FILTER (WHERE query_type = 'search') AS search_queries,
    SUM(cost_usd) AS total_cost,
    AVG(cost_usd) FILTER (WHERE cost_usd > 0) AS avg_cost_per_rag,
    COUNT(*) FILTER (WHERE cache_hit = true) AS cache_hits,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cache_hit = true) / NULLIF(COUNT(*), 0), 2) AS cache_hit_rate
FROM conversation_history
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;
```

**Usage:**
```sql
-- Get current month stats
SELECT * FROM v_monthly_budget
WHERE month = DATE_TRUNC('month', NOW());
```

---

## API Design

### RESTful Principles

1. **Resource-based URLs:** `/api/v1/rag/query` (not `/api/v1/getRagQuery`)
2. **HTTP verbs:** POST for mutations, GET for reads
3. **Status codes:** 200 (OK), 400 (Bad Request), 429 (Rate Limited), 500 (Error)
4. **JSON responses:** Consistent structure
5. **Versioning:** `/api/v1/` prefix for future compatibility

### Request/Response Format

**Standard Response:**
```json
{
  "status": "success",
  "data": { ... },
  "metadata": {
    "timestamp": "2024-12-27T10:30:45Z",
    "request_id": "req_abc123",
    "response_time_ms": 47
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 5 queries/hour",
    "details": {
      "limit": 5,
      "window": "1 hour",
      "retry_after": "2024-12-27T11:00:00Z"
    }
  },
  "metadata": {
    "timestamp": "2024-12-27T10:30:45Z",
    "request_id": "req_abc123"
  }
}
```

---

## Caching Strategy

### Cache Layers

```
┌─────────────────────────────────────────────┐
│           Cache Layer Strategy              │
├─────────────────────────────────────────────┤
│                                             │
│  Layer 1: Browser Cache (Future)            │
│  • Static assets (JS, CSS, images)         │
│  • TTL: 1 week                              │
│                                             │
│  Layer 2: Redis Cache (Phase 4)             │
│  ├─ RAG Responses                           │
│  │  • Key: rag:response:{hash}             │
│  │  • TTL: 24 hours                        │
│  │  • Hit rate: 50-60%                     │
│  │                                         │
│  ├─ Semantic Search Results                │
│  │  • Key: search:result:{hash}            │
│  │  • TTL: 1 hour                          │
│  │  • Hit rate: 40-50%                     │
│  │                                         │
│  └─ Session Data                            │
│     • Key: session:{id}                    │
│     • TTL: 7 days                           │
│                                             │
│  Layer 3: Database (Persistent)             │
│  • conversation_history (forever)           │
│  • usage_logs (1 year retention)           │
└─────────────────────────────────────────────┘
```

### Cache Key Generation

```python
def _query_hash(query: str, commodity: str, filters: dict) -> str:
    """Generate deterministic cache key."""
    # Normalize query
    normalized = query.lower().strip()

    # Create key string
    key_parts = [
        normalized,
        commodity or "all",
        json.dumps(filters, sort_keys=True)
    ]
    key_str = ":".join(key_parts)

    # Hash
    return hashlib.md5(key_str.encode()).hexdigest()
```

**Examples:**
- `rag:response:a1b2c3d4` (exact match)
- `search:result:e5f6g7h8` (filters differ = different hash)

### Cache Invalidation

**When to invalidate:**
1. Manual clear (admin action)
2. Monthly reset (budget tracking)
3. TTL expiry (automatic)

**When NOT to invalidate:**
- New documents added (old results still valid)
- Model update (Phase 5)

---

## Security Architecture

### 1. API Key Protection

```
┌─────────────────────────────────────────────┐
│         API Key Security Model              │
├─────────────────────────────────────────────┤
│                                             │
│  ❌ Frontend (NEVER store keys here)        │
│  • User's browser                           │
│  • Streamlit client-side code              │
│                                             │
│  ✅ Backend (Store keys here)               │
│  • Environment variables (.env)            │
│  • Docker secrets                          │
│  • Cloud secrets manager                   │
│                                             │
│  Access Flow:                               │
│  1. Frontend → Backend (public endpoint)   │
│  2. Backend → Perplexity (with API key)    │
│  3. Backend → Frontend (response)          │
│                                             │
│  Key Rotation:                              │
│  • Store in env vars: PERPLEXITY_API_KEY   │
│  • Update .env file                         │
│  • Restart services (no code change)       │
└─────────────────────────────────────────────┘
```

### 2. Input Sanitization

```python
# Bad: SQL injection vulnerable
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# Good: Parameterized query
query = "SELECT * FROM users WHERE name = $1"
result = await db.execute(query, user_input)

# Pydantic validation
class RAGQuery(BaseModel):
    query: str = Field(min_length=3, max_length=500)

    @validator('query')
    def sanitize_query(cls, v):
        dangerous = ['--', ';', 'DROP', 'DELETE']
        for char in dangerous:
            if char in v.upper():
                raise ValueError("Invalid query")
        return v.strip()
```

### 3. Rate Limiting

**Three-tier protection:**
1. **Monthly:** 1000 queries (Perplexity hard limit)
2. **Daily:** 50 queries (prevent monthly burn)
3. **Hourly:** 5 queries per session (prevent abuse)

**Implementation:** Redis counters with TTL

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  ui:
    build: ./ui
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

### Production (VPS)

```
┌─────────────────────────────────────────────┐
│              Nginx (Port 80/443)            │
│  • SSL/TLS termination                      │
│  • Reverse proxy                            │
│  • Static file serving                      │
└─────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐   ┌───────────────┐
│  Streamlit    │   │   FastAPI     │
│  (Port 8501)  │   │  (Port 8000)  │
│  • UI Server  │   │  • API Server │
└───────────────┘   └───────────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌───────────────┐
        │     Redis     │
        │  (Port 6379)  │
        └───────────────┘
```

---

**End of Architecture Document**

**Next:** See BUDGET_ANALYSIS.md for cost projections
