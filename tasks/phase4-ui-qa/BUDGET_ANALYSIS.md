# Phase 4: Budget Analysis

**Project:** Cambodia Agricultural Intelligence Platform
**Phase:** 4 - UI & API Budget Analysis
**Date:** December 27, 2024

---

## Executive Summary

Phase 4 can be delivered for **$1-2/month** operational cost, well within the $5/month Perplexity budget. Through strategic caching (40-60% cost reduction) and progressive disclosure (showing free semantic search first), we minimize Perplexity API usage while maximizing value to users.

**Key Findings:**
- **Projected monthly cost:** $1-2 (conservative usage)
- **Budget headroom:** $3-4/month remaining
- **Cost per query:** $0.005 (RAG), $0 (search)
- **Break-even:** 200 RAG queries/month = $1
- **Maximum queries:** 1000/month = $5 (hard limit)

---

## Cost Breakdown

### 1. One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| **Development** | $0 | Internal development |
| **Infrastructure setup** | $0 | Docker, Streamlit Cloud free |
| **Testing** | $0.50 | ~100 test Perplexity queries |
| **Documentation** | $0 | Internal effort |
| **TOTAL SETUP** | **$0.50** | One-time |

---

### 2. Monthly Operational Costs

#### A. Perplexity API (Variable)

| Usage Scenario | RAG Queries | Cost | Probability |
|----------------|-------------|------|-------------|
| **Light usage** (10% RAG) | 100 | $0.50 | 20% |
| **Moderate usage** (20% RAG) | 200 | $1.00 | 50% |
| **Heavy usage** (40% RAG) | 400 | $2.00 | 25% |
| **Very heavy** (80% RAG) | 800 | $4.00 | 5% |
| **Max budget** (100% RAG) | 1000 | $5.00 | 0% |

**Expected monthly cost:** $1-2 (80% confidence)

**Cost drivers:**
- User adoption rate
- Question complexity (simple → search, complex → RAG)
- Cache hit rate (higher = lower cost)

#### B. Infrastructure (Fixed)

| Service | Tier | Monthly Cost | Notes |
|---------|------|--------------|-------|
| **Supabase** | Free | $0 | <500 MB egress, <100k requests |
| **Streamlit Cloud** | Community | $0 | 1 app, public |
| **Redis** | Docker/Local | $0 | Self-hosted |
| **Embedding Model** | Local | $0 | CPU inference |
| **Domain/SSL** | Optional | $0-10 | Free with Streamlit Cloud |
| **Email (SMTP)** | Free tier | $0 | Gmail SMTP or SendGrid |
| **TOTAL FIXED** | | **$0** | All free tiers |

#### C. Total Monthly Cost

| Scenario | Fixed | Variable | Total |
|----------|-------|----------|-------|
| **Minimum** | $0 | $0.50 | **$0.50** |
| **Expected** | $0 | $1-2 | **$1-2** |
| **Maximum** | $0 | $5.00 | **$5.00** |

---

## Cost Analysis by User Type

### User Type 1: Farmer (Primary, 60% of users)

**Profile:**
- Skill level: Low
- Device: Mobile (Android)
- Queries/week: 5-10
- Language: Khmer
- Use case: Simple questions about farming

**Usage Pattern:**
- 80% semantic search (free)
- 20% RAG (only when search insufficient)

**Monthly cost per farmer:**
- Semantic search: 32 queries × $0 = $0
- RAG: 8 queries × $0.005 = **$0.04**

**For 10 farmers:** $0.40/month

---

### User Type 2: Analyst (Secondary, 30% of users)

**Profile:**
- Skill level: Medium
- Device: Laptop/Desktop
- Queries/week: 20-50
- Language: English, Khmer
- Use case: Market research, data analysis

**Usage Pattern:**
- 60% semantic search (quick lookups)
- 40% RAG (detailed analysis)

**Monthly cost per analyst:**
- Semantic search: 120 queries × $0 = $0
- RAG: 80 queries × $0.005 = **$0.40**

**For 5 analysts:** $2.00/month

---

### User Type 3: Administrator (Power, 10% of users)

**Profile:**
- Skill level: High
- Device: Desktop
- Queries/week: 10 (mostly monitoring)
- Language: English
- Use case: System monitoring, occasional queries

