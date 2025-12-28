# Phase 4: User Interface for Q&A System - Executive Summary

**Project:** Cambodia Agricultural Intelligence Platform
**Phase:** 4 - UI & API for Semantic Search & RAG
**Date:** December 27, 2024
**Status:** Ready for Approval
**Estimated Duration:** 15-25 hours (2-3 days)
**Estimated Cost:** $5/month (within existing Perplexity budget)

---

## Executive Overview

Phase 4 delivers a production-ready web interface and API layer for the semantic search and RAG system completed in Phase 3. This phase focuses on making the powerful backend (146 chunks, multilingual search, Perplexity RAG) accessible to end users through an intuitive, mobile-friendly interface.

### What We're Building

A complete question-answering system with:
- **Web UI:** Simple, multilingual interface for farmers, analysts, and administrators
- **REST API:** FastAPI endpoints for semantic search and RAG queries
- **Budget Management:** Rate limiting and caching to stay within $5/month
- **Usage Monitoring:** Real-time dashboard to track queries and costs

---

## Key Features

### 1. User Interface (Streamlit - Recommended)
- **Multilingual support:** Khmer, English, Vietnamese
- **Mobile-friendly:** Responsive design for field use
- **Real-time results:** Live search and Q&A
- **Citation display:** Show local sources + external references
- **Conversation history:** Track previous questions
- **Export capabilities:** PDF, Markdown, CSV

### 2. API Layer (FastAPI)
- `POST /api/v1/search` - Semantic search endpoint
- `POST /api/v1/rag/query` - RAG Q&A endpoint
- `GET /api/v1/history` - Conversation history
- `GET /api/v1/stats` - Usage statistics
- `GET /api/v1/health` - System health check

### 3. Budget Management
- **Rate limiting:** 1000 queries/month max (Perplexity limit)
- **Query caching:** Redis-based caching (40-60% cost reduction)
- **Usage tracking:** Real-time monitoring per user/session
- **Alerts:** Email notifications at 80% budget utilization

### 4. User Experience
- **Simple interface:** Single search box, instant results
- **Context-aware:** Remembers conversation history
- **Progressive disclosure:** Show semantic search first, RAG on demand
- **Offline support:** Semantic search works without Perplexity

---

## Technology Stack Decision

After evaluating three options, **Streamlit** is recommended:

| Option | Pros | Cons | Score |
|--------|------|------|-------|
| **Streamlit** (Recommended) | Python-native, rapid development, built-in components, no frontend skills needed | Limited customization, not ideal for complex UX | 9/10 |
| HTML/JS | Lightweight, full control, no dependencies | Requires frontend skills, slower development | 6/10 |
| React/Next.js | Modern, scalable, rich ecosystem | Complex setup, overkill for MVP, requires JS skills | 7/10 |

**Why Streamlit?**
- 5x faster development (1-2 days vs 5-7 days)
- Python-native (seamless integration with existing services)
- Built-in multilingual support
- Perfect for data-driven apps
- Easy deployment (Docker, cloud)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 4 Architecture                      │
└─────────────────────────────────────────────────────────────┘

User (Browser/Mobile)
        │
        ▼
┌───────────────────────┐
│   Streamlit UI        │  ← Multilingual interface
│   - Search input      │  ← Khmer/English/Vietnamese
│   - Results display   │  ← Citations + sources
│   - History view      │  ← Conversation tracking
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│   FastAPI Middleware  │  ← Rate limiting
│   - /api/v1/search    │  ← Caching layer
│   - /api/v1/rag/query │  ← Usage tracking
│   - /api/v1/stats     │  ← Health checks
└───────────────────────┘
        │
        ├──────────────┬──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Semantic     │ │ Perplexity   │ │ Redis Cache  │
