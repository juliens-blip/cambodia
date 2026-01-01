# Brief pour Agent APEX - Amélioration Analyses Cashew Cambodge

**Date:** 2026-01-01
**Demandeur:** Utilisateur (via Perplexity recommendations)
**Budget:** 0€ (APIs gratuites/freemium uniquement)
**Durée estimée:** 10-15 jours (Phase 1) + 5-7 jours (Phase 2 optionnelle)

---

## 🎯 OBJECTIF GLOBAL

Renforcer la **crédibilité des analyses cajou spécifiques au Cambodge** en :
1. Restant sur un **budget 0€** (APIs gratuites/freemium)
2. Améliorant les **prompts Perplexity**
3. Ajoutant **validation des données**
4. Intégrant **sources officielles gratuites**

---

## 📊 ARCHITECTURE DONNÉES CIBLE (100% Gratuit/Freemium)

### **Sources à Intégrer**

#### 1. **FAO GIEWS / FPMA** (Food Price Monitoring and Analysis)
- **Usage:** Prix domestiques/farmgate, prix de gros, séries mensuelles
- **Accès:** Web + CSV (pas d'API JSON native)
- **Coût:** Gratuit ✅
- **Effort:** Scripts ETL à prévoir
- **URL:** http://www.fao.org/giews/food-prices/home/en/
- **Données clés:**
  - Prix farmgate cashew (si disponible pour Cambodge)
  - Prix de gros marchés locaux
  - Comparaisons régionales (Vietnam, Inde)

#### 2. **FAOSTAT** (Commerce International)
- **Usage:** Statistiques production, commerce (exports/imports par pays)
- **Accès:** Bulk downloads CSV/Excel, API SDMX
- **Coût:** Gratuit ✅
- **URL:** https://www.fao.org/faostat/en/#data
- **Données clés:**
  - Production cashew par pays
  - Exports/imports (HS code 0801.31 RCN, 0801.32 kernels)
  - Prix producteur (quand disponible)

#### 3. **WITS (World Integrated Trade Solution)**
- **Usage:** Flux commerciaux détaillés Cambodge ↔ Vietnam/Chine
- **Accès:** API + Web interface
- **Coût:** Gratuit ✅
- **URL:** https://wits.worldbank.org/
- **Données clés:**
  - Exports Cambodge RCN vers Vietnam (volumes + valeurs)
  - Prix unitaires calculés (valeur/volume)
  - Tendances historiques

#### 4. **MEF / NBC / CSX** (Déjà intégrés ✅)
- **Usage:** Macro-économie cambodgienne
- **Données:**
  - Taux USD/KHR (MEF)
  - CSX Index (conditions financières)
  - Rapports sectoriels (MEF datasets)

#### 5. **CAC (Cambodia Agricultural Cooperatives)**
- **Usage:** Données locales production/exports
- **Accès:** Rapports publics (déjà dans Google Drive)
- **Données clés:**
  - Production: ~850,000 tonnes RCN (2024)
  - Exports: ~815,000 tonnes (90% vers Vietnam)
  - Valeur: $1.15-1.5 milliards USD

#### 6. **TradingEconomics / Commodities-API** (Freemium)
- **Usage:** Prix spot cashew, tendances
- **Accès:** API avec quotas gratuits
- **Coût:** Gratuit (limites: ~500 requests/mois) ✅
- **Données clés:**
  - Prix benchmark kernels W320
  - Tendances prix historiques

---

## 🔧 PHASES D'IMPLÉMENTATION

### **PHASE 1 : Prompts + Validation + Scénarios (10-15 jours)** 🔴 PRIORITÉ

#### 1.1 Refonte Prompts Perplexity

**Fichier:** `app/services/perplexity_service.py`

**Modifications:**

```python
# AVANT
prompt = f"""Analyze current market conditions for {commodity} in Cambodia:
1. Latest export prices (USD per ton)
...
```

**APRÈS:**
```python
prompt = f"""Analyze current market conditions for {commodity} in Cambodia:

🔍 CRITICAL: Always distinguish product types and price segments

**Price Segmentation Requirements:**
1. RCN (Raw Cashew Nuts) vs Kernels (processed)
   - RCN FOB Cambodia: Typical range $1,500-2,500/ton
   - Kernels FOB Vietnam: Typical range $6,000-7,000/ton (W320 grade)

2. FOB vs Farmgate prices
   - FOB = Export price (Sihanoukville port)
   - Farmgate = Price paid to Cambodian farmers (KHR/kg)

3. Quality grades (kernels only)
   - Premium: W180, W240 (larger kernels, higher price)
   - Standard: W320, W450 (smaller kernels, lower price)

**Data Points to Find:**

A) RCN FOB Cambodia (USD/ton)
   - Search: "Cambodia cashew RCN export price" site:customs.gov.kh
   - Search: "Vietnam import cashew Cambodia price" site:customs.gov.vn
   - Fallback: Calculate from Vietnam customs import data

B) Farmgate prices Cambodia (KHR/kg or USD/ton)
   - Search: "Cambodia cashew farmer price" site:agriculture.gov.kh
   - Search: FAO GIEWS Cambodia cashew farmgate
   - Search: USAID/FAO Cambodia agricultural market reports

C) Vietnam kernel prices (USD/ton, by grade)
   - Search: "Vietnam cashew kernel price W320" site:vietnamcashew.org
   - Search: "cashew kernel price Vietnam" site:tradingeconomics.com
   - Specify grade: W180, W240, W320, W450

D) Cambodia context (CRITICAL)
   - Production: ~850,000 tonnes RCN (2024)
   - Exports: ~815,000 tonnes (90% to Vietnam for processing)
   - Position: 2nd global RCN producer (after Ivory Coast)
   - Dependency: Vietnamese processing demand dictates RCN prices

E) Key destinations
   - Vietnam: 90% (processing, then re-export kernels)
   - China: ~5% (direct)
   - Others: ~5%

**Output Format:**
- List ALL prices with EXACT product type, grade, and basis
  ✅ GOOD: "RCN FOB Cambodia: $1,800/ton (source: Vietnam customs Dec 2024)"
  ✅ GOOD: "Kernels W320 FOB Vietnam: $6,500/ton (source: VN Cashew Assoc)"
  ❌ BAD: "Cashew price: $8,500/ton" (what product? what grade?)

- Include date and source for each price point
- If data not found, state clearly: "Data not available for [specific item]"

Focus on factual data from last 7 days. Include citations.
```

#### 1.2 Validation et Clarification Prix

**Fichier:** `app/services/market_trends_service.py`

**Ajouter fonction de validation:**

```python
def _validate_prices_cambodia(self, analysis: Dict) -> Dict:
    """
    Validate price ranges for Cambodia cashew market.

    Expected ranges (2024-2025):
    - RCN FOB Cambodia: $1,500-2,500/ton
    - Kernels W320 FOB Vietnam: $6,000-7,000/ton
    - Farmgate Cambodia: 3,000-5,000 KHR/kg (~$0.75-1.25/kg)
    """

    warnings = []

    # Extract prices from analysis text
    # (regex or LLM parsing)

    # Validate RCN prices
    if rcn_price > 2500:
        warnings.append(f"⚠️ RCN price ${rcn_price}/t seems high (expected $1,500-2,500)")

    # Validate kernel prices
    if kernel_price > 8000:
        warnings.append(f"⚠️ Kernel price ${kernel_price}/t seems high (expected $6,000-7,000)")

    # Add clarification footer
    clarification = """

📌 PRICE REFERENCE GUIDE (Cambodia Cashew)

**Product Types:**
- RCN (Raw Cashew Nuts): Unprocessed, exported to Vietnam
- Kernels: Processed cashew nuts (final product)

**Typical Price Ranges (2024-2025):**
- RCN FOB Cambodia: $1,500-2,500/ton
- Kernels W320 FOB Vietnam: $6,000-7,000/ton
- Farmgate Cambodia: 3,000-5,000 KHR/kg

**Quality Grades (Kernels):**
- W180 (Premium): Largest kernels, highest price
- W240 (Premium): Large kernels
- W320 (Standard): Most traded grade
- W450 (Economy): Smaller kernels, lower price

**Market Structure:**
- Cambodia = 2nd global RCN producer (~850k tons)
- 90% exports to Vietnam for processing
- Price-taker position (Vietnamese demand dictates RCN prices)
    """

    analysis["price_validation_warnings"] = warnings
    analysis["price_clarification"] = clarification

    return analysis
```

#### 1.3 Refonte Scénarios Cambodge

**Fichier:** `app/api/routes/trends.py` (endpoint `/scenario`)

**Template scénarios amélioré:**

```python
cambodia_context_template = """
=== CAMBODIA MARKET POSITION ({commodity.upper()}) ===

**Global Ranking:**
- 2nd largest RCN producer worldwide (~850,000 tonnes/year)
- Share of global production: ~15-18%
- Main competitor: Ivory Coast (1st), India (3rd)

**Export Structure:**
- Total exports: ~815,000 tonnes RCN (2024)
- Destination breakdown:
  * Vietnam: 90% (processing, then re-export as kernels)
  * China: 5% (direct consumption/processing)
  * Others: 5%
- Export value: $1.15-1.5 billion USD

**Processing Capacity:**
- Domestic processing: <10% of production
- Most RCN exported raw (no value addition)
- Opportunity: Build processing capacity to capture margins

**Producer Profile:**
- ~500,000 farming families
- Main provinces: Kampong Thom, Kratie, Mondulkiri
- Avg farm size: 1-3 hectares
- Farmgate price sensitivity: High (livelihood dependent)

**Market Vulnerabilities:**
- Price-taker position: Vietnamese processors dictate RCN prices
- No bargaining power: Limited domestic processing alternatives
- FX exposure: USD/KHR fluctuations affect farmer revenues
- Policy risk: US-Vietnam trade tensions indirectly impact demand

**Macro Indicators (Current):**
- USD/KHR rate: {exchange_rate} ({fx_trend})
- CSX Index: {csx_value} ({csx_change}%)
- Agricultural credit: {credit_conditions}

===

**IMPORTANT:** All scenarios must explicitly discuss impact on:
1. Cambodian farmer revenues (farmgate prices in KHR)
2. Export earnings (RCN volumes × prices)
3. Dependency on Vietnamese demand
4. FX impact (USD/KHR movements)
5. Opportunities for domestic value addition
"""

# Scénarios révisés

optimistic_cambodia = """
## Optimistic Scenario (3-6 months) - Cambodia Perspective

**Global Dynamics:**
- Strong kernel demand (US, EU, China) → +10-15%
- Vietnam processing margins healthy → Aggressive RCN buying
- Supply constraints (Ivory Coast weather) → Tighter RCN market

**Cambodia Impact:**

**Prices:**
- RCN FOB Cambodia: $2,200-2,500/ton (vs $1,800 current)
- Farmgate: 5,500-6,500 KHR/kg (vs 4,500 current) → +22-44% farmer income
- Kernel W320 FOB Vietnam: $6,800-7,200/ton

**Volumes:**
- Production stable/growing: 850k → 900k tonnes (+6%)
- Vietnam demand strong: 90% offtake maintained

**Revenue Impact:**
- Total export value: $1.8-2.25 billion USD (vs $1.25B current) → +44-80%
- Per-farmer income: $3,600-4,500/year (vs $2,500) → Significant livelihood improvement

**FX Context:**
- USD/KHR stable/KHR weakening → Amplifies farmer gains in local currency
- If KHR weakens to 4,100: Farmgate income boost +5-10% additional

**Drivers:**
1. US kernel imports remain strong despite Vietnam tariff concerns
2. China demand accelerates (+20% imports)
3. Ivory Coast crop shortfall (-15%) → Cambodia gains market share
4. Vietnamese processors compete for Cambodian RCN → Price bidding war

**Risks to Upside:**
- Overproduction Ivory Coast/India → RCN glut
- US tariffs on Vietnam kernels → Reduced Vietnamese demand
- KHR strengthening → Erodes farmer gains

**Opportunities:**
- Investment in domestic processing (capture $2,000-3,000/ton kernel margin)
- Certifications (organic, Fair Trade) → Premium prices (+10-20%)
- Direct kernel exports to EU/US → Bypass Vietnam dependency
"""

realistic_cambodia = """
## Realistic Scenario (3-6 months) - Cambodia Perspective

**Global Dynamics:**
- Moderate kernel demand growth (+3-5%)
- Vietnam processing stable, margins under pressure
- Balanced RCN supply globally

**Cambodia Impact:**

**Prices:**
- RCN FOB Cambodia: $1,600-2,000/ton (modest +$200-400 vs current)
- Farmgate: 4,500-5,500 KHR/kg (stable to +10-20%)
- Kernel W320 FOB Vietnam: $6,200-6,800/ton

**Volumes:**
- Production: 850k tonnes (flat)
- Vietnam offtake: 90% maintained (750k tonnes)

**Revenue Impact:**
- Total export value: $1.3-1.6 billion USD → +4-28%
- Per-farmer income: $2,600-3,200/year → Modest improvement

**FX Context:**
- USD/KHR stable (4,000-4,100) → Neutral impact
- Farmgate prices track USD closely

**Market Position:**
- Cambodia remains **primary RCN supplier to Vietnam**
- **Price-taker status unchanged**: Vietnamese demand dictates terms
- **No processing diversification**: <10% domestic value addition

**Drivers:**
1. Steady US/EU kernel consumption (+3-5%)
2. Vietnam processing capacity utilization stable (70-80%)
3. No major supply shocks (weather, policy)
4. Cambodia production plateaus (area expansion slowing)

**Vulnerabilities:**
1. **High dependency**: 90% Vietnam exposure → Single buyer risk
2. **No margin capture**: Export RCN raw → Vietnam captures $3,000-4,000/ton processing margin
3. **FX sensitivity**: USD/KHR swings directly impact farmer purchasing power
4. **Policy transmission**: US-Vietnam trade tensions → Indirect Cambodia impact

**Recommendations:**
1. Develop domestic processing capacity (10% → 30% target)
2. Diversify export markets (China, direct EU/US kernels)
3. Promote certifications (organic, sustainable) for premium pricing
4. Hedging mechanisms for farmers (FX, price floors)

**Baseline Expectation:**
Moderate, stable growth but **persistent structural vulnerabilities** due to lack of value addition and over-reliance on Vietnamese processing demand.
"""

pessimistic_cambodia = """
## Pessimistic Scenario (3-6 months) - Cambodia Perspective

**Global Dynamics:**
- Weak kernel demand (US recession, EU slowdown)
- Vietnam processing margins squeezed → Reduced RCN buying
- RCN oversupply (Ivory Coast + India bumper crops)

**Cambodia Impact:**

**Prices:**
- RCN FOB Cambodia: $1,200-1,500/ton (-25-40% vs current $1,800)
- Farmgate: 2,500-4,000 KHR/kg (-30-45% vs current 4,500) → **Severe farmer distress**
- Kernel W320 FOB Vietnam: $5,500-6,200/ton

**Volumes:**
- Production: 850k tonnes (unchanged, farmers lack alternatives)
- Vietnam offtake drops: 85% (720k tonnes) → 65k tonnes unsold

**Revenue Impact:**
- Total export value: $0.86-1.08 billion USD → **-14-31% vs current**
- Per-farmer income: $1,720-2,160/year → **-31-45% income shock**

**FX Context:**
- If KHR strengthens (3,900): Further erodes farmgate prices in local terms (-5-10% additional)
- If KHR weakens (4,200): Partial offset (+5-10% relief)

**Drivers:**
1. **US tariffs on Vietnam kernels** → Vietnamese processors cut RCN purchases
2. **China demand slump** → -10-15% imports
3. **Ivory Coast/India record crops** → Global RCN glut (+20% supply)
4. **Vietnam shifts to cheaper origins** (Africa) → Cambodia loses market share

**Social Impact:**
- **500,000 farming families** face income crisis
- Rural poverty increases (cashew = primary cash crop)
- Migration to cities accelerates
- Political pressure on government for support

**Cambodian Government Response (Possible):**
- Export subsidies or price floors (limited fiscal space)
- Emergency credit programs for farmers
- Push for domestic processing investments (long-term, not immediate relief)

**Structural Weakness Exposed:**
Despite being **2nd global producer**, Cambodia has:
- **No pricing power** (price-taker, Vietnam-dependent)
- **No value capture** (exports raw, misses $3k-4k/ton processing margin)
- **No buffer** (no strategic reserves, no alternative buyers)

**Mitigation Paths:**
1. **Immediate:** Negotiate guaranteed offtake deals with Vietnam processors
2. **Short-term:** Seek alternative buyers (China direct, India processors)
3. **Medium-term:** Build domestic processing (capture kernel margins)
4. **Long-term:** Diversify agricultural portfolio (reduce cashew dependency)

**Worst-Case Scenario:**
If farmgate drops below 2,500 KHR/kg for extended period:
→ Farmers abandon cashew orchards
→ Production collapses in 2-3 years
→ Cambodia loses 2nd producer status
→ Decades of agricultural investment wasted
"""
```

#### 1.4 Alignement Market Trends ↔ Labels

**Fichier:** `ui/pages/5_Market_Trends.py`

**Corriger logique d'affichage:**

```python
def get_trend_label(analysis_summary: str) -> str:
    """
    Derive trend label from analysis summary.

    Aligns visual label with actual analysis content.
    """

    # Parse analysis for keywords
    if "neutral" in analysis_summary.lower() or "stable" in analysis_summary.lower():
        if "±3%" in analysis_summary or "flat" in analysis_summary:
            return "Stable / Neutre 📊"

    if "bullish" in analysis_summary.lower() or "hausse" in analysis_summary.lower():
        if "modérée" in analysis_summary or "moderate" in analysis_summary:
            return "Légèrement haussier ↗️"
        else:
            return "Haussier 🔼"

    if "bearish" in analysis_summary.lower() or "baisse" in analysis_summary.lower():
        if "modérée" in analysis_summary or "moderate" in analysis_summary:
            return "Légèrement baissier ↘️"
        else:
            return "Baissier 🔽"

    # Default: extract from scenario type
    return "À analyser 🔍"
```

---

### **PHASE 2 : Intégration Sources Gratuites (5-7 jours)** 🟡 OPTIONNEL

#### 2.1 ETL FAO GIEWS/FPMA

**Nouveau fichier:** `app/collectors/fao_giews_collector.py`

```python
class FAOGIEWSCollector:
    """
    Collector for FAO GIEWS Food Price Monitoring data.

    Data: Farmgate and wholesale prices (monthly).
    Source: http://www.fao.org/giews/food-prices/
    Format: CSV bulk downloads (no JSON API)
    """

    async def fetch_cambodia_cashew_prices(
        self,
        start_date: str = "2024-01-01"
    ) -> List[Dict]:
        """
        Fetch Cambodia cashew prices from FAO GIEWS.

        Returns:
            [{
                "date": "2024-12-01",
                "product": "Cashew nuts (RCN)",
                "market": "Phnom Penh wholesale",
                "price_local": 4500,  # KHR/kg
                "price_usd": 1.125,   # USD/kg
                "source": "FAO GIEWS"
            }]
        """
        # Download CSV from FAO GIEWS
        # Parse for Cambodia + cashew
        # Convert to standard format
        pass
```

#### 2.2 ETL FAOSTAT/WITS

**Nouveau fichier:** `app/collectors/faostat_wits_collector.py`

```python
class FAOSTATCollector:
    """
    Collector for FAOSTAT trade data.

    Data: Production, exports, imports by country.
    API: SDMX or bulk CSV downloads
    """

    async def get_cashew_trade_flows(
        self,
        reporter: str = "KHM",  # Cambodia
        partner: str = "VNM",   # Vietnam
        year: int = 2024
    ) -> Dict:
        """
        Get Cambodia → Vietnam cashew trade flows.

        Returns:
            {
                "exports_rcn_tons": 815000,
                "exports_rcn_value_usd": 1_250_000_000,
                "avg_unit_price_usd_per_ton": 1533,
                "imports_kernels_tons": 5000,  # If any
                ...
            }
        """
        pass
```

#### 2.3 Scheduler Jobs Mensuels

**Fichier:** `app/scheduler/jobs.py`

**Ajouter job mensuel:**

```python
def monthly_data_collection():
    """
    Collect data from free sources monthly.

    Runs on 1st of each month.
    """
    print("[SCHEDULER] Starting monthly data collection...", flush=True)

    collectors = [
        fao_giews_collector,
        faostat_collector,
        wits_collector
    ]

    for collector in collectors:
        try:
            data = await collector.collect()
            # Store in Supabase
            print(f"[SCHEDULER] ✅ {collector.name} data collected")
        except Exception as e:
            print(f"[SCHEDULER] ❌ {collector.name} failed: {e}")

# Add to scheduler
scheduler.add_job(
    monthly_data_collection,
    trigger=CronTrigger(day=1, hour=3, minute=0),  # 1st of month, 03:00 UTC
    id="monthly_data_collection",
    name="Monthly Data Collection (FAO, WITS)",
    replace_existing=True
)
```

---

## 📋 CHECKLIST DE LIVRAISON

### Phase 1 (Obligatoire)
- [ ] Prompts Perplexity refondus avec distinctions RCN/kernels/grades
- [ ] Fonction validation prix avec ranges attendus
- [ ] Scénarios cambodgiens détaillés (optimiste/réaliste/pessimiste)
- [ ] Labels Market Trends alignés avec analyses
- [ ] Tests manuels: Trigger analyse → Vérifier clarifications prix
- [ ] Documentation mise à jour

### Phase 2 (Optionnel)
- [ ] Collecteur FAO GIEWS/FPMA opérationnel
- [ ] Collecteur FAOSTAT/WITS opérationnel
- [ ] Job scheduler mensuel configuré
- [ ] Dashboard visualisant données FAO/WITS
- [ ] Tests E2E: Collecte → Stockage → Affichage

---

## 💰 COÛT TOTAL

**Phase 1:** $0 (amélioration code existant)
**Phase 2:** $0 (APIs gratuites uniquement)

**Total:** **$0** ✅

---

## ⏱️ TIMELINE

| Phase | Durée | Tâches Principales |
|-------|-------|--------------------|
| **Phase 1** | 10-15 jours | Prompts, validation, scénarios, alignement |
| **Phase 2** | 5-7 jours | ETL FAO/WITS, scheduler, dashboard |
| **Total** | **15-22 jours** | |

---

## 🎯 MÉTRIQUES DE SUCCÈS

| Métrique | Avant | Après Phase 1 | Après Phase 2 |
|----------|-------|---------------|---------------|
| **Clarté prix** | ❌ Confusion (8500 USD/t) | ✅ RCN $1.5-2.5k, Kernels $6-7k | ✅ + Farmgate KHR |
| **Contexte Cambodge** | ❌ Absent | ✅ 2e producteur, 90% Vietnam mentionné | ✅ + Données provinciales |
| **Validation données** | ❌ Aucune | ✅ Warnings si hors ranges | ✅ + Sources officielles |
| **Cohérence labels** | ❌ "Très haussier" vs "neutre" | ✅ Aligné avec analyse | ✅ |
| **Sources données** | Perplexity seul | Perplexity amélioré | + FAO + WITS + GIEWS |

---

## 🚦 PRÊT POUR /analyze

Ce brief contient toutes les informations nécessaires pour que l'agent APEX lance le workflow `/analyze` puis `/plan`.

**Prochaine étape:** Lancer agent APEX avec ce brief.

---

## ADDENDUM (2026-01-01) - SOURCES GRATUITES CONFIRMEES

### FAO GIEWS / FPMA
- Acces gratuit via FPMA (telechargement CSV depuis l'interface).
- Pas d'API JSON officielle: ETL via scripts + reverse engineering des URLs.
- Reference: https://www.fao.org/giews/food-prices/home/en/
- Price tool: https://www.fao.org/giews/food-prices/price-tool/en/

### Vietnam Customs (imports RCN Cambodge)
- Pas d'API officielle gratuite simple.
- Sources gratuites possibles:
  - WITS / Comtrade pour flux HS 080130 (annuel).
  - Articles citant Vietnam Customs (Vietnamnet, Asemconnect, Vinacas, Tridge, etc.).
- Exemple WITS: https://wits.worldbank.org/trade/comtrade/en/country/All/year/2023/tradeflow/Imports/partner/VNM/product/080130

### CAC (Cashew Association of Cambodia)
- Site et rapports gratuits (PDF/communiques).
- Source: https://cac-camcashew.org/
