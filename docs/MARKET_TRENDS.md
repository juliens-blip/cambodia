# Market Trends Monitoring System

**Version:** 1.0
**Status:** ✅ Complete
**Cost:** ~$0.30/month ($0.01/day)

## Overview

The Market Trends Monitoring System analyzes Twitter/X sentiment and stock market data daily to provide real-time market intelligence for cashew and rubber commodities in Cambodia.

## Features

### 1. Daily Automated Analysis
- **Twitter/X Sentiment** (last 48 hours)
  - Sentiment classification (bullish/bearish/neutral)
  - Tweet volume tracking
  - Top influential tweets extraction
  - Key themes identification

- **Stock Market Data**
  - Current commodity prices (USD per ton)
  - Price changes (24h, 7d, 30d)
  - Trading volume trends
  - Historical comparisons

- **Combined AI Analysis**
  - Overall trend classification:
    - 📈🔥 Strong Bullish (>+7% expected)
    - 📈 Bullish (+3% to +7%)
    - ➡️ Neutral (-3% to +3%)
    - 📉 Bearish (-3% to -7%)
    - 📉💥 Strong Bearish (<-7% expected)
  - Confidence scoring (0.0-1.0)
  - Key market drivers
  - Actionable insights

### 2. Automated Alerts
Alerts are automatically generated when:
- **Price Spikes:** Changes >5%
  - Critical: >10%
  - High: 7-10%
  - Medium: 5-7%
- **Sentiment Shifts:** Bearish sentiment with high confidence (>0.7)
- **High Volatility:** Unusual market movements

### 3. Historical Tracking
- 30-90 day trend history
- Sentiment evolution charts
- Price change visualization
- Confidence score tracking

## Architecture

### Database Schema
**Tables:**
- `market_trends` - Daily trend analysis storage
- `trend_alerts` - Automated alert notifications

**Views:**
- `latest_trends` - Most recent trend per commodity
- `trend_history` - Last 30 days of trends
- `sentiment_summary` - Aggregated sentiment statistics

**Functions:**
- `get_latest_trend(commodity)` - Fetch latest analysis
- `create_trend_alert()` - Generate alerts
- `get_unread_alerts()` - Retrieve active alerts

**Triggers:**
- `auto_generate_alerts()` - Automated alert creation on new trends

### Services

**PerplexityService** (`app/services/perplexity_service.py`)
- `analyze_market_trends()` - Comprehensive Twitter + stock analysis
- `analyze_twitter_sentiment()` - Focused Twitter analysis

**MarketTrendsService** (`app/services/market_trends_service.py`)
- `analyze_and_store_trends()` - Main workflow orchestration
- `_parse_analysis()` - AI response parsing
- `get_latest_trend()` - Data retrieval
- `get_trend_history()` - Historical data
- `get_unread_alerts()` - Alert management
- `mark_alert_read()` - Alert acknowledgment

### API Endpoints

**Base URL:** `/api/v1/trends`

#### GET `/latest/{commodity}`
Get the most recent trend analysis for a commodity.

**Response:**
```json
{
  "commodity": "cashew",
  "trend_date": "2024-12-27",
  "twitter_sentiment": "bullish",
  "twitter_volume": 156,
  "stock_change_pct": 3.2,
  "overall_trend": "bullish",
  "confidence_score": 0.75,
  "ai_analysis": "...",
  "key_factors": ["...", "..."]
}
```

#### GET `/history/{commodity}?days=30`
Get historical trend data for charting.

**Parameters:**
- `days` (optional): 1-90, default: 30

**Response:**
```json
{
  "commodity": "cashew",
  "days": 30,
  "count": 25,
  "data": [...]
}
```

#### POST `/analyze/{commodity}?force_refresh=false`
Trigger new trend analysis (costs $0.005).

**Parameters:**
- `force_refresh` (optional): Skip today's check, default: false

