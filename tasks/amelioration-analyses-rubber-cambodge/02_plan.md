# Plan d'Implémentation: Amélioration Analyses Rubber Cambodge

## 📋 Informations

**Date:** 2026-01-01
**Basé sur:** 01_analysis.md
**Approche:** Délégation agents spécialisés (backend, frontend, data)
**Budget:** 0€ (sources gratuites uniquement)
**Durée estimée:** 10-12 jours

---

## 🎯 Objectif Final

Implémenter un système complet d'analyse rubber pour le Cambodge avec :
1. ✅ Prix spot global (TradingEconomics scraping)
2. ✅ Contexte Cambodia (2e producteur, 60% exports Chine)
3. ✅ Validation prix (ranges 1,700-1,900 USD/ton)
4. ✅ Scénarios Cambodia-specific (impact revenus farmers)
5. ✅ Sources gratuites (FAO, WITS, CAC, TradingEconomics)

---

## 📊 Gap Analysis

| État Actuel | État Cible | Action Requise |
|-------------|------------|----------------|
| Pas de prix spot rubber | Prix TradingEconomics quotidien | Créer TradingEconomicsCollector |
| Prompts génériques | Prompts Cambodia-specific | Modifier PerplexityService |
| Pas de validation prix | Validation ranges rubber | Ajouter _validate_rubber_prices() |
| Scénarios globaux | Scénarios impact Cambodia | Refonte templates scénarios |
| Sources non affichées | Sources claires (TradingEcon, WITS) | Modifier Market Trends UI |
| FAO/CAC rubber non utilisés | Données rubber collectées | Configurer collectors rubber |

---

## 🏗️ Architecture Proposée

```
┌────────────────────────────────────────────────────────────────┐
│          RUBBER CAMBODIA - NOUVELLE ARCHITECTURE               │
└────────────────────────────────────────────────────────────────┘

[1] DATA SOURCES (100% Gratuit)
    │
    ├─► TradingEconomics (NOUVEAU !)
    │   └─► Scraping quotidien prix spot rubber
    │   └─► API free tier backup (500 req/mois)
    │
    ├─► FAO GIEWS/FPMA (Étendu ✅)
    │   └─► Prix farmgate Thailand (proxy Cambodia -12%)
    │
    ├─► WITS / Comtrade (Étendu ✅)
    │   └─► Exports Cambodia HS 4001 (natural rubber)
    │
    └─► CAC Rubber (Configuré ✅)
        └─► Rapports PDF rubber Cambodia
    │
    ↓
[2] COLLECTORS (app/collectors/)
    │
    ├─► tradingeconomics_collector.py (NOUVEAU)
    │   └─► fetch_rubber_price()
    │   └─► fetch_history_30d()
    │
    ├─► fao_giews_collector.py (Existe ✅)
    │   └─► fetch_thailand_rubber_farmgate()
    │   └─► estimate_cambodia_farmgate()
    │
    ├─► wits_collector.py (À étendre)
    │   └─► fetch_cambodia_rubber_exports() (HS 4001)
    │
    └─► cac_collector.py (À configurer)
        └─► CACCollector(commodity="rubber")
    │
    ↓
[3] SCHEDULER (app/scheduler/jobs.py)
    │
    ├─► daily_rubber_price_collection() (NOUVEAU)
    │   └─► TradingEconomics scraping
    │   └─► Stockage Supabase prices table
    │   └─► Exécution: 08:00 UTC quotidien
    │
    └─► monthly_free_sources_collection() (Modifier)
        └─► Ajouter CACCollector rubber
        └─► Exécution: 1er du mois 03:00 UTC
    │
    ↓
[4] VALIDATION (app/services/)
    │
    ├─► market_trends_service.py (NOUVEAU)
    │   └─► _validate_rubber_prices()
    │       ├─► Global spot: 170-190 cents/kg
    │       ├─► FOB Cambodia: 1,750-1,900 USD/ton
    │       └─► Farmgate: 4,500-6,000 KHR/kg
    │
    └─► perplexity_service.py (Améliorer)
        └─► research_rubber_cambodia()
            └─► Prompt Cambodia-specific
    │
    ↓
[5] SCENARIOS (app/api/routes/trends.py)
    │
    └─► POST /api/v1/trends/scenario
        ├─► Optimistic: Export revenue +$50M
        ├─► Realistic: Stable, dependency China
        └─► Pessimistic: Revenue -$44M, farmer crisis
    │
    ↓
[6] FRONTEND (ui/pages/)
    │
    ├─► 5_Market_Trends.py (Améliorer)
    │   ├─► Afficher prix TradingEconomics + source
    │   ├─► Farmgate estimate + disclaimer
    │   └─► Sentiment: "Non calculé" si 0 tweets
    │
    └─► 6_Scenario_Analysis.py (Améliorer)
        └─► Scénarios avec impact Cambodia
            ├─► Export revenue
            ├─► Farmgate KHR/kg
            └─► ~80,000 familles affectées
```

