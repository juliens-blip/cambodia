# Phase 4: Implementation Timeline

**Project:** Cambodia Agricultural Intelligence Platform
**Phase:** 4 - UI & API Development Schedule
**Date:** December 27, 2024
**Total Duration:** 19-27 hours (2-3 days full-time, 1-2 weeks part-time)

---

## Overview

Phase 4 is divided into 5 sub-phases, each with clear deliverables and acceptance criteria. This timeline assumes a single developer working part-time (4-6 hours/day).

**Timeline Summary:**
- **Optimistic:** 19 hours (2.5 days full-time)
- **Realistic:** 23 hours (3 days full-time)
- **Pessimistic:** 27 hours (3.5 days full-time)
- **Part-time:** 1-2 weeks (4-6 hours/day)

---

## Phase Breakdown

```
Phase 4.1: API Layer ────────────────────────── [████████] 6-8 hours
Phase 4.2: Database Schema ─────────────────── [███] 2-3 hours
Phase 4.3: Streamlit UI ────────────────────── [██████████] 5-7 hours
Phase 4.4: Budget Management ──────────────── [████] 3-4 hours
Phase 4.5: Testing & Documentation ────────── [████] 3-5 hours
                                              ─────────────────────
                                              TOTAL: 19-27 hours
```

---

## Phase 4.1: API Layer

**Duration:** 6-8 hours
**Priority:** High (blocking for UI)
**Dependencies:** None (Phase 3 services already exist)

### Day 1: API Endpoints (3-4 hours)

**Tasks:**
1. Create semantic search endpoint (`POST /api/v1/search`)
   - Request/response models (Pydantic)
   - Integration with SemanticSearchService
   - Error handling
   - **Time:** 1 hour

2. Create RAG endpoint (`POST /api/v1/rag/query`)
   - Request/response models
   - Integration with PerplexityService
   - Context formatting
   - **Time:** 1.5 hours

3. Create history endpoint (`GET /api/v1/history`)
   - Query parameters (session_id, limit, offset)
   - Database integration
   - **Time:** 0.5 hours

4. Create stats endpoint (`GET /api/v1/stats`)
   - Budget statistics
   - Cache statistics
   - Performance metrics
   - **Time:** 1 hour

**Deliverables:**
- `app/api/routes/semantic.py`
- `app/models/rag.py`
- `app/models/search.py`

**Acceptance Criteria:**
- [ ] All endpoints return 200 OK with valid input
- [ ] Pydantic validation rejects invalid input (400 Bad Request)
- [ ] OpenAPI docs auto-generated at `/docs`

---

### Day 1-2: Middleware & Testing (3-4 hours)

**Tasks:**
5. Implement rate limiter middleware
   - 3-tier rate limiting (monthly, daily, hourly)
   - Redis integration
   - Error responses (429 Too Many Requests)
   - **Time:** 2 hours

6. Add request logging middleware
   - Log all requests to usage_logs table
   - Track response times
   - **Time:** 1 hour

7. Write API tests
   - Unit tests for each endpoint
   - Rate limiting tests
   - Error handling tests
   - **Time:** 1-2 hours

**Deliverables:**
- `app/middleware/rate_limiter.py`
- `app/middleware/logger.py`
- `tests/test_api_endpoints.py`

**Acceptance Criteria:**
- [ ] Rate limiter enforces all 3 limits
- [ ] Requests logged to database
- [ ] 100% test coverage for API routes

---

**Phase 4.1 Checkpoint:**
- **Completed:** API endpoints working
- **Tested:** All endpoints, rate limiting
- **Documented:** OpenAPI spec at `/docs`
- **Ready for:** UI integration

---

## Phase 4.2: Database Schema

**Duration:** 2-3 hours
**Priority:** Medium (needed for conversation history)
**Dependencies:** Supabase access

### Day 2: Schema Design & Migration (2-3 hours)

**Tasks:**
1. Write migration SQL
   - Create `conversation_history` table
   - Create `usage_logs` table
   - Create indexes
   - Create views (`v_monthly_budget`)
   - **Time:** 1 hour

2. Test migration locally
   - Run migration on dev database
   - Verify tables created
   - Test indexes (EXPLAIN ANALYZE)
   - **Time:** 0.5 hours

3. Create Python models (SQLAlchemy/Pydantic)
   - Conversation model
   - Usage log model
   - **Time:** 0.5 hours

4. Write test data script
   - Insert sample conversations
   - Verify queries work
   - **Time:** 0.5-1 hour

**Deliverables:**
- `supabase/migrations/005_conversation_history.sql`
- `app/models/conversation.py`
- `scripts/test_conversation_schema.py`