**Response:**
```json
{
  "status": "success",
  "data": {...},
  "message": "New trend analysis completed for cashew"
}
```

#### GET `/alerts`
Get unread market alerts.

**Response:**
```json
{
  "count": 3,
  "alerts": [
    {
      "id": "uuid",
      "commodity": "rubber",
      "alert_type": "price_spike",
      "severity": "high",
      "message": "rubber price changed by +7.5% on 2024-12-27",
      "created_at": "2024-12-27T09:15:00Z"
    }
  ]
}
```

#### POST `/alerts/{alert_id}/read`
Mark an alert as read.

**Response:**
```json
{
  "status": "success",
  "message": "Alert marked as read"
}
```

#### GET `/summary`
Get summary of all commodities' latest trends.

**Response:**
```json
{
  "commodities": {
    "cashew": {
      "trend_date": "2024-12-27",
      "overall_trend": "bullish",
      "twitter_sentiment": "bullish",
      "confidence_score": 0.75,
      "stock_change_pct": 3.2
    },
    "rubber": {...}
  },
  "alerts_count": 2,
  "last_updated": "2024-12-27"
}
```

## UI Integration

### Admin Dashboard (`ui/pages/4_📊_Admin.py`)
Shows market trends summary:
- Latest trend for each commodity
- Sentiment indicators
- Price changes
- Active alerts (top 5)

### Market Trends Page (`ui/pages/5_📈_Market_Trends.py`)
Dedicated trends analysis page with:
- Latest analysis display
- Historical trend charts
- Alert notifications
- Manual analysis trigger

**Features:**
- Commodity selector (cashew/rubber)
- History range slider (7-90 days)
- Auto-refresh option (60s)
- Interactive charts (Plotly)
- Manual trigger button

## Daily Automation

### Script: `scripts/daily_market_trends.py`

**Purpose:** Automated daily market analysis

**Schedule:**
```bash
# Recommended cron schedule (9:00 AM daily)
0 9 * * * cd /path/to/cambodia && python scripts/daily_market_trends.py
```

**Windows Task Scheduler:**
```
Program: python
Arguments: D:\Projects\cambodia\scripts\daily_market_trends.py
Start in: D:\Projects\cambodia
Trigger: Daily at 9:00 AM
```

**Process:**
1. Analyzes both commodities (cashew, rubber)
2. Skips if already analyzed today
3. Stores results in database
4. Generates alerts automatically
5. Reports costs and budget

**Output:**
```
================================================================================
Daily Market Trends Analysis
Date: 2024-12-27 09:00:00
================================================================================

1. Initializing services...
   Services initialized

2. Analyzing cashew market trends...
   - Searching Twitter/X (last 48h)...
   - Fetching stock market data...
   - Generating AI analysis...
   COMPLETED:
      - Sentiment: bullish
      - Overall trend: bullish
      - Confidence: 0.75
      - Tweet volume: 156
      - Price change: +3.20%

3. Analyzing rubber market trends...
   COMPLETED: ...

4. Checking for market alerts...
   ALERTS: 2 unread alerts
   ⚠️ [HIGH] rubber price changed by +7.5%

================================================================================
DAILY ANALYSIS SUMMARY
================================================================================

Commodities analyzed: 2
   - Success: 2
   - Skipped (already done): 0
   - Failed: 0

Cost:
   - Today: $0.010
   - Monthly estimate: $0.30 (if run daily)

Perplexity Budget:
   - Used this month: 2/1000
   - Remaining: 998
   - Utilization: 0.2%

================================================================================
✅ Daily analysis complete!
```

## Installation & Setup

### 1. Apply Database Migration

**Via Supabase SQL Editor:**
```sql
-- Copy and execute supabase/migrations/005_market_trends.sql
```

**Verify Migration:**
```bash
python scripts/verify_migration_005.py
```

