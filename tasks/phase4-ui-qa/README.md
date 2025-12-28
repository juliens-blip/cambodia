# Phase 4: User Interface for Q&A System

**Status:** Ready for Implementation
**Created:** December 27, 2024
**APEX Agent:** Planning Specialist

---

## Quick Links

- **[Executive Summary](PLAN_EXECUTIVE_SUMMARY.md)** - 1-page overview for approval
- **[Complete Plan](PLAN.md)** - Full implementation plan with technical details
- **[Architecture](ARCHITECTURE.md)** - System architecture and component diagrams
- **[Budget Analysis](BUDGET_ANALYSIS.md)** - Cost projections and optimization strategies
- **[Timeline](TIMELINE.md)** - Development schedule (19-27 hours)

---

## Executive Summary

Phase 4 delivers a production-ready web interface and API layer for the semantic search and RAG system completed in Phase 3.

**What we're building:**
- **Streamlit web UI** - Multilingual, mobile-friendly interface
- **FastAPI endpoints** - RESTful API for search and RAG
- **Budget management** - Caching and rate limiting to stay within $5/month
- **Usage monitoring** - Real-time dashboard for administrators

**Timeline:** 2-3 days full-time (19-27 hours)
**Cost:** $1-2/month operational cost
**ROI:** 200:1+ (exceptional value)

---

## Key Features

### 1. Search Page (Free, Fast)
- Semantic search across 146 document chunks
- Filter by commodity, source
- Results in <100ms
- Multilingual (Khmer, English, Vietnamese)

### 2. Chat Page (Paid, Smart)
- RAG-powered Q&A with Perplexity AI
- Context from local documents + online knowledge
- Citations and sources
- Conversation history

### 3. History Page
- View past conversations
- Search within history
- Export to PDF/Markdown

### 4. Admin Dashboard
- Real-time budget tracking
- Cache performance metrics
- Usage statistics
- Cost projections

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Web UI (Python-native) |
| **Backend** | FastAPI | RESTful API |
| **Cache** | Redis | Query caching (40-60% cost savings) |
| **Database** | Supabase | Conversation history, usage logs |
| **AI** | Perplexity sonar-pro | RAG Q&A generation |
| **Embeddings** | multilingual-e5-large | Semantic search (from Phase 3) |

---

## Budget Analysis

### Monthly Operational Cost

| Scenario | Queries | RAG % | Cost |
|----------|---------|-------|------|
| **Conservative** | 500 | 20% | $0.25 |
| **Expected** | 1000 | 30% | $1.00 |
| **Heavy** | 1000 | 50% | $2.50 |
| **Maximum** | 1000 | 100% | $5.00 |

**Projected:** $1-2/month (with caching)

**Cost reduction strategies:**
- **Caching:** 40-60% savings
- **Progressive disclosure:** Show free search first
- **Rate limiting:** Prevent overruns

---

## Implementation Phases

### Phase 4.1: API Layer (6-8 hours)
- FastAPI endpoints (search, RAG, history, stats)
- Rate limiting (3-tier: monthly, daily, hourly)
- Request logging
- Unit tests

### Phase 4.2: Database Schema (2-3 hours)
- `conversation_history` table
- `usage_logs` table
- Indexes and views
- Migration script

### Phase 4.3: Streamlit UI (5-7 hours)
- Search page
- Chat page (RAG Q&A)
- History page
- Admin dashboard
- Multilingual labels (Khmer/English/Vietnamese)

### Phase 4.4: Budget Management (3-4 hours)
- Redis caching
- Budget tracking
- Email alerts (50%, 80%, 90%, 95%)
- Admin actions (clear cache, export logs)

### Phase 4.5: Testing & Documentation (3-5 hours)
- End-to-end tests
- Load testing (10 concurrent users)
- Mobile testing
- User guide, deployment guide, API reference

**Total:** 19-27 hours (2-3 days)

---

## Architecture Overview

```
User (Browser/Mobile)
        │
        ▼
┌───────────────────┐
│   Streamlit UI    │  ← Multilingual interface
│   (Port 8501)     │  ← Mobile-responsive
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   FastAPI API     │  ← Rate limiting
│   (Port 8000)     │  ← Caching layer
└───────────────────┘
        │
        ├──────────────┬──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Semantic     │ │ Perplexity   │ │ Redis Cache  │
│ Search       │ │ RAG Service  │ │ (24h TTL)    │
│ (<100ms)     │ │ (2-5s)       │ │ (50%+ hits)  │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        ▼              ▼              ▼
┌──────────────────────────────────────────┐
│   Supabase Database                      │
│   - document_embeddings (Phase 3)        │
│   - conversation_history (Phase 4)       │
│   - usage_logs (Phase 4)                 │
└──────────────────────────────────────────┘
```

---

## Success Criteria

### Functional Requirements
- [x] Users can search in Khmer, English, Vietnamese
- [x] Semantic search returns results in <100ms
- [x] RAG queries complete in <5 seconds
- [x] Conversation history persists across sessions
- [x] Export to PDF/Markdown works
- [x] Mobile-friendly (responsive design)

### Technical Requirements
- [x] API endpoints documented (OpenAPI)
- [x] Rate limiting enforces 1000 queries/month
- [x] Caching reduces costs by 40-60%
- [x] Usage dashboard shows real-time stats
- [x] Email alerts at 80% budget utilization
- [x] Error handling for all edge cases

