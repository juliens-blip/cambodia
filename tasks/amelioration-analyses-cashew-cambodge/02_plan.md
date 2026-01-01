# Plan d'Implementation: Amelioration Analyses Cashew Cambodge

## Informations
**Date:** 2026-01-01
**Base sur:** 01_analysis.md
**Approche:** Amelioration prompts + validation + contexte cambodgien (Phase 1 uniquement)
**Budget:** $0 (APIs gratuites)

---

## Objectif Final

Transformer les analyses cashew generiques en analyses **specifiques au Cambodge** avec:
1. Distinction claire RCN vs Kernels avec prix valides
2. Contexte cambodgien complet (2e producteur, 90% Vietnam, ~500k familles)
3. Integration MEF/NBC/CSX dans les analyses AI
4. Coherence labels UI avec contenu analyse

---

## Gap Analysis

| Etat Actuel | Etat Cible | Action Requise |
|-------------|------------|----------------|
| Prompt generique "cashew prices" | Prompt specifiant RCN vs kernels, FOB vs farmgate | Modifier `perplexity_service.py` |
| Prix $8,500 affiche sans contexte | Prix avec type produit et validation range | Ajouter validation dans `market_trends_service.py` |
| Scenarios sans contexte Cambodge | Scenarios avec position 2e producteur, impact farmers | Modifier templates dans `trends.py` |
| Labels UI independants du contenu | Labels derives de l'analyse | Ajouter logique validation UI |
| MEF/NBC affichage seulement | MEF/NBC integres dans prompts AI | Modifier construction prompts |

---

## Architecture Proposee

```
                          +-------------------+
                          |   Perplexity AI   |
                          +--------+----------+
                                   |
                     +-------------v-------------+
                     |  PerplexityService        |
                     |  + NOUVEAU PROMPT         |<---- Distinction RCN/Kernels
                     |  + Cambodia Context       |<---- Position 2e producteur
                     +-------------+-------------+
                                   |
                     +-------------v-------------+
                     |  MarketTrendsService      |
                     |  + _validate_prices()     |<---- NOUVEAU: Validation ranges
                     |  + _add_clarification()   |<---- NOUVEAU: Footer explicatif
                     +-------------+-------------+
                                   |
                     +-------------v-------------+
                     |  API Routes (trends.py)   |
                     |  + Cambodia context block |<---- NOUVEAU: Template scenarios
                     |  + MEF/NBC integration    |<---- Injecter macro dans prompts
                     +-------------+-------------+
                                   |
                     +-------------v-------------+
                     |  UI (Market Trends)       |
                     |  + Coherence check        |<---- NOUVEAU: Validation labels
                     +---------------------------+
```

---

## Checklist Technique (Step-by-Step)

### Phase 1.1: Refonte Prompt Perplexity (2-3 jours)

- [ ] **1.1.1** - Modifier `research_daily_prices()` dans `perplexity_service.py` L36-43
  - Action: Remplacer prompt generique par prompt structure avec:
    * Distinction RCN ($1,500-2,500) vs Kernels ($6,000-7,000)
    * Precision FOB vs farmgate
    * Grades de qualite (W180, W240, W320, W450)
    * Contexte cambodgien (2e producteur, 90% Vietnam)
  - Code pattern:
    ```python
    prompt = f"""Analyze current market conditions for {commodity} in Cambodia:

    CRITICAL: Always distinguish product types and price segments

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

    **Cambodia Context (MANDATORY):**
    - 2nd largest RCN producer globally (~850,000 tonnes/year)
    - 90% exports to Vietnam for processing
    - ~500,000 farming families depend on cashew income
    - Price-taker position (Vietnamese demand dictates RCN prices)

    **Data Points to Find:**
    A) RCN FOB Cambodia (USD/ton)
    B) Farmgate prices Cambodia (KHR/kg)
    C) Vietnam kernel prices by grade (USD/ton)
    D) Cambodia export volumes and destinations

    **Output Format:**
    - List ALL prices with EXACT product type, grade, and basis
    - Include date and source for each price point
    - If data not found, state clearly: "Data not available for [specific item]"

    Focus on factual data from last 7 days. Include citations."""
    ```
  - Validation: Nouvelle analyse affiche prix separes RCN/Kernels

