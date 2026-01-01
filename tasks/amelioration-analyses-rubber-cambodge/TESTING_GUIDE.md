# Testing Guide: Rubber Cambodia Analysis UI

**Date:** 2026-01-01
**Status:** Phase 3 Complete - Ready for Manual Testing
**Deployment:** https://cambodia.up.railway.app

---

## 🎯 What Was Implemented

### Phase 1: Data Collection ✅
- TradingEconomicsCollector (daily rubber prices)
- WITS HS 4001 rubber exports
- FAO GIEWS rubber with farmgate estimation
- Scheduler jobs (daily 08:00 UTC + monthly)

### Phase 2: Services & Validation ✅
- Rubber price validation (1,700-1,900 USD/ton range)
- Farmgate calculation (70% × FOB × 4,050 KHR)
- Cambodia-specific Perplexity prompts
- Scenario analysis context (production, exports, FX)

### Phase 3: Frontend UI ✅
- Market Trends rubber section
- Scenario Analysis Cambodia Impact

---

## 🧪 Manual Testing Checklist

### Test 1: Market Trends Page (Rubber)

**URL:** https://cambodia.up.railway.app/Market_Trends

**Steps:**
1. Select commodity: **Rubber** (dropdown in sidebar)
2. Scroll to "Latest Analysis - Rubber" section

**Expected Results:**
- ✅ **Twitter Sentiment**: Should show "❓ Non calculé" if tweet_count = 0
  - Help text: "Aucun tweet trouvé - sentiment non disponible"
  - If tweets exist: Shows sentiment emoji + count

- ✅ **Stock Market section** (right column):
  - **Price**: Shows USD/ton price
  - **Conversion**: Shows cents/kg in italics (price / 10)
    - Example: `$1,825/ton` → `*(≈ 182.5 cents/kg)*`
  - **Source caption**: "Source: TradingEconomics / Market data"

- ✅ **Farmgate Estimate (Cambodia)** section:
  - Shows KHR/kg value (e.g., `5,250 KHR/kg`)
  - Shows USD/kg equivalent (e.g., `$1.30 USD/kg`)
  - **Disclaimers**:
    - "⚠️ Estimated from global prices"
    - "(~70% of FOB, based on Thailand -12%)"

**Screenshots to Take:**
- [ ] Full Latest Analysis section (rubber selected)
- [ ] Stock Market price with cents/kg conversion
- [ ] Farmgate Estimate section
- [ ] Twitter sentiment "Non calculé" (if no tweets)

---

### Test 2: Scenario Analysis Page (Rubber - Pessimistic)

**URL:** https://cambodia.up.railway.app/Scenario_Analysis

**Steps:**
1. Select commodity: **Rubber**
2. Click **"📉 Pessimistic Analysis"** tab
3. Wait for analysis to generate (~30-60 seconds)
4. Scroll down to "🇰🇭 Cambodia Impact" section

**Expected Results:**

#### A. Analysis Text
- ✅ AI-generated pessimistic scenario (Perplexity)
- ✅ Mentions Cambodia context:
  - 115,000 tons exports
  - 60% China dependency risk
  - Farmgate price impact
  - Export revenue calculations

#### B. Cambodia Impact Section (After Analysis)

**4 Metrics Row:**
1. ✅ **Export Revenue**
   - Value: `$XXX.X M` (millions USD)
   - Delta: `-15%` (red, negative)
   - Caption: `115,000 tons × $XXX/t`

2. ✅ **Farmgate Price**
   - Value: `X,XXX KHR/kg` (formatted with commas)
   - Delta: `-15%` (red, negative)
   - Caption: `≈ $X.XX/kg`

3. ✅ **Families Affected**
   - Value: `80,000` (formatted)
   - Delta: None
   - Caption: "Kampong Cham, Kratié, Mondulkiri"

4. ✅ **Scenario Price**
   - Value: `$X,XXX/ton` (15% below base)
   - Delta: `-15%` (red, negative)
   - Caption: `Base: $X,XXX/ton`

#### C. Export Destinations Pie Chart
- ✅ **Title**: "🌏 Export Destinations (2024)"
- ✅ **4 Segments**:
  - China: 60% (red) - 72,000 tons
  - Vietnam: 20% (teal) - 24,000 tons
  - Singapore: 10% (blue) - 12,000 tons
  - Others: 10% (green) - 7,000 tons
- ✅ **Donut chart** (hole in center)
- ✅ **Hover**: Shows country, tons, percentage

#### D. FX Sensitivity Table
- ✅ **Title**: "💱 FX Sensitivity (USD/KHR)"
- ✅ **3 Rows**:
  | USD/KHR Rate | Change | Farmgate KHR/kg |
  |--------------|--------|-----------------|
  | 3,950        | -2.5%  | Calculated      |
  | 4,050        | 0%     | Base (bold)     |
  | 4,150        | +2.5%  | Calculated      |
- ✅ **Caption**: "⚠️ Based on scenario price $X,XXX/ton (70% FOB)"

**Screenshots to Take:**
- [ ] Pessimistic analysis text (Cambodia mentions)
- [ ] 4 Metrics row (Export Revenue, Farmgate, Families, Price)
- [ ] Export Destinations pie chart
- [ ] FX Sensitivity table

---

### Test 3: Scenario Analysis Page (Rubber - Realistic)

**URL:** https://cambodia.up.railway.app/Scenario_Analysis

