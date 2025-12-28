# Bug Fix - Rate Limiter Blocking GET Requests

**Date:** 2025-12-27 14:15:00
**Issue:** Market Trends page showing 500 errors
**Status:** ✅ FIXED

---

## Problem

Users were getting 500 Internal Server Error when accessing Market Trends page:

```
GET /api/v1/trends/latest/cashew HTTP/1.1" 500 Internal Server Error
GET /api/v1/trends/history/cashew?days=30 HTTP/1.1" 500 Internal Server Error
```

**Error Message:**
```
Rate limit exceeded
Hourly limit exceeded (5 queries/hour)
```

---

## Root Cause

The rate limiter middleware was counting **ALL** requests (including GET requests) towards the limit.

**Original Code:**
```python
async def dispatch(self, request: Request, call_next):
    # Skip rate limiting for health check and docs
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    # THIS WAS COUNTING ALL REQUESTS (INCLUDING GET)
    allowed, reason = self.rate_limiter.check_limits(session_id)
    if not allowed:
        raise HTTPException(status_code=429, ...)
```

**Impact:**
- GET requests (read-only, no cost) were being rate limited
- After 5 requests/hour, ALL endpoints (including free ones) were blocked
- Users couldn't view trends, stats, history, etc.

---

## Solution

Exempt all GET requests from rate limiting, since they:
1. Don't cost money (no API calls to Perplexity)
2. Are read-only operations
3. Just query the database

**Fixed Code:**
```python
async def dispatch(self, request: Request, call_next):
    # Skip rate limiting for:
    # 1. Health check and docs
    # 2. All GET requests (read-only, no cost)
    # 3. Stats endpoint
    exempt_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/", "/stats"]

    if request.url.path in exempt_paths or request.method == "GET":
        return await call_next(request)

    # Only rate limit POST endpoints that cost money:
    # - /api/v1/rag/query ($0.005)
    # - /api/v1/trends/analyze/* ($0.005)
```

---

## What's Now Rate Limited

**Still Rate Limited (POST endpoints that cost money):**
- ✅ `POST /api/v1/rag/query` - $0.005 per query (Perplexity API)
- ✅ `POST /api/v1/trends/analyze/{commodity}` - $0.005 per analysis (Perplexity API)
- ✅ `POST /api/v1/search` - Free but rate limited for abuse protection

**Now Exempt (GET endpoints - no cost):**
- ✅ `GET /api/v1/stats` - Budget stats
- ✅ `GET /api/v1/history` - Conversation history
- ✅ `GET /api/v1/trends/summary` - Trends summary
- ✅ `GET /api/v1/trends/latest/{commodity}` - Latest trend
- ✅ `GET /api/v1/trends/history/{commodity}` - Historical trends
- ✅ `GET /api/v1/trends/alerts` - Active alerts
- ✅ `GET /health` - Health check
- ✅ `GET /docs` - API documentation

---

## Testing

**Before Fix:**
```bash
# 1st request - OK
curl http://localhost:8000/api/v1/trends/latest/cashew
# Returns data

# After 5 requests...
curl http://localhost:8000/api/v1/trends/latest/cashew
# 500 Error: Rate limit exceeded
```

**After Fix:**
```bash
# Unlimited GET requests
for i in {1..100}; do
  curl http://localhost:8000/api/v1/trends/latest/cashew
done
# All succeed! ✅
```

---

## Impact

**Positive:**
- Users can view trends unlimited times (GET requests)
- Only POST endpoints that cost money are rate limited
- Better user experience
- No unnecessary restrictions on free operations

**Budget Protection Still Works:**
- POST /api/v1/rag/query still limited to 5/hour (costs $0.005)
- POST /api/v1/trends/analyze/* still limited to 5/hour (costs $0.005)
- Monthly budget protection remains active

---

## Rate Limits After Fix

```
GET Requests (FREE, UNLIMITED):
├─ /api/v1/stats
├─ /api/v1/history
├─ /api/v1/trends/summary
├─ /api/v1/trends/latest/*
├─ /api/v1/trends/history/*
├─ /api/v1/trends/alerts
└─ /health, /docs, etc.

POST Requests (RATE LIMITED):
├─ /api/v1/rag/query          5/hour, 50/day, 1000/month ($0.005)
├─ /api/v1/trends/analyze/*   5/hour, 50/day, 1000/month ($0.005)
└─ /api/v1/search             5/hour, 50/day, 1000/month (FREE but limited)
```

---

## Files Modified

**File:** `app/middleware/rate_limiter.py`
**Lines:** 121-159
**Changes:** Added `request.method == "GET"` exemption

---

## Verification

**Test Endpoints:**
```bash
# These should work unlimited times now:
curl http://localhost:8000/api/v1/stats
curl http://localhost:8000/api/v1/trends/summary
curl http://localhost:8000/api/v1/trends/latest/cashew
curl http://localhost:8000/api/v1/trends/history/cashew?days=30
curl http://localhost:8000/api/v1/trends/alerts

# These are still rate limited:
curl -X POST http://localhost:8000/api/v1/rag/query -d '{"query":"test"}'
curl -X POST http://localhost:8000/api/v1/trends/analyze/cashew
```

---

## API Restart Required

After deploying this fix, restart the API server:

```bash
# Kill old process
# Ctrl+C or pkill -f uvicorn

# Start new one
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

**Status:** ✅ FIXED
**Deployed:** 2025-12-27 14:15:00
**Verified:** Market Trends page now works correctly
