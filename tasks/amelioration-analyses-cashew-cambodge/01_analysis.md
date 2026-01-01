# Analyse: Amelioration Analyses Cashew Cambodge

## Contexte
**Date:** 2026-01-01
**Demande initiale:** Renforcer la credibilite des analyses cashew specifiques au Cambodge avec budget 0 EUR
**Objectif:** Clarifier prix RCN vs kernels, ajouter contexte cambodgien, valider donnees

---

## Etat Actuel de la Codebase

### Fichiers Concernes

| Fichier | Type | Role | Lignes Cles |
|---------|------|------|-------------|
| `app/services/perplexity_service.py` | Service | Recherche Perplexity AI | L36-43 (prompt prices) |
| `app/services/market_trends_service.py` | Service | Analyse et stockage trends | L136-312 (parsing) |
| `app/api/routes/trends.py` | API Route | Endpoints scenarios | L274-410 (scenario prompts) |
| `ui/pages/5_Market_Trends.py` | UI | Affichage trends | L371-422 (labels tendance) |
| `ui/pages/6_Scenario_Analysis.py` | UI | Affichage scenarios | L596-662 (generation) |
| `app/scheduler/jobs.py` | Scheduler | Jobs automatiques | L16-52 (daily analysis) |

---

### Architecture Actuelle

```
                          +-------------------+
                          |   Perplexity AI   |
                          |  (sonar-pro API)  |
                          +--------+----------+
                                   |
                     +-------------v-------------+
                     |  PerplexityService        |
                     |  - research_daily_prices  |
                     |  - analyze_market_trends  |
                     +-------------+-------------+
                                   |
                     +-------------v-------------+
                     |  MarketTrendsService      |
                     |  - _parse_analysis()      |
                     |  - analyze_and_store()    |
                     +-------------+-------------+
                                   |
              +--------------------+--------------------+
              |                                         |
    +---------v---------+                    +----------v----------+
    |   Supabase DB     |                    |   API Routes        |
    | market_trends     |                    | /api/v1/trends/     |
    +-------------------+                    +----------+----------+
                                                        |
              +--------------------+--------------------+
              |                    |                    |
    +---------v--------+  +--------v--------+  +--------v---------+
    | 5_Market_Trends  |  | 6_Scenario      |  | MEF/NBC/CSX      |
    | (Streamlit UI)   |  | (Streamlit UI)  |  | (External APIs)  |
    +------------------+  +-----------------+  +------------------+
```

---

### Code Snippets Cles

#### 1. Prompt Perplexity ACTUEL (perplexity_service.py L36-43)

```python
# PROBLEME: Prompt trop generique, pas de distinction RCN/kernels
prompt = f"""Analyze current market conditions for {commodity} in Cambodia:
1. Latest export prices (USD per ton)
2. Key destination countries (Vietnam, China, Europe)
3. Supply/demand dynamics
4. Geopolitical factors affecting trade
5. Quality grades impact on pricing

Focus on factual data from last 7 days. Include citations."""
```

**Problemes identifies:**
- Pas de distinction RCN (Raw Cashew Nuts) vs Kernels
- Pas de precision FOB vs farmgate
- Pas de mention des grades de qualite (W180, W240, W320)
- Pas de contexte cambodgien specifique

---

#### 2. Parsing Prix ACTUEL (market_trends_service.py L181-184)

```python
# PROBLEME: Extraction prix sans validation de range
price_match = re.search(r'\$?(\d+(?:,\d{3})*)\s*(?:USD)?\s*per\s*ton', response_text, re.IGNORECASE)
if price_match:
    price_str = price_match.group(1).replace(',', '')
    parsed['stock_price_usd'] = float(price_str)
```

**Problemes identifies:**
- Aucune validation des ranges attendus
- Pas de distinction RCN ($1,500-2,500) vs Kernels ($6,000-7,000)
- Prix de $8,500/t affiche sans contexte = confusion

---

#### 3. Prompts Scenarios ACTUELS (trends.py L342-386)

```python
# PROBLEME: Prompts generiques sans contexte cambodgien
scenario_prompts = {
    'pessimistic': f"""As a conservative market analyst, provide a PESSIMISTIC (bearish) analysis for {commodity} market.

{docs_block}{macro_block}Current market data:
- Current price: ${current_price}/ton
- Price change (30 days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Focus on:
1. **Price Outlook**: Downside risks, potential price declines
2. **Risk Factors**: Supply gluts, demand weakness, market headwinds
3. **Bearish Scenarios**: What could go wrong in the next 3-6 months

Be realistic but cautious. Keep response under 300 words.""",
    # ... autres scenarios similaires
}
```

**Problemes identifies:**
- Pas de mention de la position cambodgienne (2e producteur mondial)
- Pas d'integration des indicateurs MEF/NBC/CSX dans l'analyse
- Pas de distinction impact farmers vs traders vs exportateurs

---

#### 4. Labels Tendance UI ACTUELS (5_Market_Trends.py L374-380)

```python
# Labels statiques, pas de validation coherence
trend = latest.get('overall_trend', 'neutral')
trend_emoji = {
    'strong_bullish': '',
    'bullish': '',
    'neutral': '',
    'bearish': '',
    'strong_bearish': ''
}.get(trend, '')
```

**Problemes identifies:**
- Labels ne tiennent pas compte du contenu de l'analyse
- "Tres Haussier" peut etre affiche meme si analyse dit "neutre"
- Pas de verification de coherence