**Acceptance Criteria:**
- [ ] Migration runs without errors
- [ ] Can insert and query conversations
- [ ] Indexes improve query performance
- [ ] Views return correct aggregations

---

**Phase 4.2 Checkpoint:**
- **Completed:** Database schema deployed
- **Tested:** Insert, query, aggregate operations
- **Ready for:** Conversation storage in UI

---

## Phase 4.3: Streamlit UI

**Duration:** 5-7 hours
**Priority:** High (user-facing)
**Dependencies:** Phase 4.1 (API endpoints)

### Day 2-3: Core UI Pages (3-4 hours)

**Tasks:**
1. Set up Streamlit project structure
   - Main app entry point
   - Page routing
   - Session state initialization
   - **Time:** 0.5 hours

2. Create search page (`ui/pages/1_search.py`)
   - Search input (multilingual)
   - Filter controls (commodity, source)
   - Results display
   - "Get AI Answer" button
   - **Time:** 1.5 hours

3. Create chat page (`ui/pages/2_chat.py`)
   - Chat interface (st.chat_message)
   - Conversation history display
   - RAG query integration
   - Source citations
   - **Time:** 1.5 hours

4. Create history page (`ui/pages/3_history.py`)
   - List past conversations
   - Filter by date
   - Export functionality
   - **Time:** 0.5 hours

**Deliverables:**
- `ui/streamlit_app.py`
- `ui/pages/1_search.py`
- `ui/pages/2_chat.py`
- `ui/pages/3_history.py`

**Acceptance Criteria:**
- [ ] Can search in Khmer, English, Vietnamese
- [ ] Search results display correctly
- [ ] Can trigger RAG from search results
- [ ] Chat interface maintains conversation context

---

### Day 3: Admin Dashboard & Components (2-3 hours)

**Tasks:**
5. Create admin page (`ui/pages/4_admin.py`)
   - Budget usage chart
   - Cache statistics
   - Top queries table
   - Admin actions (clear cache)
   - **Time:** 1.5 hours

6. Create reusable components
   - `search_box.py` (search input)
   - `result_card.py` (search result display)
   - `source_citation.py` (citation display)
   - **Time:** 1 hour

7. Add multilingual support
   - Translation dictionary (Khmer, English, Vietnamese)
   - Language selector
   - **Time:** 0.5 hours

**Deliverables:**
- `ui/pages/4_admin.py`
- `ui/components/` (all components)
- `ui/i18n/translations.py`

**Acceptance Criteria:**
- [ ] Admin dashboard shows real-time stats
- [ ] Components reusable across pages
- [ ] UI labels in Khmer/English/Vietnamese

---

**Phase 4.3 Checkpoint:**
- **Completed:** Full UI with 4 pages
- **Tested:** Search, chat, history, admin
- **Ready for:** User testing

---

## Phase 4.4: Budget Management

**Duration:** 3-4 hours
**Priority:** Medium (cost control)
**Dependencies:** Phase 4.1 (API), Redis

### Day 3-4: Caching & Budget Tracking (3-4 hours)

**Tasks:**
1. Set up Redis (Docker Compose)
   - Add Redis service
   - Configure persistence
   - **Time:** 0.5 hours

2. Implement CacheService
   - Get/set cached responses
   - Query hash generation
   - Cache statistics
   - **Time:** 1 hour

3. Integrate cache with RAG endpoint
   - Check cache before Perplexity call
   - Store response after call
   - Track hit/miss rates
   - **Time:** 0.5 hours

4. Implement BudgetService
   - Track usage (monthly, daily, hourly)
   - Budget alerts (50%, 80%, 90%, 95%)
   - Email notifications
   - **Time:** 1 hour

5. Add budget tracking to admin dashboard
   - Real-time usage chart
   - Cache performance metrics
   - **Time:** 0.5 hours

**Deliverables:**
- `docker-compose.yml` (add Redis)
- `app/services/cache_service.py`
- `app/services/budget_service.py`
- `tests/test_cache_service.py`

**Acceptance Criteria:**
- [ ] Cache reduces Perplexity calls by 40-60%
- [ ] Budget tracking accurate to 99%+
- [ ] Email alerts sent at thresholds
- [ ] Admin dashboard shows cache stats

---

**Phase 4.4 Checkpoint:**
- **Completed:** Caching and budget management
- **Tested:** Cache hit/miss, budget limits
- **Ready for:** Production deployment

---

## Phase 4.5: Testing & Documentation

**Duration:** 3-5 hours
**Priority:** Medium (quality assurance)
**Dependencies:** All previous phases

