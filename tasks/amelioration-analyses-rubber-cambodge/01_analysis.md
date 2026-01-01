# Analyse: Amélioration Analyses Rubber Cambodge

## 📋 Contexte

**Date:** 2026-01-01
**Demande initiale:** Renforcer analyses rubber Cambodge (budget 0€, sources gratuites)
**Objectif:** Implémenter scraping TradingEconomics, améliorer contexte Cambodia, validation prix

---

## 🔍 État Actuel de la Codebase

### Fichiers Concernés

| Fichier | Type | Rôle | Status |
|---------|------|------|--------|
| `app/collectors/tradingeconomics_collector.py` | Collector | **À CRÉER** - Scraping prix rubber | ❌ Manquant |
| `app/collectors/fao_giews_collector.py` | Collector | Prix farmgate (proxy) | ✅ Existe (L81-82 support rubber) |
| `app/collectors/cac_collector.py` | Collector | Rapports CAC rubber | ✅ Existe (param commodity) |
| `app/collectors/wits_collector.py` | Collector | Exports Cambodia | ✅ Existe (à étendre HS 4001) |
| `app/services/perplexity_service.py` | Service | Prompts AI analysis | ✅ Existe (à améliorer) |
| `app/services/market_trends_service.py` | Service | Market trends logic | ✅ Existe (validation manquante) |
| `app/api/routes/trends.py` | API | Endpoints trends/scenario | ✅ Existe (scénarios à améliorer) |
| `app/scheduler/jobs.py` | Scheduler | Jobs quotidiens/mensuels | ✅ Existe (L158-202 monthly_free_sources) |
| `ui/pages/5_Market_Trends.py` | Frontend | UI Market Trends | ✅ Existe (affichage à améliorer) |
| `ui/pages/6_Scenario_Analysis.py` | Frontend | UI Scénarios | ✅ Existe (contexte Cambodia manquant) |

---

### Architecture Actuelle

```
┌─────────────────────────────────────────────────────────────┐
│                    RUBBER DATA FLOW                         │
└─────────────────────────────────────────────────────────────┘

[1] DATA COLLECTION (Collectors)
    │
    ├─► FAOGIEWSCollector ✅ (prix farmgate proxy Thailand)
    ├─► CACCollector ✅ (rapports PDF CAC rubber)
    ├─► WITSCollector ✅ (exports Cambodia HS 4001)
    └─► TradingEconomicsCollector ❌ (MANQUANT - prix spot global)
    │
    ↓
[2] SCHEDULER (jobs.py)
    │
    ├─► daily_market_analysis() ✅ L204-240
    │   └─► Analyse Twitter + Perplexity (quotidien 09:00)
    │
    └─► monthly_free_sources_collection() ✅ L158-202
        └─► FAO + CAC + WITS (mensuel, 1er du mois)
    │
    ↓
[3] STORAGE (Supabase)
    │
    ├─► market_trends table (analyses quotidiennes)
    ├─► prices table (prix historiques)
    └─► context_documents table (rapports CAC/FAO)
    │
    ↓
[4] SERVICES (Analysis)
    │
    ├─► PerplexityService ✅ (prompts à améliorer)
    │   └─► research_daily_prices() L26-45
    │   └─► research_comprehensive() L47-68
    │
    └─► MarketTrendsService ✅ (validation manquante)
        └─► analyze_and_store_trends()
        └─► get_latest_trend()
    │
    ↓
[5] API ENDPOINTS (FastAPI)
    │
    ├─► GET /api/v1/trends/latest/{commodity} ✅
    ├─► GET /api/v1/trends/history/{commodity} ✅
    ├─► POST /api/v1/trends/analyze/{commodity} ✅
    └─► POST /api/v1/trends/scenario ✅ (scénarios à améliorer)
    │
    ↓
[6] FRONTEND (Streamlit)
    │
    ├─► Market Trends (5_Market_Trends.py) ✅
    │   └─► Affichage prix, sentiment, alertes
    │   └─► Manque: Source prix, validation ranges
    │
    └─► Scenario Analysis (6_Scenario_Analysis.py) ✅
        └─► Scénarios optimiste/réaliste/pessimiste
        └─► Manque: Impact Cambodia spécifique
```