**Usage Pattern:**
- 90% semantic search (testing)
- 10% RAG (validation)

**Monthly cost per admin:**
- Semantic search: 36 queries × $0 = $0
- RAG: 4 queries × $0.005 = **$0.02**

**For 2 admins:** $0.04/month

---

### Total User Cost

| User Type | Count | Monthly Cost |
|-----------|-------|--------------|
| Farmers | 10 | $0.40 |
| Analysts | 5 | $2.00 |
| Admins | 2 | $0.04 |
| **TOTAL** | **17** | **$2.44** |

**Within budget?** Yes ($2.44 < $5.00)

**Safety margin:** $2.56 (51% headroom)

---

## Cost Reduction Strategies

### 1. Query Caching (40-60% savings)

**Mechanism:** Store RAG responses in Redis for 24 hours

**Example:**
```
Without cache:
- 200 RAG queries/month × $0.005 = $1.00

With cache (50% hit rate):
- 100 unique queries × $0.005 = $0.50
- 100 cache hits × $0 = $0
- Total: $0.50 (50% savings)
```

**Cache hit rate projections:**

| Time Period | Hit Rate | Savings |
|-------------|----------|---------|
| Week 1 | 20% | 20% |
| Week 2 | 40% | 40% |
| Week 3 | 50% | 50% |
| Month 1+ | 60% | 60% |

**Implementation:**
```python
# app/services/cache_service.py
class CacheService:
    TTL_SECONDS = 24 * 60 * 60  # 24 hours

    async def get_cached_response(self, query_hash):
        return await self.redis.get(f"rag:response:{query_hash}")

    async def cache_response(self, query_hash, response):
        await self.redis.setex(
            f"rag:response:{query_hash}",
            self.TTL_SECONDS,
            json.dumps(response)
        )
```

**Expected savings:** $0.50-1.20/month (at 200-400 RAG queries)

---

### 2. Progressive Disclosure (Reduce RAG usage)

**Mechanism:** Show semantic search results first, RAG only on user request

**UI Flow:**
```
User searches "cashew production"
   ↓
Display semantic search results (free)
   ↓
User clicks "Get AI Answer" on relevant result
   ↓
Trigger RAG query ($0.005)
```

**Impact:**
- Without: 100% of queries trigger RAG
- With: 20-40% of queries trigger RAG

**Savings:**
```
Without progressive disclosure:
- 1000 queries × $0.005 = $5.00

With progressive disclosure (30% RAG):
- 700 search × $0 = $0
- 300 RAG × $0.005 = $1.50
- Savings: $3.50 (70%)
```

---

### 3. Query Deduplication (5-10% savings)

**Mechanism:** Detect duplicate/similar queries before calling Perplexity

**Example:**
```python
# Check similarity of new query to recent queries
recent_queries = await cache.get_recent_queries(limit=100)

for past_query in recent_queries:
    similarity = cosine_similarity(
        embed(new_query),
        embed(past_query)
    )

    if similarity > 0.95:  # Nearly identical
        # Return cached response
        return cache.get(past_query)

# New query - call Perplexity
response = await perplexity.query(new_query)
```

**Expected deduplication rate:**
- Same user: 10-15%
- All users: 5-10%

**Savings:** $0.05-0.10/month (small but free)

---

### 4. Rate Limiting (Budget protection)

**Mechanism:** Enforce hard limits to prevent budget overruns

**Limits:**
```
Monthly: 1000 queries max
Daily: 50 queries max (1000 / 20 days)
Hourly: 5 queries per session (prevent abuse)
```

**Protection:**
```python
if monthly_usage >= 1000:
    raise BudgetExceededError("Monthly limit reached")

if daily_usage >= 50:
    raise RateLimitError("Daily limit reached")

if hourly_usage >= 5:
    raise RateLimitError("Hourly limit reached (per session)")
```

**Cost protection:** Guarantees <$5/month

---

## Budget Scenarios

### Scenario 1: Conservative (Base Case)

**Assumptions:**
- 500 total queries/month
- 80% search, 20% RAG (100 RAG queries)
- 50% cache hit rate

**Cost Calculation:**
```
Search queries: 400 × $0 = $0
RAG queries (unique): 50 × $0.005 = $0.25
RAG queries (cached): 50 × $0 = $0
Total: $0.25/month
```