│ Search       │ │ RAG Service  │ │ (Optional)   │
│ (<100ms)     │ │ (2-5s)       │ │ (40-60% ↓$)  │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        ▼              ▼              ▼
┌──────────────────────────────────────────┐
│   Supabase Database                      │
│   - document_embeddings (146 chunks)     │
│   - conversation_history (new)           │
│   - usage_logs (new)                     │
└──────────────────────────────────────────┘
```

---

## Budget Analysis

### Monthly Cost Breakdown (1000 queries/month)

| Service | Unit Cost | Usage | Monthly Cost |
|---------|-----------|-------|--------------|
| **Semantic Search** | $0 | Unlimited | $0.00 |
| **Perplexity RAG** | $0.005/query | 200 queries | $1.00 |
| **Supabase (free tier)** | $0 | <500 MB | $0.00 |
| **Streamlit hosting** | $0 | Self-hosted | $0.00 |
| **Redis (optional)** | $0 | Docker/local | $0.00 |
| **TOTAL** | | | **$1.00** |

### Cost Scenarios

| Scenario | Semantic Search | RAG Queries | Monthly Cost |
|----------|----------------|-------------|--------------|
| **Conservative** (80% search, 20% RAG) | 800 | 200 | $1.00 |
| **Moderate** (60% search, 40% RAG) | 600 | 400 | $2.00 |
| **Heavy RAG** (50% search, 50% RAG) | 500 | 500 | $2.50 |
| **Max Budget** (no cache) | 0 | 1000 | $5.00 |

### Cost Reduction Strategies

1. **Query Caching (40-60% savings):**
   - Cache RAG responses for 24 hours
   - Deduplicate similar questions (cosine similarity > 0.95)
   - Expected savings: $2-3/month

2. **Progressive Disclosure:**
   - Show semantic search results first (free)
   - User clicks "Get AI Answer" to trigger RAG (paid)
   - Expected RAG usage: 20-30% of queries

3. **Rate Limiting:**
   - 1000 queries/month hard limit
   - 50 queries/day per user
   - 5 queries/hour per session

**Projected Monthly Cost:** $1-2/month (well within $5 budget)

---

## Implementation Timeline

### Phase 4.1: API Layer (6-8 hours)
- Create FastAPI endpoints for search and RAG
- Add request validation and error handling
- Implement rate limiting middleware
- Add usage tracking to database
- Write API documentation

**Deliverables:**
- `app/api/routes/semantic.py` (search & RAG endpoints)
- `app/middleware/rate_limiter.py` (budget protection)
- `app/models/conversation.py` (database schema)
- API documentation (OpenAPI/Swagger)

### Phase 4.2: Database Schema (2-3 hours)
- Create `conversation_history` table
- Create `usage_logs` table
- Add indexes for performance
- Write migration scripts

**Deliverables:**
- `supabase/migrations/005_conversation_history.sql`
- `supabase/migrations/006_usage_tracking.sql`

### Phase 4.3: Streamlit UI (5-7 hours)
- Build main search interface
- Add RAG Q&A component
- Implement conversation history view
- Add export functionality (PDF, Markdown)
- Multilingual UI labels

**Deliverables:**
- `ui/streamlit_app.py` (main app)
- `ui/components/search.py` (search component)
- `ui/components/chat.py` (Q&A component)
- `ui/components/history.py` (history view)
- `ui/i18n/translations.py` (Khmer/English/Vietnamese)

### Phase 4.4: Budget Management (3-4 hours)
- Implement Redis caching layer
- Add query deduplication
- Build usage dashboard
- Set up email alerts
- Add admin panel

**Deliverables:**
- `app/services/cache_service.py` (Redis integration)
- `app/services/budget_service.py` (usage tracking)
- `ui/pages/admin.py` (admin dashboard)
- Email alert configuration

### Phase 4.5: Testing & Documentation (3-5 hours)
- End-to-end testing (search, RAG, caching)
- Load testing (concurrent users)
- Mobile responsiveness testing
- User documentation
- Deployment guide

**Deliverables:**
- `tests/test_api_endpoints.py`
- `tests/test_ui_components.py`
- `docs/phase4-ui-qa/USER_GUIDE.md`
- `docs/phase4-ui-qa/DEPLOYMENT.md`

**Total Duration:** 19-27 hours (2-3 days)

---

## Success Criteria

### Functional Requirements
- [ ] Users can search in Khmer, English, Vietnamese
- [ ] Semantic search returns results in <100ms
- [ ] RAG queries complete in <5 seconds
- [ ] Conversation history persists across sessions
- [ ] Export to PDF/Markdown works
- [ ] Mobile-friendly (responsive design)

### Technical Requirements
- [ ] API endpoints documented (OpenAPI)
- [ ] Rate limiting enforces 1000 queries/month
- [ ] Caching reduces costs by 40-60%
- [ ] Usage dashboard shows real-time stats
- [ ] Email alerts at 80% budget utilization
- [ ] Error handling for all edge cases

### Budget Requirements
- [ ] Monthly cost stays below $5
- [ ] Query tracking accurate to 99%+
- [ ] Cache hit rate >50%
- [ ] No Perplexity API errors (proper rate limiting)

---

## User Stories

### Farmer (Primary User)
**Story:** "I want to ask questions about cashew farming in Khmer and get answers based on local documents."

**Flow:**
1. Opens app on mobile phone
2. Types question in Khmer: "តើគួរដាំស្វាយចន្ទីនៅខេត្តណា?" (Which province to plant cashew?)
3. Sees semantic search results (free, instant)
4. Clicks "Get AI Answer" for detailed response
5. Receives answer with citations from local PDFs
6. Saves conversation for later reference

### Analyst (Secondary User)
**Story:** "I need to research rubber export statistics and track my queries."

**Flow:**
1. Opens app on laptop
2. Searches "rubber export restrictions 2024"
3. Reviews semantic search results
4. Asks follow-up questions (RAG mode)
5. Exports conversation to PDF
6. Views usage dashboard to track budget

### Administrator (Power User)
**Story:** "I need to monitor system usage and manage budget."

**Flow:**
1. Opens admin dashboard
2. Views real-time usage stats
3. Sees 456/1000 queries used (45.6%)
4. Checks cache hit rate (62%)
5. Adjusts rate limits if needed
6. Receives email alert at 80% usage

---

## Risk Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Budget overrun** | High | Medium | Rate limiting + caching + alerts |
| **Slow RAG responses** | Medium | Low | Show semantic search first, RAG optional |
| **Khmer rendering issues** | High | Low | Test with Khmer Unicode fonts, use web fonts |
| **Mobile performance** | Medium | Low | Progressive disclosure, lazy loading |
| **Perplexity API downtime** | Medium | Low | Fallback to semantic search only |
| **Cache invalidation** | Low | Medium | 24-hour TTL, manual clear option |

---

## Deployment Strategy

### Option 1: Docker (Recommended)
**Pros:** Isolated, reproducible, easy scaling
**Cons:** Requires Docker knowledge

```bash
# Single command deployment
docker-compose up -d