---

### Code Snippets Clés

#### 1. FAOGIEWSCollector (déjà supporte rubber)

**Fichier:** `app/collectors/fao_giews_collector.py` L77-85

```python
async def validate(self, data: Dict[str, Any]) -> bool:
    required_fields = ["commodity", "date", "price_usd", "source"]
    if not all(field in data for field in required_fields):
        return False
    if data["commodity"] not in ["cashew", "rubber"]:  # ✅ RUBBER supporté
        return False
    if not isinstance(data["price_usd"], (int, float)):
        return False
    return True
```

**Constat:** Déjà configuré pour rubber, juste besoin de données FPMA rubber.

---

#### 2. CACCollector (commodity parameter)

**Fichier:** `app/collectors/cac_collector.py` L22-35

```python
def __init__(
    self,
    base_url: Optional[str] = None,
    seed_paths: Optional[List[str]] = None,
    commodity: str = "cashew",  # ✅ Paramétrable
    max_pdfs: Optional[int] = None,
    ...
):
    super().__init__("CAC")
    self.commodity = commodity  # Peut être "rubber"
```

**Constat:** Réutilisable pour rubber en passant `commodity="rubber"`.

---

#### 3. Monthly Free Sources Collection

**Fichier:** `app/scheduler/jobs.py` L158-202

```python
async def monthly_free_sources_collection() -> None:
    """Collect free-source data (FAO GIEWS/FPMA, CAC, WITS) monthly."""
    collectors = [
        FAOGIEWSCollector(),
        CACCollector(),  # Par défaut cashew
        wits_collector
    ]

    data = await run_collectors(collectors)
    summary = await store_data_dual(data, supabase, chromadb)
```

**Constat:** Fonctionne déjà, mais CACCollector pas configuré pour rubber.

---

#### 4. Perplexity Prompts (à améliorer)

**Fichier:** `app/services/perplexity_service.py` L36-43

```python
prompt = f"""Analyze current market conditions for {commodity} in Cambodia:
1. Latest export prices (USD per ton)
2. Key destination countries (Vietnam, China, Europe)
3. Supply/demand dynamics
4. Geopolitical factors affecting trade
5. Quality grades impact on pricing

Focus on factual data from last 7 days. Include citations."""
```

**Problèmes identifiés:**
- ❌ Pas de distinction produit (latex vs sheet rubber)
- ❌ Pas de mention Cambodia = 2nd producteur
- ❌ Pas de focus exports 60% Chine
- ❌ Pas de prix farmgate Cambodia

---

## 📚 Documentation Externe (Context7)

### Librairie: httpx
**Library ID:** `/encode/httpx`
**Utilisation:** HTTP client pour scraping TradingEconomics
**Documentation clés:**
- Async client: `async with httpx.AsyncClient() as client:`
- Timeout handling: `timeout=30.0`
- Follow redirects: `follow_redirects=True`

### Librairie: BeautifulSoup4
**Library ID:** `/beautifulsoup4`
**Utilisation:** Parsing HTML TradingEconomics
**Documentation clés:**
- Parser: `BeautifulSoup(html, 'html.parser')`
- Selectors: `.select_one('.class-name')`
- Text extraction: `.text.strip()`

### Librairie: APScheduler
**Library ID:** `/apscheduler`
**Utilisation:** Jobs quotidiens/mensuels
**Documentation clés:**
- AsyncIOScheduler: Déjà utilisé ✅
- CronTrigger: `CronTrigger(day=1, hour=3, minute=0)`
- Job management: `scheduler.add_job()`

---

## 🔗 Dépendances

### Internes

```
app/collectors/tradingeconomics_collector.py (À CRÉER)
    ↓ utilise
app/config.py (settings.tradingeconomics_url)
    ↓ appelé par
app/scheduler/jobs.py (daily job)
    ↓ stocke dans
app/services/supabase_service.py (upsert_price)
```