**Budget utilization:** 5% (very safe)

---

### Scenario 2: Moderate (Expected)

**Assumptions:**
- 1000 total queries/month
- 70% search, 30% RAG (300 RAG queries)
- 60% cache hit rate

**Cost Calculation:**
```
Search queries: 700 × $0 = $0
RAG queries (unique): 120 × $0.005 = $0.60
RAG queries (cached): 180 × $0 = $0
Total: $0.60/month
```

**Budget utilization:** 12% (safe)

---

### Scenario 3: Heavy (Pessimistic)

**Assumptions:**
- 1000 total queries/month (rate limit)
- 50% search, 50% RAG (500 RAG queries)
- 40% cache hit rate (lower due to diversity)

**Cost Calculation:**
```
Search queries: 500 × $0 = $0
RAG queries (unique): 300 × $0.005 = $1.50
RAG queries (cached): 200 × $0 = $0
Total: $1.50/month
```

**Budget utilization:** 30% (acceptable)

---

### Scenario 4: Maximum (Worst Case)

**Assumptions:**
- 1000 RAG queries/month (no search)
- 0% cache hit rate (all unique queries)

**Cost Calculation:**
```
RAG queries: 1000 × $0.005 = $5.00
Total: $5.00/month
```

**Budget utilization:** 100% (at limit)

**Likelihood:** <1% (would require caching to completely fail)

---

## Monthly Budget Tracking

### Real-Time Monitoring

**Dashboard Metrics:**
```
┌─────────────────────────────────────────┐
│        Budget Dashboard                 │
├─────────────────────────────────────────┤
│                                         │
│  Current Month: December 2024           │
│                                         │
│  Usage:                                 │
│  [████████░░░░░░░░░] 456/1000 (45.6%)  │
│                                         │
│  Breakdown:                             │
│  • Search queries: 333 (73%)           │
│  • RAG queries: 123 (27%)              │
│                                         │
│  Cost:                                  │
│  $0.62 / $5.00                          │
│                                         │
│  Cache Performance:                     │
│  • Hit rate: 62.4%                     │
│  • Saved: $1.42                        │
│                                         │
│  Projections:                           │
│  • End of month: $1.35 (27%)           │
│  • Days remaining: 15                   │
│  • Avg/day: $0.04                       │
└─────────────────────────────────────────┘
```

---

### Budget Alerts

**Email notifications at key thresholds:**

| Threshold | Action | Example |
|-----------|--------|---------|
| **50%** | Info email | "Halfway through budget ($2.50 used)" |
| **80%** | Warning email | "Approaching limit ($4.00 used)" |
| **90%** | Urgent warning | "Critical: $4.50 used, $0.50 remaining" |
| **95%** | Disable RAG | "Switching to search-only mode" |
| **100%** | Hard stop | "Budget exhausted, wait for next month" |

**Implementation:**
```python
# app/services/budget_service.py
async def check_and_alert(self, usage_percent):
    if usage_percent >= 50 and not self.alert_sent['50']:
        await self.send_email(
            subject="Budget Alert: 50% used",
            body=f"Used {usage_percent}% of monthly budget"
        )
        self.alert_sent['50'] = True

    # Similar for 80%, 90%, 95%
```

---

## Cost Optimization Roadmap

### Phase 4 (Current)
- [x] Basic caching (24h TTL)
- [x] Rate limiting (3-tier)
- [x] Progressive disclosure
- [x] Budget monitoring

**Expected cost:** $1-2/month

---

### Phase 5 (Future Optimizations)

**Option 1: Semantic Cache (Query similarity)**
- Cache based on embedding similarity (not exact match)
- If new query is 95%+ similar to cached query, return cached response
- **Expected savings:** Additional 10-20%

**Option 2: Query Classification**
- Automatically detect if query can be answered by search alone
- Skip RAG for simple "fact lookup" queries
- **Expected savings:** Additional 20-30%