---

## 📝 Checklist Technique (Step-by-Step)

### ═══════════════════════════════════════════════════════════
### PHASE 1: DATA COLLECTION (3-4 jours)
### DÉLÉGATION: Agent Backend/Data
### ═══════════════════════════════════════════════════════════

#### 1.1 Créer TradingEconomicsCollector

**Agent:** `backend-developer`
**Fichier:** `app/collectors/tradingeconomics_collector.py` (NOUVEAU)

- [ ] **1.1.1** - Créer classe `TradingEconomicsCollector(BaseCollector)`
  - Hérite de: `app/collectors/base_collector.py`
  - Source name: `"TradingEconomics"`
  - Timeout: 30.0 secondes

- [ ] **1.1.2** - Implémenter `fetch_rubber_price()`
  - URL: `https://tradingeconomics.com/commodity/rubber`
  - Scraping avec BeautifulSoup
  - Extraction:
    ```python
    {
        "price_cents_per_kg": 182.5,
        "price_usd_per_ton": 1825,  # price_cents * 10
        "change_percent_day": -1.2,
        "date": "2026-01-01",
        "source": "TradingEconomics"
    }
    ```
  - Validation: Prix entre 150-220 cents/kg

- [ ] **1.1.3** - Implémenter `fetch_history_30d()`
  - Scraper tableau historique 30 jours
  - Format:
    ```python
    [{
        "date": "2025-12-02",
        "price_cents_kg": 185.0,
        "price_usd_ton": 1850
    }, ...]
    ```

- [ ] **1.1.4** - Ajouter fallback API free tier
  - URL API: `https://api.tradingeconomics.com/`
  - Free tier: 500 requests/mois
  - Headers: `{"Authorization": f"Bearer {api_key}"}`
  - Fallback si scraping échoue

- [ ] **1.1.5** - Tests unitaires
  - Test scraping HTML mock
  - Test conversion cents/kg → USD/ton
  - Test validation ranges prix

**Code pattern:**
```python
class TradingEconomicsCollector(BaseCollector):
    BASE_URL = "https://tradingeconomics.com/commodity"

    async def fetch_rubber_price(self) -> Dict:
        url = f"{self.BASE_URL}/rubber"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract price
            price_elem = soup.select_one('.price-value')
            price_cents = float(price_elem.text.strip())

            return {
                "price_cents_per_kg": price_cents,
                "price_usd_per_ton": price_cents * 10,
                "date": datetime.now().isoformat(),
                "source": "TradingEconomics"
            }
```

---

#### 1.2 Étendre WITSCollector pour Rubber

**Agent:** `backend-developer`
**Fichier:** `app/collectors/wits_collector.py` (Modifier)

- [ ] **1.2.1** - Ajouter méthode `fetch_cambodia_rubber_exports(year: int = 2024)`
  - Product code: HS `4001` (Natural rubber, latex)
  - Reporter: `KHM` (Cambodia)
  - Partners: `CHN`, `VNM`, `SGP`

- [ ] **1.2.2** - Extraire données export
  - Total export tons
  - Total export value USD
  - Avg unit price: `value / tons`
  - Top partners breakdown