---

### Donnees MEF/NBC/CSX (Deja Integrees)

| Source | Endpoint | Donnees | Usage Actuel |
|--------|----------|---------|--------------|
| MEF | `exchange-rate?currency_id=USD` | Taux USD/KHR | Affichage seulement |
| MEF | `csx-summary` | Resume CSX | Affichage seulement |
| MEF | `csx-index` | Index CSX | Affichage seulement |

**Probleme:** Ces donnees sont affichees mais PAS integrees dans les analyses AI.

---

## Documentation Externe Requise

### Sources Gratuites a Utiliser

| Source | URL | Donnees | Format | Cout |
|--------|-----|---------|--------|------|
| FAO GIEWS | http://www.fao.org/giews/food-prices/ | Prix farmgate mensuels | CSV | Gratuit |
| FAOSTAT | https://www.fao.org/faostat/en/#data | Commerce international | CSV/SDMX | Gratuit |
| WITS | https://wits.worldbank.org/ | Flux trade Cambodge-Vietnam | API | Gratuit |
| CAC | Reports Google Drive | Production par province | PDF | Gratuit |

### Prix de Reference (2024-2025)

| Produit | Fourchette USD/ton | Source |
|---------|-------------------|--------|
| RCN FOB Cambodge | $1,500 - 2,500 | Vietnam Customs, Trade reports |
| Kernels W320 FOB Vietnam | $6,000 - 7,000 | VN Cashew Association |
| Farmgate Cambodge | 3,000 - 5,000 KHR/kg | FAO, Ministry of Agriculture |

---

## Dependances

### Internes
- `perplexity_service.py` -> `market_trends_service.py` (appelle analyze_market_trends)
- `market_trends_service.py` -> `supabase_service.py` (stockage market_trends)
- `trends.py` -> `perplexity_service.py` (appelle _query pour scenarios)
- `5_Market_Trends.py` -> `trends.py` (GET /latest, /history, /analyze)
- `6_Scenario_Analysis.py` -> `trends.py` (POST /scenario)

### Externes (packages)
- `httpx`: Client HTTP async (deja installe)
- `apscheduler`: Scheduler jobs (deja installe)
- `pydantic`: Validation donnees (deja installe)
- Aucun nouveau package requis

---

## Points d'Attention

### 1. Incoherence Prix (CRITIQUE)
- Perplexity retourne parfois $8,500/ton sans preciser si RCN ou kernels
- Utilisateurs confus car prix reels RCN = $1,500-2,500/ton

### 2. Absence Contexte Cambodge (CRITIQUE)
- Position 2e producteur mondial non mentionnee
- Dependance 90% Vietnam pas integree dans analyses
- Impact sur ~500,000 familles pas considere

### 3. MEF/NBC/CSX Sous-Utilises (MOYEN)
- Indicateurs affiches mais pas dans prompts AI
- Taux USD/KHR devrait impacter analyse revenus farmers

### 4. Labels Non Valides (MOYEN)
- Label "Tres Haussier" meme si analyse dit "neutre a +3%"
- Pas de verification coherence contenu vs affichage

---

## Opportunites Identifiees

### 1. Quick Wins (Phase 1 - 10-15 jours)
- Modifier prompts Perplexity pour clarifier RCN/kernels
- Ajouter validation prix avec ranges attendus
- Injecter contexte cambodgien dans prompts scenarios

### 2. Ameliorations Structurelles (Phase 2 - 5-7 jours optionnel)
- Creer ETL FAO GIEWS / FAOSTAT pour donnees officielles
- Scheduler mensuel pour collecte donnees externes

---

## Resume Executif

1. **Prompts Perplexity trop generiques**: Pas de distinction RCN/kernels, pas de contexte cambodgien
2. **Prix affiches sans validation**: $8,500/ton sans preciser le produit = confusion
3. **Indicateurs MEF/NBC/CSX sous-utilises**: Affiches mais pas integres dans analyses AI
4. **Labels UI non coherents**: Peuvent contredire le contenu de l'analyse
5. **Sources externes non exploitees**: FAO, WITS, CAC disponibles gratuitement

**Effort estime Phase 1:** 10-15 jours
**Cout:** $0 (APIs gratuites uniquement)
**Impact attendu:** +80% credibilite analyses cashew Cambodge

---

*Analyse completee le 2026-01-01*
*Pret pour creation 02_plan.md*

---

## ADDENDUM (2026-01-01) - STATE UPDATE AND DATA CONSTRAINTS

### Codebase Updates (Already Implemented)
- Perplexity prompts already enforce RCN vs kernels, FOB vs farmgate, grades.
- Scenario prompts already include Cambodia context and farmer impact requirements.
- Price validation and clarification already added in `app/services/market_trends_service.py`.
- Macro context now injected automatically via `app/services/cambodia_macro_service.py`.
- New config: `app/config.py` includes `mef_realtime_api_url`.

### Remaining Gaps (Phase 2 - Free Sources)
- No collector for FAO GIEWS / FPMA CSV downloads.
- No collector for CAC site (PDF communiques / reports).
- Vietnam Customs has no free API; rely on WITS/Comtrade (annual) + press citations.

### Source Constraints (User Confirmed)
- FAO GIEWS / FPMA: CSV only, needs URL scripting / reverse engineering.
- Vietnam Customs: no free API; use WITS/Comtrade + news sources.
- CAC: free PDFs at https://cac-camcashew.org/.