### Day 4-5: Comprehensive Testing (2-3 hours)

**Tasks:**
1. End-to-end tests
   - User flow: Search → RAG → History
   - Error scenarios
   - Mobile testing (Android)
   - **Time:** 1.5 hours

2. Load testing
   - 10 concurrent users
   - 1000 requests
   - Performance profiling
   - **Time:** 1 hour

3. Security testing
   - Input validation
   - SQL injection attempts
   - Rate limit bypass attempts
   - **Time:** 0.5 hours

**Deliverables:**
- `tests/test_e2e.py`
- `tests/load_test.py` (Locust)
- Load test results report

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Load test: <5s p95 for RAG
- [ ] No security vulnerabilities found

---

### Day 5: Documentation (1-2 hours)

**Tasks:**
4. User documentation
   - How to use search
   - How to use chat
   - Multilingual guide
   - **Time:** 1 hour

5. Deployment guide
   - Docker Compose setup
   - Environment variables
   - Streamlit Cloud deployment
   - **Time:** 0.5 hours

6. API documentation
   - Endpoint reference
   - Example requests/responses
   - Error codes
   - **Time:** 0.5 hours

**Deliverables:**
- `docs/phase4-ui-qa/USER_GUIDE.md`
- `docs/phase4-ui-qa/DEPLOYMENT.md`
- `docs/phase4-ui-qa/API_REFERENCE.md`
- `docs/phase4-ui-qa/TROUBLESHOOTING.md`

**Acceptance Criteria:**
- [ ] User guide covers all features
- [ ] Deployment guide tested on fresh Ubuntu
- [ ] API docs include all endpoints

---

**Phase 4.5 Checkpoint:**
- **Completed:** Testing and documentation
- **Ready for:** Production deployment
- **Status:** Phase 4 COMPLETE

---

## Detailed Schedule (3-Day Sprint)

### Day 1: API Foundation (8 hours)

**Morning (4 hours):**
- 09:00-10:00: Create search endpoint
- 10:00-11:30: Create RAG endpoint
- 11:30-12:00: Create history endpoint
- 12:00-13:00: Lunch

**Afternoon (4 hours):**
- 13:00-14:00: Create stats endpoint
- 14:00-16:00: Implement rate limiter
- 16:00-17:00: Add request logger

**Checkpoint:** API endpoints working, rate limiting active

---

### Day 2: Database & UI Core (8 hours)

**Morning (4 hours):**
- 09:00-10:00: Write database migration
- 10:00-10:30: Test migration
- 10:30-11:30: Set up Streamlit project
- 11:30-13:00: Build search page

**Afternoon (4 hours):**
- 14:00-15:30: Build chat page
- 15:30-16:00: Build history page
- 16:00-17:00: API integration testing

**Checkpoint:** UI pages functional, connected to API

---

### Day 3: Budget & Polish (7 hours)

**Morning (4 hours):**
- 09:00-09:30: Set up Redis
- 09:30-10:30: Implement CacheService
- 10:30-11:30: Implement BudgetService
- 11:30-13:00: Build admin dashboard

**Afternoon (3 hours):**
- 14:00-15:00: End-to-end testing
- 15:00-16:00: Documentation
- 16:00-17:00: Final review

**Checkpoint:** Phase 4 complete, ready for deployment

---

## Part-Time Schedule (1-2 Weeks)

**Week 1:**
- **Mon (4h):** Phase 4.1 - API endpoints
- **Tue (4h):** Phase 4.1 - Middleware & tests
- **Wed (4h):** Phase 4.2 - Database + Phase 4.3 start
- **Thu (4h):** Phase 4.3 - UI pages
- **Fri (4h):** Phase 4.3 - Admin dashboard

**Week 2:**
- **Mon (4h):** Phase 4.4 - Caching & budget
- **Tue (4h):** Phase 4.5 - Testing
- **Wed (2h):** Phase 4.5 - Documentation
- **Thu (2h):** Buffer / polish
- **Fri:** DONE

**Total:** 26 hours over 9 days

---

## Milestones & Deliverables

### Milestone 1: API Complete (Day 1)
**Deliverables:**
- [x] 4 API endpoints (search, RAG, history, stats)
- [x] Rate limiting (3-tier)
- [x] Request logging
- [x] Unit tests (100% coverage)

**Demo:** curl commands show all endpoints working

---

### Milestone 2: UI Complete (Day 2)
**Deliverables:**
- [x] 4 UI pages (search, chat, history, admin)
- [x] Multilingual support (Khmer/English/Vietnamese)
- [x] Mobile-responsive design

**Demo:** Video walkthrough of all pages

---