- [ ] **1.1.2** - Modifier `analyze_market_trends()` dans `perplexity_service.py` L322-548
  - Action: Ajouter section Cambodia context dans le prompt trends
  - Code pattern: Injecter block contexte avant "INTEGRATED SYNTHESIS"
  - Validation: Analyse trends mentionne position cambodgienne

---

### Phase 1.2: Validation et Clarification Prix (2-3 jours)

- [ ] **1.2.1** - Creer fonction `_validate_prices()` dans `market_trends_service.py`
  - Action: Ajouter apres ligne 312 (fin de _parse_analysis)
  - Code pattern:
    ```python
    def _validate_prices_cambodia(self, parsed: Dict, commodity: str) -> Dict:
        """Validate price ranges for Cambodia cashew market."""
        if commodity != 'cashew':
            return parsed

        warnings = []
        price = parsed.get('stock_price_usd')

        if price:
            # Detect if RCN or Kernels based on price range
            if 1000 <= price <= 3000:
                parsed['price_type'] = 'RCN'
                parsed['price_context'] = 'Raw Cashew Nuts (FOB Cambodia)'
            elif 5000 <= price <= 9000:
                parsed['price_type'] = 'Kernels'
                parsed['price_context'] = 'Processed Kernels (FOB Vietnam)'
            else:
                warnings.append(f"Price ${price}/t outside expected ranges")

            # Validate against expected ranges
            if price > 8000:
                warnings.append(f"High price ${price}/t - likely premium kernels W180/W240")

        # Add clarification footer
        parsed['price_clarification'] = """
    PRICE REFERENCE GUIDE (Cambodia Cashew)

    Product Types:
    - RCN (Raw Cashew Nuts): Unprocessed, exported to Vietnam - $1,500-2,500/ton
    - Kernels: Processed cashew nuts - $6,000-7,000/ton (W320 grade)

    Quality Grades (Kernels):
    - W180 (Premium): Largest kernels, highest price
    - W320 (Standard): Most traded grade
    - W450 (Economy): Smaller kernels, lower price
        """

        parsed['price_warnings'] = warnings
        return parsed
    ```
  - Validation: Parsed data contient price_type et price_context

- [ ] **1.2.2** - Appeler `_validate_prices()` dans `_parse_analysis()` L312
  - Action: Ajouter avant return dans _parse_analysis()
  - Code: `parsed = self._validate_prices_cambodia(parsed, 'cashew')`
  - Validation: Test unitaire validation prix

---

### Phase 1.3: Scenarios Cambodgiens Detailles (3-4 jours)

- [ ] **1.3.1** - Creer template contexte cambodgien dans `trends.py` L274
  - Action: Ajouter avant scenario_prompts
  - Code pattern:
    ```python
    def _build_cambodia_context(commodity: str, exchange_rate=None, csx_data=None) -> str:
        """Build Cambodia-specific context for scenario analysis."""
        if commodity != 'cashew':
            return ""

        context = f"""
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

    **Producer Profile:**
    - ~500,000 farming families
    - Main provinces: Kampong Thom, Kratie, Mondulkiri
    - Farmgate price sensitivity: High (livelihood dependent)

    **Market Vulnerabilities:**
    - Price-taker position: Vietnamese processors dictate RCN prices
    - No bargaining power: Limited domestic processing alternatives
    - FX exposure: USD/KHR fluctuations affect farmer revenues
    """

        if exchange_rate:
            context += f"\n**Current Exchange Rate:** {exchange_rate} KHR/USD"

        if csx_data:
            context += f"\n**CSX Index:** {csx_data}"

        context += """
    ===

    **IMPORTANT:** All scenarios must explicitly discuss impact on:
    1. Cambodian farmer revenues (farmgate prices in KHR)
    2. Export earnings (RCN volumes x prices)
    3. Dependency on Vietnamese demand
    4. Opportunities for domestic value addition
    """
        return context
    ```
  - Validation: Context template genere correctement