- [ ] **1.2.3** - Valider données
  - Expected volumes: 100,000-150,000 tons/year
  - Expected avg price: 1,500-2,000 USD/ton
  - Warning si hors ranges

**Code pattern:**
```python
async def fetch_cambodia_rubber_exports(self, year: int = 2024) -> Dict:
    url = f"{self.api_url}/country/KHM/year/{year}/product/4001"
    # Fetch WITS data
    # Parse partners, volumes, values
    return {
        "total_export_tons": 120000,
        "total_export_value_usd": 219000000,
        "avg_price_usd_ton": 1825,
        "top_partners": {...}
    }
```

---

#### 1.3 Configurer FAOGIEWSCollector pour Rubber

**Agent:** `data-engineer`
**Fichier:** `app/collectors/fao_giews_collector.py` (Déjà OK, config seulement)

- [ ] **1.3.1** - Vérifier settings FAO GIEWS rubber
  - `settings.fao_giews_commodity_keywords` inclut `["rubber", "caoutchouc"]`
  - Country filter: Thailand (pour proxy)

- [ ] **1.3.2** - Tester récupération données Thailand
  - Product: "Rubber (sheet)" ou "Natural rubber"
  - Prix farmgate Thailand (THB/kg)

- [ ] **1.3.3** - Créer fonction estimation Cambodia
  - Formula: `cambodia_price = thailand_price * 0.875` (-12.5%)
  - Conversion KHR: `price_usd_kg * 4050`

**Code pattern:**
```python
def estimate_cambodia_farmgate(thailand_price_usd_kg: float) -> Dict:
    discount = 0.125
    cambodia_usd_kg = thailand_price_usd_kg * (1 - discount)
    cambodia_khr_kg = cambodia_usd_kg * 4050

    return {
        "estimated_price_usd_kg": cambodia_usd_kg,
        "estimated_price_khr_kg": cambodia_khr_kg,
        "basis": "Thailand FAO FPMA -12.5%",
        "disclaimer": "Estimated from regional data"
    }
```

---

#### 1.4 Configurer CACCollector pour Rubber

**Agent:** `backend-developer`
**Fichier:** `app/scheduler/jobs.py` (Modifier)

- [ ] **1.4.1** - Ajouter CACCollector rubber dans `monthly_free_sources_collection()`
  - Ligne ~192: Ajouter `CACCollector(commodity="rubber")`
  - Modifier liste collectors

- [ ] **1.4.2** - Tester collecte rapports CAC rubber
  - URL: https://cac-camcashew.org/ (chercher rubber reports si dispos)
  - Parser PDFs rubber

**Code pattern:**
```python
collectors = [
    FAOGIEWSCollector(),
    CACCollector(commodity="cashew"),
    CACCollector(commodity="rubber"),  # NOUVEAU
    wits_collector
]
```

---

#### 1.5 Ajouter Job Scheduler Quotidien TradingEconomics

**Agent:** `backend-developer`
**Fichier:** `app/scheduler/jobs.py` (Modifier)

- [ ] **1.5.1** - Créer fonction `daily_rubber_price_collection()`
  - Appeler `TradingEconomicsCollector().fetch_rubber_price()`
  - Stocker dans Supabase `prices` table
  - Logs: `[SCHEDULER] Rubber price collected: ${price} USD/ton`

- [ ] **1.5.2** - Ajouter job scheduler
  - CronTrigger: `hour=8, minute=0` (08:00 UTC quotidien)
  - ID: `"daily_rubber_price_tradingeconomics"`
  - Max instances: 1

- [ ] **1.5.3** - Tests scheduler
  - Déclencher manuellement job
  - Vérifier données stockées Supabase
  - Check logs Railway