Expected output:
```
================================================================================
Migration 005 Verification - Market Trends Monitoring
================================================================================

1. Connecting to Supabase...
   ✅ Connected

2. Verifying tables...
   ✅ Table 'market_trends' exists
   ✅ Table 'trend_alerts' exists

3. Verifying views...
   ✅ View 'latest_trends' exists
   ✅ View 'trend_history' exists
   ✅ View 'sentiment_summary' exists

4. Verifying functions...
   ✅ Function 'get_latest_trend()' works
   ✅ Function 'get_unread_alerts()' works

...

✅ Migration 005 verified successfully!
```

### 2. Update Environment Variables

Ensure `.env` contains:
```bash
# Perplexity API
PERPLEXITY_API_KEY=pplx-xxxxx

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

### 3. Update FastAPI Application

Already integrated in `app/main.py`:
```python
from app.api.routes import trends
app.include_router(trends.router, tags=["Market Trends"])
```

### 4. Test Endpoints

Start the API:
```bash
uvicorn app.main:app --reload
```

Test endpoints:
```bash
# Get latest trend
curl http://localhost:8000/api/v1/trends/latest/cashew

# Get history
curl http://localhost:8000/api/v1/trends/history/cashew?days=30

# Trigger analysis (costs $0.005)
curl -X POST http://localhost:8000/api/v1/trends/analyze/cashew

# Get alerts
curl http://localhost:8000/api/v1/trends/alerts

# Get summary
curl http://localhost:8000/api/v1/trends/summary
```

### 5. Setup Daily Automation

**Option A: Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Cambodia Agri - Daily Market Trends"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
   - Program: `python`
   - Arguments: `D:\Projects\cambodia\scripts\daily_market_trends.py`
   - Start in: `D:\Projects\cambodia`

**Option B: Cron (Linux/Mac)**
```bash
crontab -e

# Add this line:
0 9 * * * cd /path/to/cambodia && /path/to/python scripts/daily_market_trends.py >> logs/daily_trends.log 2>&1
```

## Cost Analysis

### Daily Costs
- Cashew analysis: $0.005
- Rubber analysis: $0.005
- **Total per day:** $0.010

### Monthly Costs
- Daily runs (30 days): $0.30
- Manual triggers (estimate 10): $0.05
- **Total per month:** ~$0.35

### Budget Safety
- Monthly budget: $5.00
- Trends utilization: 7% ($0.35 / $5.00)
- **Remaining for RAG:** $4.65 (930 queries)

## Usage Examples

### Example 1: View Latest Trends

**Streamlit UI:**
1. Navigate to "📈 Market Trends"
2. Select commodity (cashew/rubber)
3. View latest analysis with:
   - Overall trend indicator
   - Twitter sentiment
   - Price changes
   - Confidence score
   - Key factors
   - Top tweets

### Example 2: Check Historical Trends

**API:**
```python
import httpx

# Get 30-day history
response = httpx.get(
    "http://localhost:8000/api/v1/trends/history/cashew",
    params={"days": 30}
)

history = response.json()

# Plot sentiment over time
import pandas as pd
import plotly.express as px

df = pd.DataFrame(history['data'])
df['trend_date'] = pd.to_datetime(df['trend_date'])

fig = px.line(
    df,
    x='trend_date',
    y='confidence_score',
    title='Cashew Market Confidence'
)
fig.show()
```

### Example 3: Manual Trigger

**When to use:**
- Breaking news event
- Urgent market update needed
- Daily automation failed
- Testing new analysis

**Cost:** $0.005 per trigger

**API:**
```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/trends/analyze/cashew",
    params={"force_refresh": True}
)

result = response.json()

if result['status'] == 'success':
    print(f"Analysis complete!")
    print(f"Trend: {result['data']['overall_trend']}")
    print(f"Sentiment: {result['data']['twitter_sentiment']}")
```

**Streamlit UI:**
1. Go to "📈 Market Trends"
2. Scroll to "🔄 Manual Analysis"
3. Check "Force refresh" if needed
4. Click "🚀 Trigger New Analysis"
5. Wait 5-10 seconds
6. View updated results

### Example 4: Monitor Alerts

**API:**
```python
import httpx