- [ ] **1.3.2** - Modifier scenario_prompts dans `trends.py` L341-386
  - Action: Injecter cambodia_context dans chaque scenario
  - Code pattern: Ajouter `{cambodia_context}` apres `{docs_block}{macro_block}`
  - Validation: Scenarios mentionnent 2e producteur, 90% Vietnam

- [ ] **1.3.3** - Ajouter scenarios specifiques Cambodge
  - Action: Creer 3 nouveaux templates scenarios (optimiste/realiste/pessimiste)
  - Code: Voir brief 00_brief.md lignes 275-435
  - Validation: Chaque scenario inclut:
    * Prix RCN et Kernels distincts
    * Impact revenus farmers en KHR
    * Dependance Vietnam
    * Recommandations diversification

---

### Phase 1.4: Alignement Labels Market Trends (2-3 jours)

- [ ] **1.4.1** - Creer fonction validation coherence dans `5_Market_Trends.py`
  - Action: Ajouter apres ligne 370
  - Code pattern:
    ```python
    def validate_trend_label(ai_analysis: str, current_label: str) -> str:
        """Validate that trend label matches AI analysis content."""
        analysis_lower = ai_analysis.lower()

        # Check for explicit trend mentions
        if 'neutral' in analysis_lower or 'stable' in analysis_lower:
            if '+/-3%' in analysis_lower or 'flat' in analysis_lower:
                return 'neutral'

        if 'bullish' in analysis_lower:
            if 'strong' in analysis_lower:
                return 'strong_bullish'
            return 'bullish'

        if 'bearish' in analysis_lower:
            if 'strong' in analysis_lower:
                return 'strong_bearish'
            return 'bearish'

        # Default to current if no explicit mention
        return current_label
    ```
  - Validation: Labels corriges si incoherence detectee

- [ ] **1.4.2** - Appeler validation dans affichage trend L384-388
  - Action: Valider label avant affichage
  - Code:
    ```python
    ai_analysis = latest.get('ai_analysis', '')
    validated_trend = validate_trend_label(ai_analysis, trend)
    trend = validated_trend
    ```
  - Validation: Test avec analyse "neutre" ne montre pas "Tres Haussier"

---

### Phase 1.5: Tests et Validation (2-3 jours)

- [ ] **1.5.1** - Test manuel: Trigger analyse cashew
  - Action: POST /api/v1/trends/analyze/cashew?force_refresh=true
  - Verification:
    * Prix RCN distinct de Kernels
    * Contexte cambodgien present
    * Clarification prix en footer

- [ ] **1.5.2** - Test manuel: Generation scenarios
  - Action: POST /api/v1/trends/scenario/cashew
  - Verification:
    * Mention 2e producteur mondial
    * Impact farmers en KHR
    * Dependance Vietnam

- [ ] **1.5.3** - Test UI: Page Market Trends
  - Action: Naviguer vers /Market_Trends
  - Verification:
    * Labels coherents avec analyse
    * Prix clarifies
    * Indicateurs MEF affiches

- [ ] **1.5.4** - Test UI: Page Scenario Analysis
  - Action: Naviguer vers /Scenario_Analysis
  - Verification:
    * 3 scenarios avec contexte Cambodge
    * Prix RCN/Kernels distincts
    * Recommandations pertinentes

---

## Commandes a Executer

```bash
# Demarrer environnement local (optionnel)
cd D:\Projects\cambodia
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Lancer API en local pour tests
uvicorn app.main:app --reload --port 8000

# Lancer UI Streamlit pour tests
streamlit run ui/Home.py --server.port 8501

# Test API endpoint
curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true"

# Git commit apres chaque phase
git add .
git commit -m "feat: Phase 1.X - [description]"
```

---

