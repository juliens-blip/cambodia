# Data Quality System - Quick Start Guide

## 🚀 Quick Start

### 1. Run Your First Audit

```bash
# From project root
python scripts/audit_data_quality.py
```

**Expected output:**
- Console summary with key metrics
- `reports/data_quality_report.json` (machine-readable)
- `reports/DATA_QUALITY_REPORT.md` (human-readable)

**Runtime:** ~5-10 seconds

### 2. View Results in Dashboard

```bash
# Start dashboard (if not already running)
streamlit run dashboard/app.py

# Navigate to: 🔍 Data Quality page
```

**URL:** http://localhost:8501/Data_Quality

### 3. Review Recommendations

Open `reports/DATA_QUALITY_REPORT.md` and check the **Recommendations** section for prioritized actions.

## 📊 Current Status (2025-12-25)

### Summary
- ✅ **245 price records** (MEF + WITS)
- ❌ **0 production records** (need to run with --include-odc)
- ⚠️ **191 duplicates** (migration needed)
- ⚠️ **190% MEF-WITS discrepancy** (unit issue)

### Quality Score: 92.6/100

**Breakdown:**
- ✅ Completeness: 100% (for price data)
- ✅ Validity: 100% (no invalid values)
- 🟡 Consistency: 85% (MEF vs WITS discrepancy)
- 🟡 Timeliness: 80% (latest data: 2025-07-01)

## 🔧 Fix Critical Issues

### Issue #1: Duplicate Records (HIGH PRIORITY)

**Problem:** 191 duplicate price records found

**Solution:**
```bash
# Apply unique constraint migration
# (Run in Supabase SQL Editor or via CLI)
psql -h <host> -d <db> -f scripts/migrations/001_add_unique_constraint_prices.sql

# Re-seed data (duplicates will be merged)
python scripts/seed_collectors.py
```

### Issue #2: Missing Production Data (HIGH PRIORITY)

**Problem:** 0 production records

**Solution:**
```bash
# Seed with production data included
python scripts/seed_collectors.py --include-odc
```

**Expected result:** ~30-50 sample production records

### Issue #3: MEF vs WITS Discrepancy (MEDIUM PRIORITY)

**Problem:** 190% average difference between MEF and WITS export values

**Root cause:** Unit mismatch (both stored as price_usd_per_unit but MEF uses USD, WITS uses thousand_usd)

**Workaround:** Dashboard already handles this via `metadata.value_unit` check

**Long-term fix:** Normalize all values to base unit (USD) during collection

## 📈 Understanding the Metrics

### Quality Score Components

| Component     | Weight | Current | Target |
|---------------|--------|---------|--------|
| Completeness  | 40%    | 100%    | 95%+   |
| Validity      | 30%    | 100%    | 98%+   |
| Consistency   | 20%    | 85%     | 90%+   |
| Timeliness    | 10%    | 80%     | 90%+   |

### Coverage Metrics

**By Commodity:**
- Rubber: 233 records (95%)
- Cashew: 12 records (5%) ⚠️ Low coverage

**By Source:**
- MEF: 221 records (90%)
- WITS: 24 records (10%)

**Recommendation:** Add more cashew-specific sources

### Temporal Gaps

**WITS data:** 365-day gaps (expected - annual data)
**MEF data:** Continuous monthly data

## 🎯 Next Steps

### Immediate Actions (Today)

1. ✅ Run initial audit (DONE)
2. ⚠️ Apply migration to fix duplicates
3. ⚠️ Seed production data with --include-odc
4. ✅ Review dashboard

### Short-term (This Week)

1. Investigate cashew data gap (only 12 records)
2. Verify GDrive collector for KML/geolocation data
3. Run daily_pipeline to generate AI analyses
4. Set up automated daily audits

### Medium-term (This Month)

1. Add FAO or UNCTAD data sources
2. Normalize unit handling (thousand_usd → usd)
3. Expand geographic coverage (more provinces)
4. Implement automated alerting

## 📁 Files & Locations

### Scripts
- `scripts/audit_data_quality.py` - Main audit script

### Services
- `app/services/data_quality_service.py` - Reusable quality service

### Dashboard
- `dashboard/pages/6_🔍_Data_Quality.py` - Quality monitoring page

### Reports
- `reports/data_quality_report.json` - Latest JSON report
- `reports/DATA_QUALITY_REPORT.md` - Latest Markdown report

### Documentation
- `DATA_QUALITY_SYSTEM.md` - Complete system documentation
- `DATA_QUALITY_QUICKSTART.md` - This file

## 🆘 Troubleshooting

### "No quality report found"

**Solution:** Run the audit script first:
```bash
python scripts/audit_data_quality.py
```

### "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"

**Solution:** Check your `.env` file:
```bash
# Required variables
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx...
```

### "UnicodeEncodeError in console output"

**Cause:** Windows console encoding issue (emoji in output)

**Impact:** None - reports are still generated correctly

**Fix:** Ignore the error or run with output redirection:
```bash
python scripts/audit_data_quality.py 2>nul
```

### Dashboard shows "Error loading data"

**Solution:**
1. Verify API is running: http://localhost:8000/health
2. Check API_URL in `.env`: `API_URL=http://127.0.0.1:8000`
3. Restart dashboard: `Ctrl+C` then `streamlit run dashboard/app.py`

## 💡 Tips

### Run Audit After Every Data Change

```bash
# After seeding
python scripts/seed_collectors.py
python scripts/audit_data_quality.py

# After migration
psql -h <host> -d <db> -f scripts/migrations/001_xxx.sql
python scripts/audit_data_quality.py
```

### Compare Reports Over Time

```bash
# Save timestamped backup
cp reports/data_quality_report.json reports/backup/quality_$(date +%Y%m%d_%H%M%S).json

# Later, compare
diff reports/backup/quality_20251225_120000.json reports/data_quality_report.json
```

### Monitor Quality Score Trend

Track the overall score over time:
```bash
# Extract score from JSON
cat reports/data_quality_report.json | jq '.quality_score.overall'

# Keep a log
echo "$(date): $(cat reports/data_quality_report.json | jq '.quality_score.overall')" >> quality_score_log.txt
```

## 📞 Support

For detailed information, see:
- `DATA_QUALITY_SYSTEM.md` - Full system documentation
- `RESUME_CODEX.md` - Project overview
- `PRODUCTION_DATA_SETUP.md` - Production data guide

---

**Last Updated:** 2025-12-25
**System Version:** 1.0.0