**Code pattern:**
```python
async def daily_rubber_price_collection():
    print("[SCHEDULER] Collecting rubber price from TradingEconomics...", flush=True)

    collector = TradingEconomicsCollector()
    price_data = await collector.fetch_rubber_price()

    # Store in Supabase
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    await supabase.upsert_price({
        "commodity": "rubber",
        "date": price_data["date"],
        "price_usd_per_unit": price_data["price_usd_per_ton"],
        "source": "TradingEconomics",
        ...
    })

# Add to scheduler
scheduler.add_job(
    daily_rubber_price_collection,
    trigger=CronTrigger(hour=8, minute=0),
    id="daily_rubber_price",
    name="Daily Rubber Price (TradingEconomics)",
    replace_existing=True
)
```

---

### ═══════════════════════════════════════════════════════════
### PHASE 2: SERVICES & VALIDATION (3-4 jours)
### DÉLÉGATION: Agent Backend
### ═══════════════════════════════════════════════════════════

#### 2.1 Refonte Prompts Perplexity Rubber

**Agent:** `prompt-engineer` ou `backend-developer`
**Fichier:** `app/services/perplexity_service.py` (Modifier)

- [ ] **2.1.1** - Créer méthode `research_rubber_cambodia()`
  - Nouveau prompt Cambodia-specific
  - Mentions obligatoires:
    - Cambodia = 2nd producer (~120k tons)
    - 95% exports (60% China, 20% Vietnam)
    - Price-taker position
    - Farmgate estimate

- [ ] **2.1.2** - Template prompt complet
  - Voir brief section "Nouveau prompt rubber"
  - Recherches ciblées: TradingEconomics, WITS, FAO
  - Format output: Prix + source + Cambodia context

- [ ] **2.1.3** - Tests prompts
  - Appeler Perplexity API avec nouveau prompt
  - Vérifier mentions Cambodia présentes
  - Valider citations sources

**Code pattern:**
```python
async def research_rubber_cambodia(self, commodity: str = "rubber") -> Dict:
    prompt = f"""Analyze rubber market for Cambodia:

🔍 CAMBODIA CONTEXT (MANDATORY):
- Production: ~120,000 tons/year natural rubber
- Exports: ~115,000 tons (95%), China 60%, Vietnam 20%
- Price-taker (follows global TSR20)

DATA POINTS:
A) Global price TSR20: Search TradingEconomics rubber
   Expected: 170-190 cents/kg (1,700-1,900 USD/ton)

B) Cambodia exports: Search WITS HS 4001
   Expected: ~120k tons/year, $219M USD

C) Farmgate Cambodia: Estimate from Thailand FAO -12%
   Expected: 4,500-6,000 KHR/kg

D) China demand: Main buyer (60% exports)
   Search: China rubber imports trend

Focus last 30 days. Include citations.
"""

    return await self._query(prompt, commodity, query_type="rubber_market")
```

---

#### 2.2 Ajouter Validation Prix Rubber

**Agent:** `backend-developer`
**Fichier:** `app/services/market_trends_service.py` (Modifier)

- [ ] **2.2.1** - Créer fonction `_validate_rubber_prices(analysis: Dict) -> Dict`
  - Ranges attendus:
    - Global spot: 170-190 cents/kg
    - FOB Cambodia: 1,750-1,900 USD/ton
    - Farmgate: 4,500-6,000 KHR/kg

- [ ] **2.2.2** - Générer warnings si hors ranges
  - Warning si prix > 2,500 USD/ton
  - Warning si farmgate < 3,000 KHR/kg
  - Logger warnings

- [ ] **2.2.3** - Ajouter clarification footer
  - Texte explicatif prix rubber
  - Ranges typiques
  - Market structure Cambodia

- [ ] **2.2.4** - Intégrer dans `analyze_and_store_trends()`
  - Appeler `_validate_rubber_prices()` après Perplexity
  - Stocker warnings dans analysis result

**Code pattern:**
```python
def _validate_rubber_prices(self, analysis: Dict) -> Dict:
    warnings = []

    # Extract prices from analysis (regex or LLM parsing)
    spot_price = extract_spot_price(analysis["response_text"])

    if spot_price > 2500:
        warnings.append(f"⚠️ Rubber ${spot_price}/t high (expected 1,700-1,900)")

    clarification = """
📌 RUBBER PRICE REFERENCE (Cambodia)
- Global spot: 170-190 cents/kg (1,700-1,900 USD/ton)
- FOB Cambodia: ~1,800 USD/ton
- Farmgate: 4,500-6,000 KHR/kg (estimated)
"""

    analysis["price_warnings"] = warnings
    analysis["price_clarification"] = clarification
    return analysis
```