**Option 3: Incremental RAG**
- For follow-up questions, use previous context (don't re-search)
- Reduces Perplexity context size → faster + cheaper
- **Expected savings:** 10-15% on multi-turn conversations

**Option 4: Local LLM (Long-term)**
- Replace Perplexity with local Llama 3.1 8B
- Requires GPU ($50/month cloud GPU or one-time $500 local GPU)
- **Cost:** $0/query (after infrastructure)
- **Break-even:** 10,000 queries/month

---

## Risk Analysis

### Risk 1: Cache Failure

**Scenario:** Redis crashes, all cache lost

**Impact:**
- Cache hit rate drops to 0%
- Cost doubles temporarily (from $1 → $2)

**Mitigation:**
- Redis persistence enabled (AOF)
- Automatic restart (Docker)
- Budget alerts catch spike

**Probability:** 5%
**Impact if occurs:** $1 extra cost (one-time)

---

### Risk 2: User Abuse

**Scenario:** Single user submits 1000 queries in a day

**Impact:**
- Daily rate limit hit (50/day per user)
- Monthly budget exhausted in 20 days

**Mitigation:**
- Hourly rate limit (5/hour per session)
- IP-based blocking (optional)
- CAPTCHA for suspicious activity (Phase 5)

**Probability:** 10%
**Impact if occurs:** Budget limit enforced, no overage

---

### Risk 3: Query Complexity Increase

**Scenario:** Users start asking more complex questions → higher RAG usage

**Impact:**
- RAG % increases from 30% to 60%
- Cost doubles (from $1.50 → $3.00)

**Mitigation:**
- Monitor query patterns
- Educate users on search-first approach
- Add "Did search results help?" prompt before RAG

**Probability:** 20%
**Impact if occurs:** Still within budget ($3 < $5)

---

### Risk 4: Perplexity Price Increase

**Scenario:** Perplexity raises prices from $0.005 to $0.01/query

**Impact:**
- Monthly cost doubles ($1 → $2, or $2 → $4)

**Mitigation:**
- Monitor Perplexity pricing announcements
- Evaluate alternatives (OpenAI, Claude)
- Consider local LLM migration

**Probability:** 30% (within 1 year)
**Impact if occurs:** May need budget increase or local LLM

---

## Budget Allocation Recommendations

### Recommended Monthly Budget: $5

| Allocation | Amount | Purpose |
|------------|--------|---------|
| **Perplexity API** | $1-2 | RAG queries (expected) |
| **Buffer** | $2-3 | Usage spikes, testing |
| **Reserved** | $1 | Emergency / month-end spike |

**Utilization target:** 20-40% ($1-2 actual spend)

**Alert thresholds:**
- 50% ($2.50) - Info
- 80% ($4.00) - Warning
- 90% ($4.50) - Critical

---

## Cost-Benefit Analysis

### Benefits (Value Delivered)

| Benefit | Annual Value | Notes |
|---------|--------------|-------|
| **Time saved** (analysts) | $5,000+ | 5 analysts × 2 hrs/week × $50/hr |
| **Better decisions** | $10,000+ | Improved crop planning, market timing |
| **Knowledge access** | Priceless | Farmers get expert-level answers |

### Costs (Annual)

| Cost | Amount | Notes |
|------|--------|-------|
| **Perplexity API** | $12-24 | $1-2/month × 12 |
| **Development** | $0 | Internal |
| **Maintenance** | $0 | <1 hr/month |
| **TOTAL** | **$12-24/year** | |

### ROI

**Return on Investment:** 200:1 to 400:1

```
ROI = (Annual Benefits - Annual Costs) / Annual Costs
    = ($15,000 - $24) / $24
    = 624:1
```

**Payback period:** <1 week

---

## Conclusion

### Summary

- **Projected monthly cost:** $1-2 (conservative estimate)
- **Budget headroom:** $3-4 (60-80% unused)
- **Risk level:** Low (multiple cost controls)
- **ROI:** 200:1+ (exceptional value)

### Recommendations

1. **Approve $5/month budget** (ample safety margin)
2. **Implement all cost controls** (caching, rate limiting, progressive disclosure)
3. **Monitor weekly** for first month, then monthly
4. **Plan for Phase 5 optimizations** if usage grows

### Go/No-Go Decision

**GO** - Budget is sustainable, risks are managed, value is exceptional.

---

**Prepared by:** APEX Planning Agent
**Date:** December 27, 2024
**Status:** Ready for Approval