```
app/services/perplexity_service.py
    ↓ appelé par
app/services/market_trends_service.py
    ↓ appelé par
app/api/routes/trends.py (/analyze endpoint)
    ↓ consommé par
ui/pages/5_Market_Trends.py
```

### Externes

| Package | Version | Utilisation | Status |
|---------|---------|-------------|--------|
| `httpx` | >=0.24.0 | HTTP client async | ✅ Installé |
| `beautifulsoup4` | >=4.12.0 | HTML parsing | ✅ Installé |
| `apscheduler` | >=3.10.4 | Job scheduling | ✅ Installé |
| `supabase` | >=2.0.0 | Database | ✅ Installé |
| `perplexity` | API | AI analysis | ✅ Configuré |

**Aucune nouvelle dépendance requise** ✅

---

## ⚠️ Points d'Attention

### 1. TradingEconomics Scraping
- **Risque:** Structure HTML peut changer
- **Mitigation:**
  - Fallback vers API free tier (500 req/mois)
  - Tests réguliers scraping
  - Logs détaillés si échec

### 2. Prix Farmgate Cambodia Estimation
- **Problème:** Pas de données directes Cambodia
- **Solution:** Proxy Thailand -10-15%
- **Disclaimer:** Afficher clairement "Estimated from regional data"

### 3. WITS Rubber Data
- **HS Code:** 4001 (Natural rubber, latex form)
- **Fréquence:** Données annuelles (pas quotidiennes)
- **Utilisation:** Contexte export, pas prix temps réel

### 4. Sentiment Twitter Rubber
- **Problème:** Peu de tweets rubber vs cashew
- **Solution:** Si tweet_count = 0 → "Non calculé" (pas "50% neutre")

### 5. Validation Prix Ranges
- **Ranges attendus:**
  - Global spot: 170-190 cents/kg (1,700-1,900 USD/ton)
  - FOB Cambodia: 1,750-1,900 USD/ton
  - Farmgate Cambodia: 4,500-6,000 KHR/kg
- **Action:** Warnings si hors ranges

---

## 💡 Opportunités Identifiées

### 1. Réutilisation Collectors Existants
- ✅ `FAOGIEWSCollector` déjà prêt rubber
- ✅ `CACCollector` paramétrable
- ✅ `WITSCollector` extensible HS 4001

**Gain:** 40% du travail déjà fait !

### 2. Job Scheduler Mensuel Actif
- ✅ `monthly_free_sources_collection()` L158-202
- **Action:** Ajouter TradingEconomics daily job

### 3. Pattern Validation Prix
- Existe pour autres commodities (public_prices_service)
- **Réutilisable:** Créer `_validate_rubber_prices()`

### 4. Frontend Market Trends Modulaire
- UI déjà structure rubber/cashew
- **Extension facile:** Ajouter sections prix source, farmgate

---

## 📊 Résumé Exécutif

### État Actuel: 60% Prêt ✅

**Existant (✅):**
- Collectors: FAO GIEWS, CAC, WITS
- Scheduler: Jobs quotidiens/mensuels
- Services: Perplexity, MarketTrends
- API: Endpoints trends/scenario
- Frontend: Market Trends UI

**Manquant (❌):**
- TradingEconomics Collector (prix spot global)
- Validation prix rubber
- Prompts Perplexity Cambodia-specific
- Scénarios rubber Cambodia impact
- Affichage sources prix UI

### Effort Estimé: 10-12 jours

**Phase 1 (3j):** TradingEconomics Collector + daily job
**Phase 2 (4j):** Services (prompts, validation, scénarios)
**Phase 3 (3j):** Frontend UI updates
**Phase 4 (2j):** Tests E2E

### Budget: 0€ ✅

Toutes sources gratuites (TradingEconomics scraping, FAO, WITS, CAC).

---

## 🚀 Prêt pour Planification

Cette analyse est **complète** et prête pour `/plan`.

**Fichiers identifiés:**
- 10 fichiers existants à modifier
- 1 nouveau collector à créer
- 0 nouvelles dépendances

**Architecture:** Claire, modulaire, extensible.

**Next step:** Créer `02_plan.md` avec checklist détaillée step-by-step.