---

#### 2.3 Créer Scénarios Rubber Cambodia

**Agent:** `backend-developer` + `content-marketer`
**Fichier:** `app/api/routes/trends.py` (Modifier endpoint `/scenario`)

- [ ] **2.3.1** - Template scénario Optimistic
  - Prix: 1,950-2,100 USD/ton
  - Export revenue: +$38-57M USD
  - Farmgate: +20-30% (6,000-6,500 KHR/kg)
  - Driver: China demand +15%

- [ ] **2.3.2** - Template scénario Realistic
  - Prix: 1,750-1,900 USD/ton
  - Export revenue: Stable $209-219M
  - Farmgate: 5,100-5,500 KHR/kg
  - Driver: Moderate growth +3-5%

- [ ] **2.3.3** - Template scénario Pessimistic
  - Prix: 1,400-1,600 USD/ton
  - Export revenue: -$44-66M USD (-20-30%)
  - Farmgate: 3,500-4,500 KHR/kg (-25-35%)
  - Driver: China recession, EV shift

- [ ] **2.3.4** - Ajouter bloc "Cambodia Impact"
  - Export value calculation
  - Farmgate KHR impact
  - ~80,000 farming families
  - FX effect (USD/KHR)

**Code pattern:**
```python
realistic_rubber_template = f"""
## Realistic Scenario (3-6 months) - Rubber Cambodia

**Global Price:** 1,750-1,900 USD/ton (175-190 cents/kg)

**Cambodia Export Revenue:**
- Volume: 115,000 tons
- Price: 1,825 USD/ton (avg)
- Total: $209.9 million
- Change: -4.2% vs 2024

**Farmgate Prices:**
- 5,100-5,500 KHR/kg
- Impact: Slight pressure (-5-10%)

**FX Effect (USD/KHR = 4,050):**
- If weakens to 4,150: +2.5% KHR terms
- If strengthens to 3,950: -2.5% KHR terms

**Farmers Impact:**
- ~80,000 families affected
- Provinces: Kampong Cham (35%), Kratié (25%)
- Dependency: HIGH (rubber = main cash crop)

**Drivers:**
1. China auto +3% (tire demand)
2. No supply shocks
3. Synthetic rubber competition

**Risks:**
- China slowdown
- EV adoption (tire demand shift)
- Currency volatility
"""
```

---

### ═══════════════════════════════════════════════════════════
### PHASE 3: FRONTEND UI (2-3 jours)
### DÉLÉGATION: Agent Frontend
### ═══════════════════════════════════════════════════════════

#### 3.1 Market Trends UI - Rubber Section

**Agent:** `frontend-developer`
**Fichier:** `ui/pages/5_Market_Trends.py` (Modifier)

- [ ] **3.1.1** - Afficher prix TradingEconomics avec source
  - Format: "182.5 cents/kg (1,825 USD/ton)"
  - Source: "TradingEconomics, updated 2026-01-01"
  - Change 24h: "-1.2% ▼"

- [ ] **3.1.2** - Ajouter section Farmgate Estimate
  - Prix: "5,100-5,500 KHR/kg"
  - Conversion USD: "~1.26-1.36 USD/kg"
  - Disclaimer: "⚠️ Estimated from Thailand FAO data (-12%)"

- [ ] **3.1.3** - Fix sentiment si tweet_count = 0
  - Condition: `if tweet_count == 0:`
  - Affichage: "Sentiment: Non calculé (aucun tweet) ❓"
  - Confidence: 0
  - Pas de smiley neutre artificiel

- [ ] **3.1.4** - Ajouter contexte Cambodia
  - Production: ~120,000 tons
  - Exports: 95% (China 60%, Vietnam 20%)
  - Position: Price-taker, no processing

