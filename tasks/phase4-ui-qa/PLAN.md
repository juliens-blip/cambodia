# Phase 4: User Interface for Q&A System - Complete Implementation Plan

**Project:** Cambodia Agricultural Intelligence Platform
**Phase:** 4 - UI & API Layer
**Date:** December 27, 2024
**Status:** Ready for Implementation
**Duration:** 19-27 hours (2-3 days)

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [API Specifications](#api-specifications)
5. [UI Components](#ui-components)
6. [Database Schema](#database-schema)
7. [Budget Management](#budget-management)
8. [Security Considerations](#security-considerations)
9. [Implementation Phases](#implementation-phases)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)

---

## Overview

### Goals

Build a production-ready web interface and API layer that makes the Phase 3 semantic search and RAG system accessible to end users while staying within the $5/month Perplexity budget.

### Target Users

1. **Farmers** (Primary)
   - Need: Simple Q&A in Khmer about cashew/rubber farming
   - Device: Mobile phone (Android)
   - Technical skill: Low
   - Usage: 5-10 queries/week

2. **Agricultural Analysts** (Secondary)
   - Need: Research capabilities in English/Khmer
   - Device: Laptop/Desktop
   - Technical skill: Medium
   - Usage: 20-50 queries/week

3. **Administrators** (Power Users)
   - Need: System monitoring and budget management
   - Device: Desktop
   - Technical skill: High
   - Usage: Daily monitoring, occasional queries

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Search latency | <100ms | API response time |
| RAG latency | <5 seconds | End-to-end response |
| Mobile usability | 90%+ satisfaction | User testing |
| Monthly cost | <$5 | Perplexity usage tracking |
| Cache hit rate | >50% | Redis metrics |
| Error rate | <1% | API logs |

---

## Technology Stack

### Decision Matrix

| Technology | Purpose | Alternatives Considered | Decision |
|------------|---------|-------------------------|----------|
| **Streamlit** | UI Framework | React, HTML/JS | ✅ Selected (Python-native, rapid dev) |
| **FastAPI** | API Layer | Flask, Django | ✅ Already in use |
| **Redis** | Caching | Memcached, in-memory dict | ✅ Selected (persistence + advanced features) |
| **Supabase** | Database | PostgreSQL, MongoDB | ✅ Already in use |
| **Docker** | Deployment | K8s, bare metal | ✅ Selected (simplicity + portability) |

### Why Streamlit?

**Pros:**
- Python-native (no context switching)
- Rapid development (5x faster than React)
- Built-in components (charts, file upload, etc.)
- Automatic reactivity (no state management complexity)
- Perfect for data apps
- Easy deployment (Streamlit Cloud free)
- Good mobile support (responsive by default)

**Cons:**
- Limited customization (compared to React)
- Not ideal for complex UX flows
- Session state can be tricky

**Verdict:** Pros outweigh cons for MVP. Can migrate to React later if needed.

### Dependencies to Add

```txt
# UI Framework
streamlit>=1.29.0
streamlit-option-menu>=0.3.6  # Navigation menu
streamlit-extras>=0.3.5       # Additional components

# Caching
redis>=5.0.0
hiredis>=2.2.3                # C-based parser (faster)

# Markdown/PDF Export
reportlab>=4.0.7              # PDF generation
markdown>=3.5.0               # Markdown rendering

# UI Enhancements
plotly>=5.18.0                # Interactive charts
streamlit-aggrid>=0.3.4       # Advanced data grids
```

---

## System Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                      Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Mobile    │  │   Desktop   │  │   Tablet    │           │
│  │  (Android)  │  │  (Chrome)   │  │   (iPad)    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│         │                │                │                     │
│         └────────────────┴────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTPS
┌────────────────────────────────────────────────────────────────┐
│                   Presentation Layer                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Streamlit UI Server (Port 8501)                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │ │
│  │  │ Search Page  │  │  Chat Page   │  │  History Page │ │ │
│  │  └──────────────┘  └──────────────┘  └───────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐                    │ │
│  │  │  Admin Page  │  │ Export Utils │                    │ │
│  │  └──────────────┘  └──────────────┘                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTP/JSON
┌────────────────────────────────────────────────────────────────┐
│                    Application Layer                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         FastAPI Server (Port 8000)                       │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │            Middleware Stack                      │   │ │
│  │  │  - CORS                                          │   │ │
│  │  │  - Rate Limiter (1000/month, 50/day, 5/hour)   │   │ │
│  │  │  - Request Logger                               │   │ │
│  │  │  - Error Handler                                │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │         API Endpoints (v1)                       │   │ │
│  │  │  POST   /api/v1/search                          │   │ │
│  │  │  POST   /api/v1/rag/query                       │   │ │
│  │  │  GET    /api/v1/history                         │   │ │
│  │  │  POST   /api/v1/history/{id}                    │   │ │
│  │  │  GET    /api/v1/stats                           │   │ │
│  │  │  GET    /api/v1/stats/budget                    │   │ │
│  │  │  POST   /api/v1/cache/clear                     │   │ │
│  │  │  GET    /api/v1/health                          │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                    Service Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │   Semantic      │  │   Perplexity    │  │     Cache     │ │
│  │   Search        │  │   RAG Service   │  │   Service     │ │
│  │   Service       │  │                 │  │   (Redis)     │ │
│  │   (<100ms)      │  │   (2-5s)        │  │   (24h TTL)   │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │   Budget        │  │   Conversation  │  │   Export      │ │
│  │   Service       │  │   Service       │  │   Service     │ │
│  │   (tracking)    │  │   (history)     │  │   (PDF/MD)    │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                     Data Layer                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Supabase PostgreSQL                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ document_        │  │ conversation_    │            │  │
│  │  │ embeddings       │  │ history          │            │  │
│  │  │ (146 chunks)     │  │ (new)            │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ usage_logs       │  │ cache_keys       │            │  │
│  │  │ (new)            │  │ (metadata only)  │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                Redis Cache                              │  │
│  │  - RAG responses (24h TTL)                             │  │
│  │  - Semantic search results (1h TTL)                    │  │
│  │  - Session data (7d TTL)                               │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│              Semantic Search Flow (Free)                      │
└──────────────────────────────────────────────────────────────┘

User Query
    │
    ▼
Check Cache (Redis)
    │
    ├─ Cache Hit ──────────────────────┐
    │                                   │
    └─ Cache Miss                       │
        │                               │
        ▼                               │
    Embed Query (20ms)                  │
        │                               │
        ▼                               │
    pgvector Search (30ms)              │
        │                               │
        ▼                               │
    Format Results                      │
        │                               │
        ▼                               │
    Cache Results (1h TTL)              │
        │                               │
        └───────────────────────────────┤
                                        │
                                        ▼
                            Return Results to User


┌──────────────────────────────────────────────────────────────┐
│            RAG Q&A Flow ($0.005 per query)                    │
└──────────────────────────────────────────────────────────────┘

User Query
    │
    ▼
Check Budget Limit
    │
    ├─ Over Limit ─────> Error: Budget exceeded
    │
    └─ Within Limit
        │
        ▼
    Check Cache (query similarity > 0.95)
        │
        ├─ Cache Hit ────────────────────┐
        │                                 │
        └─ Cache Miss                     │
            │                             │
            ▼                             │
        Semantic Search (50ms)            │
            │                             │
            ▼                             │
        Format Context (5ms)              │
            │                             │
            ▼                             │
        Perplexity API (2-5s)             │
            │                             │
            ▼                             │
        Log Usage (query_count++)         │
            │                             │
            ▼                             │
        Save to Conversation History      │
            │                             │
            ▼                             │
        Cache Response (24h TTL)          │
            │                             │
            └─────────────────────────────┤
                                          │
                                          ▼
                            Return AI Answer + Citations
```

---

## API Specifications

### Endpoint: POST /api/v1/search

**Purpose:** Semantic search across document embeddings (free, fast)

**Request:**
```json
{
  "query": "ការផលិតស្វាយចន្ទី",
  "top_k": 5,
  "commodity": "cashew",
  "source": null,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "query": "ការផលិតស្វាយចន្ទី",
  "results_count": 5,
  "search_time_ms": 47,
  "cache_hit": false,
  "results": [
    {
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_text": "Cambodia cashew production reached 5,200 tons...",
      "similarity": 0.8538,
      "metadata": {
        "source": "GDrive",
        "commodity": "cashew",
        "title": "iTrade Cashew Bulletin Q4 2024",
        "url": "https://drive.google.com/...",
        "chunk_index": 2,
        "total_chunks": 7
      }
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query parameter
- `500 Internal Server Error`: Search service failure

---

### Endpoint: POST /api/v1/rag/query

**Purpose:** RAG question answering with Perplexity ($0.005/query)

**Request:**
```json
{
  "query": "What are the best provinces for cashew farming in Cambodia?",
  "commodity": "cashew",
  "language": "en",
  "use_cache": true,
  "session_id": "user123_session456"
}
```

**Response:**
```json
{
  "query": "What are the best provinces for cashew farming in Cambodia?",
  "answer": "According to the iTrade Bulletin (local document), the best provinces for cashew farming in Cambodia are:\n\n1. Kampong Thom (5,200 tons/year)\n2. Kampong Cham (3,800 tons/year)\n3. Kratie (2,100 tons/year)\n\nThese provinces have suitable soil conditions and established processing facilities.",
  "sources": {
    "local": [
      {
        "title": "iTrade Cashew Bulletin Q4 2024",
        "source": "GDrive",
        "similarity": 0.8538,
        "excerpt": "Kampong Thom province produces..."
      }
    ],
    "external": [
      {
        "title": "Cambodia Agricultural Statistics 2024",
        "url": "https://www.maff.gov.kh/...",
        "citation_index": 1
      }
    ]
  },
  "metadata": {
    "model": "sonar-pro",
    "response_time_ms": 3245,
    "cache_hit": false,
    "context_chunks": 5,
    "perplexity_tokens": 487,
    "cost_usd": 0.005,
    "remaining_budget": 995
  },
  "conversation_id": "conv_abc123"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query
- `429 Too Many Requests`: Rate limit exceeded
- `402 Payment Required`: Budget limit reached
- `500 Internal Server Error`: Service failure

---

### Endpoint: GET /api/v1/history

**Purpose:** Get conversation history for a user/session

**Query Parameters:**
- `session_id` (required): User session identifier
- `limit` (optional, default=20): Number of conversations
- `offset` (optional, default=0): Pagination offset

**Response:**
```json
{
  "session_id": "user123_session456",
  "total_conversations": 47,
  "conversations": [
    {
      "conversation_id": "conv_abc123",
      "query": "Best provinces for cashew?",
      "answer_preview": "According to the iTrade Bulletin...",
      "created_at": "2024-12-27T10:30:45Z",
      "query_type": "rag",
      "cost_usd": 0.005
    }
  ]
}
```

---

### Endpoint: GET /api/v1/stats

**Purpose:** System usage statistics (admin only)

**Response:**
```json
{
  "period": "current_month",
  "budget": {
    "total_queries": 456,
    "rag_queries": 123,
    "search_queries": 333,
    "total_cost_usd": 0.615,
    "budget_limit_usd": 5.00,
    "utilization_percent": 12.3,
    "remaining_queries": 877,
    "days_remaining": 15
  },
  "cache": {
    "hit_rate_percent": 62.4,
    "total_requests": 456,
    "cache_hits": 284,
    "cache_misses": 172,
    "cost_saved_usd": 1.42
  },
  "performance": {
    "avg_search_latency_ms": 47,
    "avg_rag_latency_ms": 3245,
    "p95_search_latency_ms": 89,
    "p95_rag_latency_ms": 4872
  },
  "top_queries": [
    {
      "query": "cashew production statistics",
      "count": 23,
      "avg_similarity": 0.84
    }
  ]
}
```

---

### Endpoint: GET /api/v1/health

**Purpose:** Health check for monitoring

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-27T10:30:45Z",
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 12
    },
    "redis": {
      "status": "up",
      "latency_ms": 3
    },
    "embedding_service": {
      "status": "up",
      "model_loaded": true
    },
    "perplexity": {
      "status": "up",
      "last_check": "2024-12-27T10:28:00Z"
    }
  }
}
```

---

## UI Components

### Page Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Header (Persistent)                  │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│  │ Search │  │  Chat  │  │History │  │ Admin  │       │
│  └────────┘  └────────┘  └────────┘  └────────┘       │
│                                                         │
│  Language: [EN] [KH] [VI]      User: admin             │
└─────────────────────────────────────────────────────────┘
│                                                         │
│                   Main Content Area                     │
│                   (Page-specific)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
│                    Footer (Persistent)                  │
│  Budget: 456/1000 queries (45.6%) | Cache: 62% hit     │
└─────────────────────────────────────────────────────────┘
```

### 1. Search Page (Default)

**Purpose:** Fast semantic search without Perplexity (free)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Search Agricultural Documents                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Search query... (Khmer/English/Vietnamese)        │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Commodity: [All ▼] [Cashew] [Rubber]                  │
│  Source: [All ▼] [GDrive] [ODC] [MEF]                  │
│  Results: [5 ▼] [10] [20]                              │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Results (5 found in 47ms)                         │ │
│  │                                                   │ │
│  │ ┌─────────────────────────────────────────────┐ │ │
│  │ │ [📄] iTrade Cashew Bulletin Q4 2024        │ │ │
│  │ │ Similarity: 85.4%  Source: GDrive          │ │ │
│  │ │                                             │ │ │
│  │ │ Cambodia cashew production reached 5,200   │ │ │
│  │ │ tons in Kampong Thom province...           │ │ │
│  │ │                                             │ │ │
│  │ │ [View Full] [Get AI Answer 💡]             │ │ │
│  │ └─────────────────────────────────────────────┘ │ │
│  │                                                   │ │
│  │ ┌─────────────────────────────────────────────┐ │ │
│  │ │ [📄] ODC Agricultural Report 2023          │ │ │
│  │ │ ...                                         │ │ │
│  │ └─────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time search (debounced 300ms)
- Filter by commodity, source
- Adjustable result count
- Similarity score visualization
- One-click RAG upgrade ("Get AI Answer")
- Export results to CSV/PDF

**Code Structure:**
```python
# ui/pages/search.py
import streamlit as st
from app.services.semantic_search_service import SemanticSearchService

def render_search_page():
    st.title("🔍 Search Agricultural Documents")

    # Input
    query = st.text_input("Search query", placeholder="ការផលិតស្វាយចន្ទី...")
    col1, col2, col3 = st.columns(3)
    commodity = col1.selectbox("Commodity", ["All", "Cashew", "Rubber"])
    source = col2.selectbox("Source", ["All", "GDrive", "ODC", "MEF"])
    top_k = col3.selectbox("Results", [5, 10, 20])

    if query:
        with st.spinner("Searching..."):
            results = search_service.search(
                query=query,
                commodity=commodity if commodity != "All" else None,
                source=source if source != "All" else None,
                top_k=top_k
            )

        st.success(f"Found {len(results)} results in {results['search_time_ms']}ms")

        for result in results:
            with st.expander(f"{result['metadata']['title']} ({result['similarity']*100:.1f}%)"):
                st.write(result['chunk_text'])

                col1, col2 = st.columns(2)
                if col1.button("View Full", key=result['chunk_id']):
                    # Navigate to full document view
                    pass

                if col2.button("Get AI Answer 💡", key=f"rag_{result['chunk_id']}"):
                    # Trigger RAG query
                    st.session_state.rag_query = query
                    st.switch_page("pages/chat.py")
```

---

### 2. Chat Page (RAG Q&A)

**Purpose:** AI-powered Q&A with citations ($0.005/query)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  AI Assistant (RAG-powered)                             │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 💬 Conversation                                   │ │
│  │                                                   │ │
│  │ You: What are the best provinces for cashew?     │ │
│  │                                                   │ │
│  │ AI: According to the iTrade Bulletin (local      │ │
│  │ document), the best provinces are:               │ │
│  │                                                   │ │
│  │ 1. Kampong Thom (5,200 tons/year)               │ │
│  │ 2. Kampong Cham (3,800 tons/year)               │ │
│  │ 3. Kratie (2,100 tons/year)                      │ │
│  │                                                   │ │
│  │ 📚 Sources:                                       │ │
│  │ • iTrade Cashew Bulletin Q4 2024 (85% match)    │ │
│  │ • Cambodia Agricultural Statistics 2024          │ │
│  │                                                   │ │
│  │ [📥 Export] [🔖 Save] [↻ Regenerate]             │ │
│  │                                                   │ │
│  │ You: Tell me more about Kampong Thom...          │ │
│  │                                                   │ │
│  │ AI: (typing...)                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Type your question... (Khmer/English/Vietnamese) │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  [Send] [Clear Conversation]                           │
│                                                         │
│  ⚠️ This uses Perplexity API ($0.005/query)            │
│     Budget: 456/1000 queries (45.6%)                   │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Chat interface with conversation history
- Context-aware follow-up questions
- Citation display (local + external)
- Export conversation to PDF/Markdown
- Cost tracking per query
- Budget warning at 80%

**Code Structure:**
```python
# ui/pages/chat.py
import streamlit as st
from app.services.perplexity_service import PerplexityService
from app.services.semantic_search_service import SemanticSearchService

def render_chat_page():
    st.title("💬 AI Assistant")

    # Initialize conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display conversation
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for source in msg["sources"]:
                        st.write(f"- {source['title']} ({source['similarity']*100:.1f}%)")

    # Input
    if prompt := st.chat_input("Ask a question..."):
        # Check budget
        stats = budget_service.get_stats()
        if stats['remaining_queries'] < 1:
            st.error("Budget limit reached! Please wait until next month.")
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get RAG response
        with st.spinner("Thinking..."):
            # 1. Semantic search for context
            context = search_service.search_with_context(prompt, top_k=5)

            # 2. RAG query
            response = perplexity_service.rag_query(
                query=prompt,
                retrieved_context=context,
                commodity="cashew"  # TODO: detect from query
            )

        # Add AI message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response['response_text'],
            "sources": response['sources'],
            "cost": response['metadata']['cost_usd']
        })

        # Save to conversation history
        conversation_service.save_message(
            session_id=st.session_state.session_id,
            query=prompt,
            response=response
        )

        st.rerun()
```

---

### 3. History Page

**Purpose:** View past conversations and queries

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Conversation History                                   │
│                                                         │
│  Filter: [All ▼] [Today] [This Week] [This Month]      │
│  Search: [Search conversations...]                     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Dec 27, 2024 - 10:30 AM                          │ │
│  │ Q: What are the best provinces for cashew?       │ │
│  │ A: According to the iTrade Bulletin...           │ │
│  │ Type: RAG | Cost: $0.005 | Sources: 5            │ │
│  │ [View Full] [Re-ask] [Export] [Delete]           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Dec 27, 2024 - 09:15 AM                          │ │
│  │ Q: ការផលិតស្វាយចន្ទី                              │ │
│  │ Results: 5 documents found                        │ │
│  │ Type: Search | Cost: Free                         │ │
│  │ [View Full] [Re-search] [Export]                 │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  [Load More] [Export All to PDF]                       │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Chronological list of queries
- Filter by date range
- Search within history
- Re-run past queries
- Export individual or all conversations
- Delete conversations

---

### 4. Admin Page (Power Users)

**Purpose:** Monitor system usage and manage budget

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Admin Dashboard                                        │
│                                                         │
│  ┌───────────────────────────┐  ┌──────────────────┐  │
│  │ Budget Status             │  │ Cache Stats      │  │
│  │                           │  │                  │  │
│  │ [████████░░░░░░░░░] 45.6% │  │ Hit Rate: 62.4%  │  │
│  │                           │  │ Saved: $1.42     │  │
│  │ Used: 456/1000 queries    │  │ Hits: 284        │  │
│  │ Cost: $0.62/$5.00         │  │ Misses: 172      │  │
│  │ Remaining: 15 days        │  │                  │  │
│  └───────────────────────────┘  └──────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Query Distribution (This Month)                   │ │
│  │                                                   │ │
│  │ ██████████████████ Semantic Search (73%)          │ │
│  │ ████████ RAG Queries (27%)                        │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Top Queries                                       │ │
│  │                                                   │ │
│  │ 1. cashew production statistics (23 queries)     │ │
│  │ 2. rubber export restrictions (18 queries)       │ │
│  │ 3. ការដាំស្វាយចន្ទី (15 queries)                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Performance Metrics                               │ │
│  │                                                   │ │
│  │ Avg Search Latency: 47ms (p95: 89ms)            │ │
│  │ Avg RAG Latency: 3.2s (p95: 4.9s)               │ │
│  │ Error Rate: 0.2% (1/456 queries)                 │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Actions                                           │ │
│  │                                                   │ │
│  │ [Clear Cache] [Export Logs] [Reset Counter]      │ │
│  │ [Configure Alerts] [Download Report]             │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time budget tracking
- Cache performance visualization
- Top queries analysis
- Performance metrics (latency, error rate)
- Admin actions (clear cache, export logs)
- Email alert configuration

---

## Database Schema

### 1. conversation_history Table

**Purpose:** Store user conversations for history and analysis

```sql
CREATE TABLE conversation_history (
    -- Primary key
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification
    session_id TEXT NOT NULL,
    user_id TEXT,  -- Optional authenticated user

    -- Query details
    query_text TEXT NOT NULL,
    query_language TEXT,  -- 'en', 'km', 'vi'
    query_type TEXT NOT NULL,  -- 'search', 'rag'
    commodity TEXT,  -- 'cashew', 'rubber', NULL

    -- Response details
    response_text TEXT,  -- NULL for semantic search
    sources JSONB,  -- {local: [...], external: [...]}
    context_chunks JSONB,  -- Array of chunk IDs used

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
    user_agent TEXT,

    -- Indexing
    CONSTRAINT valid_query_type CHECK (query_type IN ('search', 'rag'))
);

-- Indexes
CREATE INDEX idx_conversation_session ON conversation_history(session_id);
CREATE INDEX idx_conversation_created ON conversation_history(created_at DESC);
CREATE INDEX idx_conversation_type ON conversation_history(query_type);
CREATE INDEX idx_conversation_cost ON conversation_history(cost_usd) WHERE cost_usd > 0;
```

**Example Row:**
```sql
INSERT INTO conversation_history (
    session_id,
    query_text,
    query_language,
    query_type,
    commodity,
    response_text,
    sources,
    cost_usd,
    cache_hit
) VALUES (
    'user123_session456',
    'Best provinces for cashew farming?',
    'en',
    'rag',
    'cashew',
    'According to the iTrade Bulletin...',
    '{"local": [{"title": "iTrade Cashew Bulletin", "similarity": 0.85}], "external": []}',
    0.005,
    false
);
```

---

### 2. usage_logs Table

**Purpose:** Track API usage for budget management and analytics

```sql
CREATE TABLE usage_logs (
    -- Primary key
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Timestamp
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    log_date DATE GENERATED ALWAYS AS (logged_at::DATE) STORED,

    -- API endpoint
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,  -- 'GET', 'POST'

    -- Request details
    session_id TEXT,
    query_hash TEXT,  -- MD5 of query for deduplication

    -- Response details
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,

    -- Cost tracking
    cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    cache_hit BOOLEAN DEFAULT FALSE,

    -- Metadata
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_usage_date ON usage_logs(log_date DESC);
CREATE INDEX idx_usage_endpoint ON usage_logs(endpoint);
CREATE INDEX idx_usage_session ON usage_logs(session_id);
CREATE INDEX idx_usage_cost ON usage_logs(cost_usd) WHERE cost_usd > 0;

-- Partitioning by month (optional, for large scale)
-- CREATE TABLE usage_logs_2024_12 PARTITION OF usage_logs
--     FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
```

---

### 3. Migration Script

**File:** `supabase/migrations/005_conversation_history.sql`

```sql
-- Migration: Add conversation history and usage tracking
-- Date: 2024-12-27
-- Phase: 4 (UI & API)

BEGIN;

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversation_history table
CREATE TABLE conversation_history (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    user_id TEXT,
    query_text TEXT NOT NULL,
    query_language TEXT,
    query_type TEXT NOT NULL CHECK (query_type IN ('search', 'rag')),
    commodity TEXT,
    response_text TEXT,
    sources JSONB,
    context_chunks JSONB,
    search_time_ms INTEGER,
    rag_time_ms INTEGER,
    total_time_ms INTEGER,
    cost_usd DECIMAL(10, 6) DEFAULT 0.00,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_conversation_session ON conversation_history(session_id);
CREATE INDEX idx_conversation_created ON conversation_history(created_at DESC);
CREATE INDEX idx_conversation_type ON conversation_history(query_type);
CREATE INDEX idx_conversation_cost ON conversation_history(cost_usd) WHERE cost_usd > 0;

-- Create usage_logs table
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

CREATE INDEX idx_usage_date ON usage_logs(log_date DESC);
CREATE INDEX idx_usage_endpoint ON usage_logs(endpoint);
CREATE INDEX idx_usage_session ON usage_logs(session_id);
CREATE INDEX idx_usage_cost ON usage_logs(cost_usd) WHERE cost_usd > 0;

-- Create view for monthly budget summary
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

COMMIT;
```

---

## Budget Management

### 1. Rate Limiting Strategy

**Three-Tier Limits:**

```python
# app/middleware/rate_limiter.py
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import redis

class RateLimiter:
    """Multi-tier rate limiter for budget protection."""

    def __init__(self, redis_client):
        self.redis = redis_client

        # Limits
        self.MONTHLY_LIMIT = 1000  # Perplexity hard limit
        self.DAILY_LIMIT = 50      # 1000 / 20 days = 50/day
        self.HOURLY_LIMIT = 5      # Prevent abuse

    async def check_limits(self, session_id: str, endpoint: str) -> dict:
        """
        Check all rate limits.

        Returns:
            dict with 'allowed': bool and 'reason': str
        """
        now = datetime.utcnow()
        month_key = f"rate_limit:month:{now.year}-{now.month:02d}"
        day_key = f"rate_limit:day:{now.date()}"
        hour_key = f"rate_limit:hour:{session_id}:{now.hour}"

        # Check monthly limit
        monthly_count = self.redis.get(month_key) or 0
        if int(monthly_count) >= self.MONTHLY_LIMIT:
            return {
                'allowed': False,
                'reason': f"Monthly limit exceeded ({self.MONTHLY_LIMIT} queries/month)",
                'retry_after': self._get_next_month()
            }

        # Check daily limit
        daily_count = self.redis.get(day_key) or 0
        if int(daily_count) >= self.DAILY_LIMIT:
            return {
                'allowed': False,
                'reason': f"Daily limit exceeded ({self.DAILY_LIMIT} queries/day)",
                'retry_after': self._get_next_day()
            }

        # Check hourly limit (per session)
        hourly_count = self.redis.get(hour_key) or 0
        if int(hourly_count) >= self.HOURLY_LIMIT:
            return {
                'allowed': False,
                'reason': f"Hourly limit exceeded ({self.HOURLY_LIMIT} queries/hour)",
                'retry_after': self._get_next_hour()
            }

        return {'allowed': True}

    async def increment(self, session_id: str):
        """Increment all counters after successful query."""
        now = datetime.utcnow()
        month_key = f"rate_limit:month:{now.year}-{now.month:02d}"
        day_key = f"rate_limit:day:{now.date()}"
        hour_key = f"rate_limit:hour:{session_id}:{now.hour}"

        # Increment with expiry
        self.redis.incr(month_key)
        self.redis.expire(month_key, timedelta(days=32))  # Expire next month

        self.redis.incr(day_key)
        self.redis.expire(day_key, timedelta(days=2))  # Expire tomorrow

        self.redis.incr(hour_key)
        self.redis.expire(hour_key, timedelta(hours=2))  # Expire next hour
```

**Usage in API:**
```python
@router.post("/api/v1/rag/query")
async def rag_query(request: Request, query: RAGQuery):
    # Check rate limits
    rate_check = await rate_limiter.check_limits(
        session_id=query.session_id,
        endpoint="/rag/query"
    )

    if not rate_check['allowed']:
        raise HTTPException(
            status_code=429,
            detail={
                'error': 'Rate limit exceeded',
                'reason': rate_check['reason'],
                'retry_after': rate_check['retry_after']
            }
        )

    # Process query...
    response = await perplexity_service.rag_query(...)

    # Increment counter
    await rate_limiter.increment(query.session_id)

    return response
```

---

### 2. Query Caching

**Strategy:** Cache RAG responses for 24 hours, deduplicate similar queries

```python
# app/services/cache_service.py
import redis
import hashlib
import json
from typing import Optional

class CacheService:
    """Redis-based caching for RAG responses."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.TTL_SECONDS = 24 * 60 * 60  # 24 hours

    def _query_hash(self, query: str, commodity: str) -> str:
        """Generate cache key from query."""
        normalized = query.lower().strip()
        key_str = f"{normalized}:{commodity}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get_cached_response(
        self,
        query: str,
        commodity: str,
        similarity_threshold: float = 0.95
    ) -> Optional[dict]:
        """
        Get cached response if exists.

        Args:
            query: User query
            commodity: Commodity filter
            similarity_threshold: Min similarity for cache hit (0.95 = very similar)

        Returns:
            Cached response dict or None
        """
        query_hash = self._query_hash(query, commodity)
        cache_key = f"rag:response:{query_hash}"

        # Check exact match
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # TODO: Check fuzzy match using embeddings
        # For MVP, only exact matches

        return None

    async def cache_response(
        self,
        query: str,
        commodity: str,
        response: dict
    ):
        """Cache RAG response for 24 hours."""
        query_hash = self._query_hash(query, commodity)
        cache_key = f"rag:response:{query_hash}"

        self.redis.setex(
            cache_key,
            self.TTL_SECONDS,
            json.dumps(response)
        )

    async def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        # Get all cache keys
        keys = self.redis.keys("rag:response:*")

        # Count hits/misses from metadata
        hits = self.redis.get("cache:hits") or 0
        misses = self.redis.get("cache:misses") or 0
        total = int(hits) + int(misses)

        hit_rate = (int(hits) / total * 100) if total > 0 else 0

        return {
            'cached_responses': len(keys),
            'hits': int(hits),
            'misses': int(misses),
            'hit_rate_percent': round(hit_rate, 2),
            'estimated_savings_usd': int(hits) * 0.005
        }

    async def clear_cache(self):
        """Clear all cached responses (admin action)."""
        keys = self.redis.keys("rag:response:*")
        if keys:
            self.redis.delete(*keys)

        # Reset counters
        self.redis.set("cache:hits", 0)
        self.redis.set("cache:misses", 0)
```

**Integration in RAG endpoint:**
```python
@router.post("/api/v1/rag/query")
async def rag_query(request: Request, query: RAGQuery):
    # Check cache first
    cached = await cache_service.get_cached_response(
        query=query.query,
        commodity=query.commodity
    )

    if cached:
        # Cache hit - free!
        await cache_service.record_hit()
        cached['metadata']['cache_hit'] = True
        return cached

    # Cache miss - call Perplexity
    await cache_service.record_miss()

    # Get context
    context = await search_service.search_with_context(query.query)

    # RAG query
    response = await perplexity_service.rag_query(
        query=query.query,
        retrieved_context=context,
        commodity=query.commodity
    )

    # Cache response
    await cache_service.cache_response(
        query=query.query,
        commodity=query.commodity,
        response=response
    )

    response['metadata']['cache_hit'] = False
    return response
```

---

### 3. Budget Alerts

**Email Notifications:**

```python
# app/services/budget_service.py
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class BudgetService:
    """Monitor budget and send alerts."""

    def __init__(self, db, cache, email_config):
        self.db = db
        self.cache = cache
        self.email_config = email_config

        # Alert thresholds
        self.ALERT_THRESHOLDS = [0.5, 0.8, 0.9, 0.95]  # 50%, 80%, 90%, 95%
        self.BUDGET_LIMIT = 1000  # queries/month

    async def check_budget(self) -> dict:
        """
        Check current budget usage.

        Returns:
            dict with usage statistics
        """
        # Get current month's usage
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        result = await self.db.execute(
            """
            SELECT
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE query_type = 'rag') as rag_queries,
                SUM(cost_usd) as total_cost,
                COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits
            FROM conversation_history
            WHERE created_at >= $1
            """,
            month_start
        )

        row = result[0]

        utilization = (row['total_queries'] / self.BUDGET_LIMIT) * 100

        # Check if alert needed
        await self._check_alert_threshold(utilization)

        return {
            'total_queries': row['total_queries'],
            'rag_queries': row['rag_queries'],
            'search_queries': row['total_queries'] - row['rag_queries'],
            'total_cost': float(row['total_cost']),
            'budget_limit': self.BUDGET_LIMIT,
            'utilization_percent': round(utilization, 2),
            'remaining_queries': self.BUDGET_LIMIT - row['total_queries'],
            'cache_hits': row['cache_hits'],
            'cache_hit_rate': round((row['cache_hits'] / row['total_queries'] * 100), 2)
        }

    async def _check_alert_threshold(self, utilization: float):
        """Send email alert if threshold crossed."""
        for threshold in self.ALERT_THRESHOLDS:
            threshold_key = f"alert:sent:{int(threshold*100)}"

            if utilization >= (threshold * 100):
                # Check if alert already sent
                if not self.cache.get(threshold_key):
                    await self._send_alert_email(threshold, utilization)

                    # Mark as sent (expires end of month)
                    self.cache.setex(threshold_key, 30 * 24 * 60 * 60, "1")

    async def _send_alert_email(self, threshold: float, current: float):
        """Send budget alert email."""
        subject = f"⚠️ Budget Alert: {int(threshold*100)}% threshold reached"

        body = f"""
        Budget Alert - Cambodia Agri Analytics

        The Perplexity API budget has reached {int(threshold*100)}% utilization.

        Current Usage: {current:.1f}%
        Remaining Queries: {self.BUDGET_LIMIT - int(current/100 * self.BUDGET_LIMIT)}

        Actions:
        - Review usage dashboard: https://yourdomain.com/admin
        - Consider enabling stricter rate limits
        - Clear cache to reduce costs

        This is an automated alert.
        """

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_email']

        # Send email
        with smtplib.SMTP(self.email_config['smtp_host']) as server:
            server.send_message(msg)
```

---

## Security Considerations

### 1. API Key Protection

**Never expose Perplexity API key to frontend:**

```python
# ❌ BAD: Frontend calling Perplexity directly
# Frontend code (DON'T DO THIS):
# fetch('https://api.perplexity.ai/chat/completions', {
#     headers: { 'Authorization': `Bearer ${PERPLEXITY_KEY}` }
# })

# ✅ GOOD: Frontend calls backend, backend calls Perplexity
# Frontend:
response = await fetch('/api/v1/rag/query', {
    method: 'POST',
    body: JSON.stringify({ query: 'cashew farming' })
})

# Backend (FastAPI):
@router.post("/api/v1/rag/query")
async def rag_query(query: RAGQuery):
    # API key stored in environment variable
    response = await perplexity_service.rag_query(
        query=query.query,
        ...
    )
    return response
```

**Environment variables:**
```bash
# .env (NEVER commit to git)
PERPLEXITY_API_KEY=pplx-xxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
REDIS_URL=redis://localhost:6379
```

---

### 2. Input Validation

**Prevent injection attacks:**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class RAGQuery(BaseModel):
    """Validated RAG query request."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="User question (3-500 chars)"
    )

    commodity: Optional[str] = Field(
        None,
        regex="^(cashew|rubber)$",
        description="Commodity filter"
    )

    language: str = Field(
        "en",
        regex="^(en|km|vi)$",
        description="Response language"
    )

    session_id: str = Field(
        ...,
        min_length=10,
        max_length=100,
        description="Session identifier"
    )

    @validator('query')
    def sanitize_query(cls, v):
        """Remove potential SQL injection attempts."""
        # Strip dangerous characters
        dangerous = ['--', ';', '/*', '*/', 'DROP', 'DELETE', 'UPDATE']
        for char in dangerous:
            if char in v.upper():
                raise ValueError(f"Query contains forbidden pattern: {char}")

        return v.strip()

# Usage:
@router.post("/api/v1/rag/query")
async def rag_query(query: RAGQuery):  # Pydantic validates automatically
    ...
```

---

### 3. Rate Limiting by IP

**Prevent abuse from single IP:**

```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/rag/query")
@limiter.limit("10/hour")  # 10 requests per hour per IP
async def rag_query(request: Request, query: RAGQuery):
    ...
```

---

### 4. CORS Configuration

**Allow only trusted domains:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://admin.yourdomain.com",
        "http://localhost:8501"  # Streamlit dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Implementation Phases

### Phase 4.1: API Layer (6-8 hours)

**Goal:** Build FastAPI endpoints for search and RAG

**Tasks:**
1. Create API routes (`app/api/routes/semantic.py`)
2. Add request/response models (Pydantic)
3. Implement rate limiting middleware
4. Add usage logging
5. Write API documentation (OpenAPI)
6. Test endpoints with Postman/curl

**Files to Create:**
```
app/api/routes/semantic.py         # Search & RAG endpoints
app/middleware/rate_limiter.py     # Rate limiting
app/middleware/logger.py           # Request logging
app/models/rag.py                  # Pydantic models
app/services/budget_service.py     # Budget tracking
tests/test_api_endpoints.py        # API tests
```

**Acceptance Criteria:**
- [ ] `/api/v1/search` returns results in <100ms
- [ ] `/api/v1/rag/query` returns AI answer in <5s
- [ ] Rate limiting blocks at 1000/month, 50/day, 5/hour
- [ ] All endpoints documented in OpenAPI
- [ ] 100% test coverage for API routes

---

### Phase 4.2: Database Schema (2-3 hours)

**Goal:** Create tables for conversation history and usage tracking

**Tasks:**
1. Write migration SQL script
2. Create `conversation_history` table
3. Create `usage_logs` table
4. Add indexes for performance
5. Create views for analytics
6. Test migration on dev database

**Files to Create:**
```
supabase/migrations/005_conversation_history.sql
scripts/test_conversation_schema.py
```

**Acceptance Criteria:**
- [ ] Migration runs without errors
- [ ] Can insert conversation records
- [ ] Can query history by session_id
- [ ] Indexes speed up queries (EXPLAIN ANALYZE)
- [ ] Views return correct aggregations

---

### Phase 4.3: Streamlit UI (5-7 hours)

**Goal:** Build user-friendly web interface

**Tasks:**
1. Set up Streamlit project structure
2. Create search page (main page)
3. Create chat page (RAG Q&A)
4. Create history page
5. Create admin dashboard
6. Add multilingual labels (Khmer, English, Vietnamese)
7. Implement export functionality (PDF, Markdown)
8. Test on mobile (responsive)

**Files to Create:**
```
ui/streamlit_app.py                # Main app entry
ui/pages/1_search.py               # Search page
ui/pages/2_chat.py                 # Chat page
ui/pages/3_history.py              # History page
ui/pages/4_admin.py                # Admin page
ui/components/search_box.py        # Reusable components
ui/components/result_card.py
ui/components/export.py
ui/i18n/translations.py            # Multilingual labels
ui/config.py                       # UI config
ui/utils.py                        # Helper functions
```

**Acceptance Criteria:**
- [ ] Can search in Khmer, English, Vietnamese
- [ ] Search results display with citations
- [ ] Can trigger RAG query from search results
- [ ] Chat interface maintains conversation context
- [ ] Can export to PDF and Markdown
- [ ] Mobile-friendly (tested on Android)
- [ ] Admin dashboard shows real-time stats

---

### Phase 4.4: Budget Management (3-4 hours)

**Goal:** Implement caching and budget monitoring

**Tasks:**
1. Set up Redis (Docker)
2. Implement `CacheService`
3. Integrate cache with RAG endpoint
4. Add cache statistics endpoint
5. Implement budget alerts (email)
6. Add admin actions (clear cache, export logs)

**Files to Create:**
```
app/services/cache_service.py      # Redis caching
app/services/budget_service.py     # Budget monitoring
app/services/email_service.py      # Email alerts
docker-compose.yml                 # Add Redis service
tests/test_cache_service.py
```

**Acceptance Criteria:**
- [ ] Cache hit rate >50% after 1 week
- [ ] Cached responses return in <50ms
- [ ] Email alerts sent at 50%, 80%, 90%, 95%
- [ ] Admin can clear cache
- [ ] Cache reduces costs by 40-60%

---

### Phase 4.5: Testing & Documentation (3-5 hours)

**Goal:** Ensure quality and provide user documentation

**Tasks:**
1. Write end-to-end tests
2. Load testing (concurrent users)
3. Mobile responsiveness testing
4. Write user documentation
5. Write deployment guide
6. Record demo video (optional)

**Files to Create:**
```
tests/test_e2e.py                  # End-to-end tests
tests/load_test.py                 # Locust/k6 load tests
docs/phase4-ui-qa/USER_GUIDE.md    # How to use UI
docs/phase4-ui-qa/DEPLOYMENT.md    # How to deploy
docs/phase4-ui-qa/API_REFERENCE.md # API docs
docs/phase4-ui-qa/TROUBLESHOOTING.md
```

**Acceptance Criteria:**
- [ ] All tests pass (unit, integration, e2e)
- [ ] Load test: 10 concurrent users, <5s p95
- [ ] Mobile works on Android (Chrome, Firefox)
- [ ] User guide covers all features
- [ ] Deployment guide tested on fresh Ubuntu

---

## Testing Strategy

### 1. Unit Tests

**API Endpoints:**
```python
# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_endpoint():
    response = client.post("/api/v1/search", json={
        "query": "cashew production",
        "top_k": 5
    })

    assert response.status_code == 200
    assert len(response.json()['results']) <= 5
    assert response.json()['search_time_ms'] < 200

def test_rag_endpoint():
    response = client.post("/api/v1/rag/query", json={
        "query": "Best provinces for cashew?",
        "commodity": "cashew",
        "session_id": "test_session"
    })

    assert response.status_code == 200
    assert 'answer' in response.json()
    assert 'sources' in response.json()
    assert response.json()['metadata']['cost_usd'] == 0.005

def test_rate_limiting():
    session_id = "abuse_test"

    # Send 6 requests in quick succession
    for i in range(6):
        response = client.post("/api/v1/rag/query", json={
            "query": f"test query {i}",
            "session_id": session_id
        })

        if i < 5:
            assert response.status_code == 200
        else:
            # 6th request should be rate limited
            assert response.status_code == 429
```

---

### 2. Integration Tests

**Cache Service:**
```python
# tests/test_cache_service.py
import pytest
from app.services.cache_service import CacheService

@pytest.fixture
async def cache_service():
    redis_client = redis.from_url("redis://localhost:6379")
    return CacheService(redis_client)

async def test_cache_hit(cache_service):
    query = "cashew production"
    commodity = "cashew"

    # First call - cache miss
    response1 = await cache_service.get_cached_response(query, commodity)
    assert response1 is None

    # Cache response
    await cache_service.cache_response(query, commodity, {"answer": "test"})

    # Second call - cache hit
    response2 = await cache_service.get_cached_response(query, commodity)
    assert response2 == {"answer": "test"}

async def test_cache_expiry(cache_service):
    # Cache with 1-second TTL
    await cache_service.cache_response(
        "test query",
        "cashew",
        {"answer": "test"},
        ttl=1
    )

    # Immediate read - should hit
    response1 = await cache_service.get_cached_response("test query", "cashew")
    assert response1 is not None

    # Wait 2 seconds
    await asyncio.sleep(2)

    # Should be expired
    response2 = await cache_service.get_cached_response("test query", "cashew")
    assert response2 is None
```

---

### 3. End-to-End Tests

**Full RAG Workflow:**
```python
# tests/test_e2e.py
import pytest
from playwright.async_api import async_playwright

async def test_search_to_rag_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to app
        await page.goto("http://localhost:8501")

        # Enter search query
        await page.fill("input[placeholder*='Search']", "cashew production")
        await page.press("input[placeholder*='Search']", "Enter")

        # Wait for results
        await page.wait_for_selector(".search-result")

        # Click "Get AI Answer"
        await page.click("button:has-text('Get AI Answer')")

        # Wait for RAG response
        await page.wait_for_selector(".ai-response", timeout=10000)

        # Verify response contains answer
        response_text = await page.text_content(".ai-response")
        assert len(response_text) > 100

        # Verify sources displayed
        sources = await page.query_selector_all(".source-citation")
        assert len(sources) > 0

        await browser.close()
```

---

### 4. Load Testing

**Concurrent Users:**
```python
# tests/load_test.py (using Locust)
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)  # 75% of requests
    def search(self):
        self.client.post("/api/v1/search", json={
            "query": "cashew",
            "top_k": 5
        })

    @task(1)  # 25% of requests
    def rag_query(self):
        self.client.post("/api/v1/rag/query", json={
            "query": "Best provinces for cashew?",
            "session_id": f"user_{self.environment.runner.user_count}"
        })

# Run:
# locust -f tests/load_test.py --host http://localhost:8000
# Test: 10 concurrent users, 1000 requests
```

**Expected Results:**
- Search: <100ms p95
- RAG: <5s p95
- No errors under 10 concurrent users
- Cache hit rate improves over time

---

## Deployment Plan

### Option 1: Docker Compose (Recommended for Development)

**File:** `docker-compose.yml`
```yaml
version: '3.8'

services:
  # FastAPI backend
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./app:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Streamlit UI
  ui:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    volumes:
      - ./ui:/ui
    command: streamlit run /ui/streamlit_app.py --server.port 8501

  # Redis cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Dockerfile.api:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ./app ./app

# Download embedding model (cache in Docker layer)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.streamlit:**
```dockerfile
FROM python:3.11-slim

WORKDIR /ui

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt streamlit

# Copy UI code
COPY ./ui ./ui

EXPOSE 8501

CMD ["streamlit", "run", "/ui/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

**Deploy:**
```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your credentials

# 2. Build and start
docker-compose up -d

# 3. Access
# API: http://localhost:8000/docs
# UI: http://localhost:8501
```

---

### Option 2: Streamlit Cloud (Recommended for Production)

**Pros:**
- Free hosting (community tier)
- Auto-deploy from GitHub
- HTTPS included
- No server management

**Cons:**
- Limited resources (1 GB RAM, 1 CPU)
- Public apps only (unless paid)

**Setup:**
1. Push code to GitHub
2. Connect repo to Streamlit Cloud
3. Add secrets (Supabase, Perplexity keys)
4. Deploy

**File:** `.streamlit/config.toml`
```toml
[server]
port = 8501
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

**File:** `.streamlit/secrets.toml` (not committed)
```toml
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "xxx"
PERPLEXITY_API_KEY = "pplx-xxx"
REDIS_URL = "redis://xxx"  # Use Redis Cloud free tier
```

---

### Option 3: VPS Deployment (DigitalOcean, AWS Lightsail)

**Cost:** $5-10/month

**Setup Script:**
```bash
#!/bin/bash
# deploy.sh - Deploy to Ubuntu VPS

set -e

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone repo
git clone https://github.com/yourusername/cambodia-agri-analytics.git
cd cambodia-agri-analytics

# 5. Set up environment
cp .env.example .env
nano .env  # Edit with credentials

# 6. Start services
docker-compose up -d

# 7. Set up reverse proxy (Nginx)
sudo apt install nginx -y
sudo cp nginx.conf /etc/nginx/sites-available/default
sudo systemctl restart nginx

echo "Deployment complete!"
echo "API: http://your-ip:8000"
echo "UI: http://your-ip:8501"
```

**Nginx config:**
```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;

    # Streamlit UI
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # FastAPI
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

---

## Summary

### What We're Building

1. **API Layer (FastAPI)**
   - RESTful endpoints for search and RAG
   - Rate limiting (1000/month, 50/day, 5/hour)
   - Usage tracking and logging
   - Budget monitoring

2. **Web UI (Streamlit)**
   - Search page (free semantic search)
   - Chat page (paid RAG Q&A)
   - History page (past conversations)
   - Admin dashboard (usage stats)
   - Multilingual (Khmer, English, Vietnamese)
   - Mobile-friendly

3. **Budget Management**
   - Redis caching (40-60% cost reduction)
   - Query deduplication
   - Email alerts (50%, 80%, 90%, 95%)
   - Real-time usage tracking

### Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 4.1 API Layer | 6-8h | FastAPI endpoints, rate limiting |
| 4.2 Database | 2-3h | Conversation history, usage logs |
| 4.3 Streamlit UI | 5-7h | Search, chat, history, admin pages |
| 4.4 Budget Mgmt | 3-4h | Caching, alerts, monitoring |
| 4.5 Testing | 3-5h | Tests, documentation |
| **TOTAL** | **19-27h** | **Complete Q&A system** |

### Budget

| Scenario | Monthly Cost |
|----------|--------------|
| Conservative (20% RAG) | $1.00 |
| Moderate (40% RAG) | $2.00 |
| Heavy (50% RAG) | $2.50 |
| Max (no cache) | $5.00 |

**Projected: $1-2/month** (well within $5 budget)

---

## Next Steps

1. **Get Approval** for this plan
2. **Install Dependencies** (Streamlit, Redis)
3. **Start Phase 4.1** (API Layer)
4. **Iterate Weekly** until complete

---

**Prepared by:** APEX Planning Agent
**Date:** December 27, 2024
**Status:** Ready for Implementation