# Get unread alerts
response = httpx.get("http://localhost:8000/api/v1/trends/alerts")
alerts = response.json()

for alert in alerts['alerts']:
    severity = alert['severity']
    message = alert['message']

    if severity == 'critical':
        send_notification(message)  # Your notification system

    # Mark as read
    httpx.post(f"http://localhost:8000/api/v1/trends/alerts/{alert['id']}/read")
```

**Streamlit UI:**
1. Alerts shown on Admin Dashboard
2. Alerts shown on Market Trends page
3. Color-coded by severity:
   - 🚨 Critical (red)
   - ⚠️ High/Medium (yellow)
   - ℹ️ Low (blue)

## Troubleshooting

### Issue: No trend data found

**Cause:** Migration not applied or no analysis run yet

**Solution:**
1. Verify migration: `python scripts/verify_migration_005.py`
2. Run manual analysis: POST `/api/v1/trends/analyze/{commodity}`

### Issue: API returns 500 error

**Cause:** Perplexity API key missing or invalid

**Solution:**
1. Check `.env` file has `PERPLEXITY_API_KEY`
2. Verify key is valid on Perplexity dashboard
3. Check service logs for detailed error

### Issue: Alerts not generating

**Cause:** Trigger not working or threshold not met

**Solution:**
1. Verify trigger exists: Check migration 005 applied
2. Check alert thresholds:
   - Price spike: >5%
   - Sentiment: bearish with confidence >0.7
3. Test with manual extreme values

### Issue: Daily script fails

**Cause:** Environment issues or API errors

**Solution:**
1. Run manually to see errors: `python scripts/daily_market_trends.py`
2. Check Perplexity budget not exceeded
3. Verify network connectivity
4. Check logs for detailed errors

## Future Enhancements

### Phase 1 (Priority)
- [ ] WhatsApp/Telegram alert notifications
- [ ] SMS alerts for critical events
- [ ] Email digest (weekly summary)
- [ ] Export to PDF/Excel

### Phase 2 (Nice to Have)
- [ ] Multi-language AI analysis (Khmer translation)
- [ ] Competitor tracking (Vietnam, Thailand)
- [ ] Weather impact correlation
- [ ] Seasonal pattern recognition
- [ ] Predictive forecasting (ML models)

### Phase 3 (Advanced)
- [ ] Real-time streaming (WebSocket)
- [ ] Custom alert rules (user-defined)
- [ ] Integration with trading platforms
- [ ] Advanced sentiment analysis (FinBERT)
- [ ] News aggregation from multiple sources

## Technical Specifications

### Dependencies
- `perplexity-api` - AI analysis
- `supabase-py` - Database
- `fastapi` - API framework
- `streamlit` - UI framework
- `plotly` - Charts
- `pandas` - Data manipulation

### Performance
- Analysis time: 5-10 seconds per commodity
- API response time: <100ms (cached), <3s (live)
- Database queries: <50ms
- UI load time: <2s

### Scalability
- Current: 2 commodities
- Max: 100+ commodities (with budget increase)
- Rate limit: 1000 analyses/month (Perplexity limit)
- Storage: ~1MB per commodity per year

### Security
- API rate limiting (3-tier)
- Budget constraints ($5/month)
- Read-only database views
- Parameterized queries (SQL injection protection)

## Support

### Documentation
- This file: `/docs/MARKET_TRENDS.md`
- API docs: `http://localhost:8000/docs#/Market%20Trends`
- Migration: `/supabase/migrations/005_market_trends.sql`

### Contact
For questions or issues, check:
1. API documentation (`/docs`)
2. Verification script output
3. Service logs
4. Supabase dashboard

---

**Version:** 1.0
**Last Updated:** 2024-12-27
**Status:** ✅ Production Ready
