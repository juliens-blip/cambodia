# Cambodia Agri Analytics - Data Quality Report

**Generated:** 2025-12-25T21:47:52.906676
**Version:** 1.0.0

## Executive Summary

- **Commodities:** 2
- **Price Records:** 54
- **Production Records:** 31
- **Analyses:** 0
- **Reports:** 0
- **Price Sources:** MEF, WITS
- **Production Sources:** ODC, TEST

## Integrity Checks

### Prices Table

- **Total Records:** 54
- **Null Percentage:** 0.0%
- **Null commodity_id:** 0
- **Null date:** 0
- **Null price_usd_per_unit:** 0
- **Null source:** 0

**Value Validation:**
- Negative prices: 0
- Zero prices: 0
- Outliers (>3σ): 3
- Mean price: $147510.31
- Price range: $32111.38 - $1189958.32

**Unit Consistency:**
- thousand_usd: 54
- usd: 0
- No unit specified: 0

**Duplicates:** 0 potential duplicates found

### Production Table

- **Total Records:** 31

**Data Completeness:**
- Area (hectares): 100.0%
- Production (tons): 100.0%
- Yield (kg/ha): 0.0%
- Geolocation: 0.0%

### Foreign Key Validation

- **Status:** PASS
- **Valid Commodity IDs:** 2
- **Prices Invalid FK:** 0
- **Production Invalid FK:** 0

## Consistency Checks

- **Overlapping Records (MEF vs WITS):** 2
- **High Discrepancy Count (>20%):** 2
- **Average Difference:** 184.24%

## Temporal Continuity

### Price Data Gaps
- **Commodity-Source Combinations:** 3
- **Combinations with Gaps:** 2

### Production Data Gaps
- **Total Combinations:** 11
- **Combinations with Gaps:** 0

## Coverage Metrics

### Price Coverage by Commodity
- **rubber:** 51 records
- **cashew:** 3 records

### Price Coverage by Source
- **MEF:** 48 records
- **WITS:** 6 records

### Temporal Coverage (Prices)
- **Date Range:** 2021-01-01 to 2025-07-01

### Geographic Coverage
- **Total Provinces:** 5
- **Provinces:** Kampong Cham, Kampong Thom, Kratie, Mondulkiri, Ratanakiri

## Recommendations

### Data Coverage - Priority: HIGH
**Issue:** Low price data volume
**Recommendation:** Only 54 price records found. Consider collecting more historical data from MEF and WITS.
**Action:** Extend date range in collectors to fetch 10+ years of data

### Data Coverage - Priority: HIGH
**Issue:** Low production data volume
**Recommendation:** Only 31 production records found. Production data is critical for analysis.
**Action:** Run seed with --include-odc flag, or implement additional scrapers for government agricultural reports

### Temporal Continuity - Priority: MEDIUM
**Issue:** Found 2 commodity-source combinations with date gaps
**Recommendation:** Historical data has gaps. Consider re-collecting data for missing periods.
**Action:** Review gap_details in report and target specific date ranges for re-collection

### Data Coverage - Priority: LOW
**Issue:** Limited data sources (2 sources)
**Recommendation:** Diversify data sources to improve reliability and coverage
**Action:** Add FAO, UNCTAD, or local market price collectors

### Geographic Coverage - Priority: MEDIUM
**Issue:** Limited geographic coverage (5 provinces)
**Recommendation:** Cambodia has 25 provinces. Expand data collection to cover more regions.
**Action:** Search for provincial-level agricultural statistics or KML files for missing provinces

### Data Completeness - Priority: LOW
**Issue:** Low completeness for: yield_kg_per_ha_coverage, geolocation_coverage
**Recommendation:** Enrich production data with missing fields where possible
**Action:** Cross-reference with additional sources or use estimation models for missing values

### Analytics - Priority: HIGH
**Issue:** No AI analyses or reports generated yet
**Recommendation:** Run daily_pipeline to generate Perplexity analyses and Claude reports
**Action:** Execute: python scripts/seed_collectors.py (then wait for scheduled job, or manually trigger daily_pipeline)