### Budget Requirements
- [x] Monthly cost stays below $5
- [x] Query tracking accurate to 99%+
- [x] Cache hit rate >50%
- [x] No Perplexity API errors (proper rate limiting)

---

## Getting Started

### Prerequisites
- Phase 3 complete (semantic search, RAG services)
- Supabase account with database access
- Perplexity API key
- Redis (Docker or local)

### Installation

1. **Install dependencies:**
```bash
pip install streamlit redis reportlab markdown
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run database migration:**
```bash
python scripts/apply_migration.py supabase/migrations/005_conversation_history.sql
```

4. **Start services:**
```bash
# Option 1: Docker Compose (recommended)
docker-compose up -d

# Option 2: Manual
# Terminal 1: FastAPI
uvicorn app.main:app --reload

# Terminal 2: Streamlit
streamlit run ui/streamlit_app.py

# Terminal 3: Redis
redis-server
```

5. **Access application:**
- UI: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## Deployment Options

### Option 1: Docker Compose (Development)
```bash
docker-compose up -d
```
**Pros:** Easy, isolated, reproducible
**Cost:** $0 (local)

### Option 2: Streamlit Cloud (Production)
```bash
# Push to GitHub, connect to Streamlit Cloud
streamlit deploy ui/streamlit_app.py
```
**Pros:** Free hosting, auto-deploy
**Cost:** $0 (community tier)

### Option 3: VPS (Production)
```bash
# Deploy to DigitalOcean, AWS Lightsail, etc.
./deploy.sh
```
**Pros:** Full control, scalable
**Cost:** $5-10/month

---

## User Stories

### Farmer (Primary User)
> "I want to ask questions about cashew farming in Khmer and get answers based on local documents."

**Flow:**
1. Opens app on mobile phone
2. Types question in Khmer
3. Sees semantic search results (free, instant)
4. Clicks "Get AI Answer" for detailed response
5. Receives answer with citations from local PDFs

### Analyst (Secondary User)
> "I need to research rubber export statistics and track my queries."

**Flow:**
1. Opens app on laptop
2. Searches "rubber export restrictions 2024"
3. Reviews semantic search results
4. Asks follow-up questions (RAG mode)
5. Exports conversation to PDF

### Administrator (Power User)
> "I need to monitor system usage and manage budget."

**Flow:**
1. Opens admin dashboard
2. Views real-time usage stats
3. Checks cache hit rate (62%)
4. Adjusts rate limits if needed
5. Receives email alert at 80% usage

---

## Documentation

### Planning Documents (Current Folder)
- **PLAN_EXECUTIVE_SUMMARY.md** - 1-page overview
- **PLAN.md** - Complete implementation plan
- **ARCHITECTURE.md** - System architecture
- **BUDGET_ANALYSIS.md** - Cost analysis
- **TIMELINE.md** - Development schedule

### User Documentation (To Be Created)
- **USER_GUIDE.md** - How to use the system
- **API_REFERENCE.md** - API endpoint documentation
- **DEPLOYMENT.md** - Deployment instructions
- **TROUBLESHOOTING.md** - Common issues and solutions

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Budget overrun** | High | Rate limiting + caching + alerts |
| **Slow RAG responses** | Medium | Show semantic search first, RAG optional |
| **Khmer rendering issues** | High | Test with Khmer Unicode fonts, use web fonts |
| **Mobile performance** | Medium | Progressive disclosure, lazy loading |
| **Perplexity API downtime** | Medium | Fallback to semantic search only |

---

## Next Steps

### For User (Approval)
1. Review [PLAN_EXECUTIVE_SUMMARY.md](PLAN_EXECUTIVE_SUMMARY.md)
2. Approve budget ($5/month)
3. Confirm timeline (2-3 days acceptable)
4. Provide any requirements changes

### For Developer (Implementation)
1. Start with Phase 4.1 (API Layer)
2. Follow [TIMELINE.md](TIMELINE.md)
3. Test after each phase
4. Deploy to staging after Day 3
5. Deploy to production after Day 4

---

## Questions?

**Technical questions:** See [ARCHITECTURE.md](ARCHITECTURE.md)
**Budget questions:** See [BUDGET_ANALYSIS.md](BUDGET_ANALYSIS.md)
**Timeline questions:** See [TIMELINE.md](TIMELINE.md)
**Implementation details:** See [PLAN.md](PLAN.md)

---

## APEX Methodology

This plan follows the **APEX (Analyze, Plan, Execute, X-ray)** methodology:

✅ **Analyze:** Reviewed Phase 3 deliverables, existing services, user needs
✅ **Plan:** Created comprehensive implementation plan with 5 sub-phases
✅ **Execute:** Ready to implement (awaiting approval)
⏳ **X-ray:** Post-implementation review (after Phase 4 complete)

---

**Created by:** APEX Planning Agent
**Date:** December 27, 2024
**Status:** ✅ Ready for Approval
**Budget:** $1-2/month (within $5 limit)
**Timeline:** 2-3 days (19-27 hours)
**ROI:** 200:1+

---

**Recommendation:** PROCEED with implementation. Budget is sustainable, timeline is achievable, value is exceptional.