### Milestone 3: Production-Ready (Day 3)
**Deliverables:**
- [x] Caching (40-60% cost reduction)
- [x] Budget monitoring (real-time)
- [x] Email alerts
- [x] End-to-end tests
- [x] Documentation

**Demo:** Deploy to staging, run load test

---

## Risk Buffer

**Contingency time:** 20% (4-6 hours)

**Potential delays:**
- Streamlit learning curve (if unfamiliar): +2 hours
- Redis setup issues: +1 hour
- Testing edge cases: +2 hours
- Documentation polish: +1 hour

**Mitigation:**
- Start with Phase 4.1 (most critical)
- Use existing code examples from Phase 3
- Timebox each task (move on if stuck)

---

## Dependencies & Blockers

### External Dependencies
- [x] Phase 3 complete (semantic search, RAG)
- [x] Supabase access
- [x] Perplexity API key
- [ ] Redis installation (Day 3)

### Potential Blockers
1. **Supabase migration fails**
   - Mitigation: Test on dev database first
   - Fallback: Use local PostgreSQL

2. **Streamlit Cloud limits**
   - Mitigation: Test locally first
   - Fallback: Deploy to VPS

3. **Redis not available**
   - Mitigation: Start with in-memory cache (dict)
   - Fallback: Add Redis in Phase 5

---

## Testing Schedule

### Unit Tests (Ongoing)
- Write tests alongside each feature
- Target: 90%+ coverage
- Tools: pytest, httpx TestClient

### Integration Tests (Day 2-3)
- API ↔ Database
- API ↔ Cache
- UI ↔ API

### E2E Tests (Day 3)
- Full user flows
- Mobile testing
- Error scenarios

### Load Tests (Day 3)
- 10 concurrent users
- 1000 total requests
- Performance profiling

---

## Deployment Schedule

### Day 3 PM: Staging Deployment
1. Deploy to Docker Compose (local)
2. Smoke test all features
3. Invite team for feedback

### Day 4: Production Deployment
1. Deploy to Streamlit Cloud
2. Configure environment variables
3. Test on public URL
4. Share with stakeholders

### Day 5: Monitoring
1. Watch usage metrics
2. Monitor for errors
3. Iterate based on feedback

---

## Success Criteria

**Phase 4 is complete when:**
- [ ] All 5 sub-phases delivered
- [ ] All acceptance criteria met
- [ ] Tests passing (unit, integration, e2e)
- [ ] Documentation complete
- [ ] Deployed to production
- [ ] Budget < $5/month verified
- [ ] User can search and ask questions
- [ ] Admin can monitor usage

---

## Post-Launch Activities

### Week 1 (Monitoring)
- Daily check of usage stats
- Daily check of error logs
- Collect user feedback
- Fix critical bugs

### Week 2 (Optimization)
- Analyze cache hit rates
- Optimize slow queries
- Improve UI based on feedback

### Month 1 (Review)
- Review budget (actual vs projected)
- Review user adoption
- Plan Phase 5 enhancements

---

## Gantt Chart (Text)

```
Phase 4 Timeline (19-27 hours)
─────────────────────────────────────────────

Day 1    Day 2    Day 3    Day 4    Day 5
│        │        │        │        │
├─ 4.1 API Layer ────────┤
│  │                      │
│  ├─ Endpoints ────┤
│  └─ Middleware ──────┤
│
├────── 4.2 DB Schema ──┤
│                        │
├─────── 4.3 Streamlit UI ─────────────┤
│         │                             │
│         ├─ Pages ────────┤
│         └─ Components ──────┤
│
│         ├─ 4.4 Budget Mgmt ─────┤
│                                  │
│                  ├─ 4.5 Testing & Docs ────┤
│                                              │
└──────────────────────────────────────────────┘
          COMPLETE                    DEPLOY
```

---

## Conclusion

Phase 4 can be delivered in **3-5 days** (full-time) or **1-2 weeks** (part-time), with a realistic estimate of **23 hours** total effort.

**Key Success Factors:**
1. **Clear scope:** Well-defined deliverables
2. **Modular design:** Independent phases
3. **Existing foundation:** Phase 3 services ready
4. **Risk buffer:** 20% contingency
5. **Incremental delivery:** Test after each phase

**Recommended approach:**
- Start Day 1 (Monday)
- Complete by Day 3-4 (Wed-Thu)
- Deploy to staging Day 3 PM
- Deploy to production Day 4
- Monitor Week 1

**Go/No-Go:** GO - Timeline is achievable, phases well-scoped.

---

**Prepared by:** APEX Planning Agent
**Date:** December 27, 2024
**Status:** Ready for Execution