**Steps:**
1. Select commodity: **Rubber**
2. Click **"⚖️ Realistic Analysis"** tab
3. Wait for analysis to generate
4. Scroll to "🇰🇭 Cambodia Impact" section

**Expected Results:**
- ✅ **Metrics deltas**: All show `0%` (no change from base)
- ✅ **Scenario Price**: Same as base price (1.0× multiplier)
- ✅ **FX Table**: Middle row (4,050 KHR) is the base
- ✅ **Pie chart**: Same percentages as pessimistic

**Screenshots to Take:**
- [ ] Realistic scenario Cambodia Impact (0% deltas)

---

### Test 4: Scenario Analysis Page (Rubber - Optimistic)

**URL:** https://cambodia.up.railway.app/Scenario_Analysis

**Steps:**
1. Select commodity: **Rubber**
2. Click **"📈 Optimistic Analysis"** tab
3. Wait for analysis to generate
4. Scroll to "🇰🇭 Cambodia Impact" section

**Expected Results:**
- ✅ **Metrics deltas**: All show `+15%` (green, positive)
- ✅ **Export Revenue**: Higher value (115k tons × +15% price)
- ✅ **Farmgate Price**: Higher KHR/kg (+15%)
- ✅ **Scenario Price**: 15% above base (1.15× multiplier)

**Screenshots to Take:**
- [ ] Optimistic scenario Cambodia Impact (+15% deltas)

---

### Test 5: Compare Cashew vs Rubber

**URL:** https://cambodia.up.railway.app/Scenario_Analysis

**Steps:**
1. Select commodity: **Cashew**
2. Go to any scenario tab
3. Scroll down after analysis
4. Check if "🇰🇭 Cambodia Impact" section appears

**Expected Results:**
- ✅ **Cambodia Impact section**: Should **NOT** appear for cashew
- ✅ Only rubber commodity shows the Cambodia Impact visualization

**Steps:**
1. Switch to commodity: **Rubber**
2. Go to any scenario tab
3. Scroll down after analysis

**Expected Results:**
- ✅ **Cambodia Impact section**: **DOES** appear for rubber
- ✅ Confirms conditional display based on commodity

---

## 📊 Test Data Reference

### Expected Price Ranges (Rubber)
- **Global spot**: 1,700-1,900 USD/ton (TSR20)
- **FOB Cambodia**: 1,750-1,900 USD/ton
- **Farmgate**: 4,500-6,000 KHR/kg (~1.11-1.48 USD/kg)
- **Exchange rate**: 4,050 KHR/USD (base)

### Scenario Multipliers
- **Pessimistic**: 0.85× (-15%)
- **Realistic**: 1.0× (0%)
- **Optimistic**: 1.15× (+15%)

### Cambodia Constants
- **Export volume**: 115,000 tons/year
- **Farming families**: 80,000
- **Main provinces**: Kampong Cham (35%), Kratié (25%), Mondulkiri (20%)
- **Export destinations**:
  - China: 60% (72,000 t)
  - Vietnam: 20% (24,000 t)
  - Singapore: 10% (12,000 t)
  - Others: 10% (7,000 t)

### Farmgate Calculation
```
farmgate_usd_kg = (scenario_price_usd_ton / 1000) × 0.70
farmgate_khr_kg = farmgate_usd_kg × exchange_rate

Example (realistic, base price $1,825/ton):
= (1825 / 1000) × 0.70 = $1.2775/kg
= 1.2775 × 4,050 = 5,174 KHR/kg
```

---

## 🐛 Known Limitations

1. **WebFetch Testing**: Cannot test Streamlit UI via automated tools (requires JavaScript)
2. **API Direct Access**: Railway serves Streamlit on all routes; FastAPI is internal only
3. **Manual Testing Required**: All UI tests must be performed manually in browser

---

## ✅ Code Verification (Completed)

### Files Modified (Phase 3):
1. ✅ `ui/pages/5_Market_Trends.py` (L466-595)
   - Sentiment "Non calculé" fix
   - Price source + cents/kg conversion
   - Farmgate estimate section

2. ✅ `ui/pages/6_Scenario_Analysis.py` (L938-1093, L1189-1221)
   - `display_cambodia_impact_rubber()` function
   - Cambodia Impact section integration
   - Pie chart + FX table

### Backend Endpoints (Phase 2):
- ✅ `/api/v1/trends/latest/rubber` - Returns farmgate fields
- ✅ `/api/v1/trends/scenario/{commodity}` - Cambodia context in prompts

---

## 🎯 Success Criteria

**Test is successful if:**
- [ ] Market Trends shows rubber-specific UI (farmgate, cents/kg)
- [ ] Scenario Analysis shows Cambodia Impact for rubber (not cashew)
- [ ] All 4 metrics display correctly with proper deltas
- [ ] Pie chart renders with 4 segments
- [ ] FX table shows 3 sensitivity rows
- [ ] Calculations match expected formulas

**Test fails if:**
- ❌ Cambodia Impact appears for cashew
- ❌ Metrics show NaN or null values
- ❌ Pie chart missing or malformed
- ❌ FX table has wrong exchange rates
- ❌ Deltas don't match scenario multipliers

---

## 📝 Testing Notes

**Testing Date:** _____________
**Tester:** _____________
**Browser:** _____________
**Issues Found:** _____________

---

**Status:** Ready for manual browser testing ✅
**Deployment:** https://cambodia.up.railway.app
**Documentation:** Complete