# Services:
# - FastAPI (port 8000)
# - Streamlit (port 8501)
# - Redis (port 6379)
```

### Option 2: Cloud Platform (Streamlit Cloud)
**Pros:** Free hosting, auto-deployment from GitHub
**Cons:** Limited resources on free tier

```bash
# Deploy to Streamlit Cloud
streamlit deploy ui/streamlit_app.py
```

### Option 3: VPS (DigitalOcean, AWS Lightsail)
**Pros:** Full control, scalable
**Cons:** $5-10/month hosting cost

```bash
# Install on Ubuntu VPS
./deploy.sh
```

**Recommendation:** Start with Docker locally, then Streamlit Cloud for production.

---

## Next Steps

### Immediate Actions
1. **Approve Plan:** Review and approve this plan
2. **Install Dependencies:** Add Streamlit, Redis to requirements.txt
3. **Create Database Schema:** Run migration for conversation_history
4. **Start Phase 4.1:** Build API endpoints

### Week 1 Goals
- Complete API layer (Phase 4.1)
- Build basic Streamlit UI (Phase 4.3)
- Test end-to-end flow

### Week 2 Goals
- Add budget management (Phase 4.4)
- Finalize UI/UX
- Complete documentation
- Deploy to production

---

## Conclusion

Phase 4 delivers a complete, user-friendly interface for the powerful semantic search and RAG system. With careful budget management (caching, rate limiting), we can provide unlimited semantic search and ~200-500 RAG queries per month for just $1-2/month.

**Key Benefits:**
- **Low cost:** $1-2/month (vs $5 budget)
- **Fast development:** 2-3 days (Streamlit advantage)
- **User-friendly:** Multilingual, mobile-ready
- **Production-ready:** Rate limiting, caching, monitoring
- **Scalable:** Easy to add features later

**Recommendation:** Proceed with implementation using Streamlit + FastAPI architecture.

---

**Prepared by:** APEX Planning Agent
**Date:** December 27, 2024
**Status:** Ready for Approval
**Budget:** $1-2/month (within $5 limit)
**Timeline:** 2-3 days (19-27 hours)