**Code pattern:**
```python
# Market Trends rubber section
st.subheader("Rubber Market Trends (Cambodia)")

# Prix spot
st.metric(
    "Global Spot Price (TradingEconomics)",
    f"1,825 USD/ton",
    delta="-1.2%",
    help="Source: TradingEconomics, updated 2026-01-01"
)

# Farmgate estimate
st.info("""
**Farmgate Estimate (Cambodia):**
- 5,100-5,500 KHR/kg (~1.26-1.36 USD/kg)
- ⚠️ Estimated from Thailand FAO data (-12% discount)
""")

# Sentiment (fix if 0 tweets)
if tweet_count == 0:
    st.warning("Sentiment: Non calculé (aucun tweet trouvé)")
else:
    st.success(f"Sentiment: {sentiment_label}")
```

---

#### 3.2 Scenario Analysis UI - Rubber

**Agent:** `frontend-developer`
**Fichier:** `ui/pages/6_Scenario_Analysis.py` (Modifier)

- [ ] **3.2.1** - Afficher scénarios Cambodia-specific
  - Section "Cambodia Impact" visible
  - Export revenue calculation
  - Farmgate KHR impact
  - Farmers affected count

- [ ] **3.2.2** - Visualisation exports destinations
  - Chart pie: China 60%, Vietnam 20%, Others 20%
  - Source: WITS data

- [ ] **3.2.3** - FX sensitivity display
  - Table USD/KHR scenarios
  - Impact % sur farmgate KHR

**Code pattern:**
```python
# Scenario optimistic
st.markdown(f"""
### Optimistic Scenario

**Global Price:** 1,950-2,100 USD/ton

**Cambodia Impact:**
- Export revenue: **+$38-57M** (+17-26%)
- Farmgate: **6,000-6,500 KHR/kg** (+20-30%)
- **80,000 families** benefit from higher prices

**Drivers:**
1. China auto demand +15%
2. Supply constraints
3. Strong tire demand
""")

# Export destinations chart
fig = px.pie(
    values=[72000, 24000, 19000],
    names=["China", "Vietnam", "Others"],
    title="Cambodia Rubber Exports by Destination"
)
st.plotly_chart(fig)
```

---

### ═══════════════════════════════════════════════════════════
### PHASE 4: TESTS & VALIDATION (2 jours)
### DÉLÉGATION: Vous-même ou Agent Testing
### ═══════════════════════════════════════════════════════════

#### 4.1 Tests Collectors

- [ ] **4.1.1** - Test TradingEconomicsCollector
  - Scraping HTML réussi
  - Prix extrait correct (170-190 cents/kg range)
  - Conversion USD/ton OK

- [ ] **4.1.2** - Test WITS rubber Cambodia
  - HS 4001 data retrieved
  - Exports ~100-150k tons
  - Partners China/Vietnam présents

- [ ] **4.1.3** - Test FAO GIEWS farmgate
  - Thailand data retrieved
  - Cambodia estimate -12% OK
  - Conversion KHR correct

---

#### 4.2 Tests Services

- [ ] **4.2.1** - Test prompts Perplexity rubber
  - Cambodia context mentionné
  - Prix sources correctes
  - Citations présentes

- [ ] **4.2.2** - Test validation prix
  - Warnings si prix > 2,500 USD/ton
  - Clarification footer affiché

- [ ] **4.2.3** - Test scénarios
  - 3 scénarios générés
  - Impact Cambodia présent
  - Calculations correctes

---

#### 4.3 Tests UI

- [ ] **4.3.1** - Market Trends rubber
  - Prix TradingEconomics affiché
  - Source visible
  - Farmgate estimate + disclaimer
  - Sentiment "Non calculé" si 0 tweets

- [ ] **4.3.2** - Scenario Analysis
  - Scénarios Cambodia-specific
  - Export revenue calculations
  - Charts destinations

---

#### 4.4 Tests E2E

- [ ] **4.4.1** - Workflow complet
  1. Trigger `daily_rubber_price_collection()`
  2. Vérifier Supabase `prices` table
  3. Trigger `/api/v1/trends/analyze/rubber`
  4. Vérifier `market_trends` table
  5. Ouvrir Market Trends UI
  6. Vérifier données affichées