## Risques Identifies

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Perplexity ne trouve pas prix RCN specifiques | Moyen | Fallback sur ranges valides + clarification |
| Prompts trop longs (>4000 tokens) | Faible | Optimiser templates, garder essentiel |
| Latence API augmentee | Faible | Cache existant suffit |
| Regression fonctionnalites existantes | Moyen | Tests manuels apres chaque modification |

---

## Points de Validation

- [ ] Code compile sans erreur Python
- [ ] API repond correctement (200 OK)
- [ ] UI Streamlit charge sans erreur
- [ ] Prix RCN et Kernels distingues dans analyses
- [ ] Contexte cambodgien present dans scenarios
- [ ] Labels coherents avec contenu analyse
- [ ] Pas de regression sur rubber analysis

---

## Estimation

- **Complexite:** Moyenne
- **Fichiers modifies:** 4 fichiers
  - `app/services/perplexity_service.py`
  - `app/services/market_trends_service.py`
  - `app/api/routes/trends.py`
  - `ui/pages/5_Market_Trends.py`
- **Fichiers crees:** 0 (modification uniquement)
- **Dependencies:** 0 (aucun nouveau package)

---

## Pret pour Implementation

- [x] Analyse complete (01_analysis.md)
- [ ] Plan valide par l'utilisateur
- [x] Toutes les dependances identifiees
- [x] Strategie claire et sans ambiguite

---

*Plan cree le 2026-01-01*
*En attente validation utilisateur avant implementation*

---

## ADDENDUM (2026-01-01) - PLAN UPDATE FOR FREE SOURCES (PHASE 2)

### Status Update
- Phase 1 (prompts, price validation, scenario context, macro injection) is already implemented in code.
- Remaining work focuses on free-source ETL and data ingestion.

### Phase 2: Free Sources Integration (FAO GIEWS/FPMA, CAC, WITS/Comtrade)

- [ ] **2.1** - Create collector `app/collectors/fao_giews_collector.py`
  - Use FPMA API JSON when CSV is not available.
  - FPMA endpoints:
    - `FpmaSerie?commodity=<id>&iso3_country_code=KHM`
    - `FpmaSeriePrice?uuid__in=<uuid1,uuid2>`
  - Parse for Cambodia + cashew (if missing, log "no data").
  - Normalize to `prices` table with metadata:
    - source: `FAO_GIEWS`
    - price_type: `farmgate` or `wholesale`
    - unit: `KHR/kg` or `USD/ton`.
  - Keep CSV fallback (configurable URLs).

- [ ] **2.2** - Create collector `app/collectors/cac_collector.py`
  - Scrape https://cac-camcashew.org/ for PDF/communique links.
  - Crawl report/news pages to find PDF attachments.
  - Download PDFs and store as `context_documents` (for semantic search).
  - Reuse existing PDF parsing logic (from GDrive collector) where possible.
  - Include metadata: source `CAC`, title, date, url.

- [ ] **2.3** - WITS/Comtrade alignment for Vietnam flows
  - Ensure WITS data focuses on HS 080130 (RCN) and partner VNM.
  - Use Download.aspx HS6 export if SDMX rejects 080130.
  - Store annual flow data and unit values as metadata.
  - Add prompt guidance: WITS/Comtrade is annual and not real-time.

- [ ] **2.4** - Update prompts to reflect data latency
  - Add a short disclaimer in Perplexity prompts:
    - Vietnam Customs data is indirect (WITS/Comtrade, press citations).
    - FAO GIEWS is monthly, not daily.

- [ ] **2.5** - Scheduler job (monthly)
  - Add a monthly job to run FAO + CAC collectors.
  - Use existing scheduler pattern in `app/scheduler/jobs.py`.

### Validation (Phase 2)
- [ ] Run FAO collector once and verify new `prices` rows (or "no data" if FPMA lacks Cambodia cashew).
- [ ] Run CAC collector and verify `context_documents` entries.
- [ ] Trigger indexation and verify CAC docs are searchable.

### Notes
- No paid APIs required.
- Vietnam Customs remains indirect via WITS/Comtrade and news citations.