- [ ] **4.4.2** - Tests scheduler
  - Job quotidien 08:00 UTC exécuté
  - Job mensuel 1er du mois exécuté
  - Logs Railway OK

---

## 🔧 Commandes à Exécuter

```bash
# Phase 1: Tests collectors
pytest tests/collectors/test_tradingeconomics_collector.py
pytest tests/collectors/test_wits_collector.py

# Phase 2: Tests services
pytest tests/services/test_perplexity_service.py
pytest tests/services/test_market_trends_service.py

# Phase 3: Lancer UI local
cd ui
streamlit run streamlit_app.py

# Phase 4: Trigger manuel jobs
python -c "
from app.scheduler.jobs import daily_rubber_price_collection
import asyncio
asyncio.run(daily_rubber_price_collection())
"

# Build et deploy
git add .
git commit -m "feat: rubber Cambodia analysis with TradingEconomics"
git push  # Auto-deploy Railway
```

---

## ⚠️ Risques Identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| TradingEconomics HTML change | 🔴 High | Fallback API free tier, tests réguliers |
| FAO FPMA pas de données rubber Thailand | 🟡 Medium | Utiliser Indonesia/Malaysia proxy |
| WITS Cambodia rubber data manquante | 🟡 Medium | Utiliser articles presse Cambodia |
| Scraping bloqué (rate limit) | 🟡 Medium | Retry logic, cache 24h, user-agent rotation |
| 0 tweets rubber fréquent | 🟢 Low | Afficher "Non calculé" (déjà prévu) |

---

## 🔍 Points de Validation

- [ ] Code compile sans erreur Python
- [ ] Tests unitaires passent (coverage >80%)
- [ ] Prix TradingEconomics affiché Market Trends
- [ ] Farmgate estimate visible avec disclaimer
- [ ] Scénarios Cambodia impact présent
- [ ] Sources affichées (TradingEcon, WITS, FAO)
- [ ] Sentiment "Non calculé" si 0 tweets
- [ ] Validation prix warnings fonctionnent
- [ ] Jobs scheduler exécutés quotidien/mensuel
- [ ] Railway logs clean (pas d'erreurs)

---

## 📚 Références (Context7)

- **httpx:** Async HTTP client pour scraping
- **BeautifulSoup:** HTML parsing TradingEconomics
- **APScheduler:** Jobs quotidiens/mensuels
- **Streamlit:** UI Market Trends/Scenarios

---

## 📊 Estimation

- **Complexité:** Moyenne
- **Fichiers modifiés:** 6 fichiers
- **Fichiers créés:** 1 collector nouveau
- **Dépendances:** 0 nouvelles (tout existe)
- **Durée:** 10-12 jours
- **Budget:** 0€ (sources gratuites)

---

## 🚦 Prêt pour Implémentation

- [x] Analyse complète (01_analysis.md ✓)
- [ ] Plan validé par l'utilisateur ← **ATTENTE VALIDATION**
- [x] Toutes les dépendances identifiées
- [x] Stratégie claire et sans ambiguïté
- [x] Délégation agents définie

---

## 🎯 DÉLÉGATION AGENTS

### Phase 1: Agent `backend-developer` ou `data-engineer`
**Tâches:** 1.1 à 1.5 (Collectors + Scheduler)
**Durée:** 3-4 jours

### Phase 2: Agent `backend-developer` + `prompt-engineer`
**Tâches:** 2.1 à 2.3 (Services + Validation + Scénarios)
**Durée:** 3-4 jours

### Phase 3: Agent `frontend-developer`
**Tâches:** 3.1 à 3.2 (UI Market Trends + Scenarios)
**Durée:** 2-3 jours

### Phase 4: Vous-même ou `test-engineer`
**Tâches:** 4.1 à 4.4 (Tests E2E)
**Durée:** 2 jours

---

**Plan terminé. En attente de validation pour lancer /implement.**
