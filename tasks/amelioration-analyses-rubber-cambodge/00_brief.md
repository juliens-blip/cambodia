# Brief APEX - Amélioration Analyses Rubber Cambodge

**Date:** 2026-01-01
**Feature:** Analyse caoutchouc cambodgien (budget 0€)
**Délégation:** Agents spécialisés disponibles

---

## 🎯 OBJECTIF

Renforcer l'**analyse du caoutchouc au Cambodge** sans payer d'API, en combinant :
1. **Sources gratuites** : FAO, WITS, MEF/NBC/CSX, articles, rapports
2. **Scraping TradingEconomics** : Prix spot caoutchouc (free tier)
3. **Focus Cambodge** : Impact local, contexte macro, exports

---

## 📊 DONNÉES À UTILISER (100% Gratuites)

### 1.1 **Prix Mondiaux du Caoutchouc**

**Source principale:** TradingEconomics (scraping/free tier)

**URL:** https://tradingeconomics.com/commodity/rubber

**Données à extraire:**
- Prix spot (cents/kg)
- Variation % jour
- Historique 30 derniers jours
- Conversion : **1 cent/kg = 10 USD/ton**

**Tâche IA:**
```python
# Scraper TradingEconomics une fois/jour
# Extraire:
{
    "price_cents_per_kg": 182.5,
    "change_percent_day": -1.2,
    "date": "2026-01-01",
    "history_30d": [
        {"date": "2025-12-02", "price": 185.0},
        {"date": "2025-12-03", "price": 183.5},
        ...
    ]
}

# Convertir en USD/ton pour dashboard
price_usd_per_ton = price_cents_per_kg * 10
# Exemple: 182.5 cents/kg = 1,825 USD/ton
```

**Alternative API (free tier):**
- TradingEconomics Free Tier: 500 requests/mois
- Endpoint: `/markets/commodity/{symbol}`
- Symbol: `RUBBER`

---

### 1.2 **Contexte Macro Cambodge**

**Sources gratuites (déjà intégrées ✅):**
- MEF: Taux USD/KHR
- NBC: Exchange rate trends
- CSX: Index boursier

**Tâches:**
- ✅ Continuer récupération MEF/NBC/CSX
- 🆕 **Relier explicitement à rubber :**
  - Conversion revenus export en KHR
  - Impact taux change sur rentabilité producteurs
  - Conditions financières locales (crédit agricole)

**Exemple d'intégration:**
```python
# Dans scénarios rubber
usd_khr_rate = 4050
rubber_price_usd_ton = 1825

farmgate_khr_kg = (rubber_price_usd_ton / 1000) * usd_khr_rate * 0.7  # 70% du FOB
# farmgate_khr_kg ≈ 5,164 KHR/kg

if usd_khr_trend == "weakening":  # KHR perd valeur
    impact = "Favorable: Farmers earn more KHR per kg (export competitive)"
elif usd_khr_trend == "strengthening":
    impact = "Défavorable: Farmers earn less KHR per kg (export pressure)"
```

---

### 1.3 **Commerce International et Rôle du Cambodge**

**Sources à intégrer (gratuites):**

#### A) **WITS / UN Comtrade**
- **URL:** https://wits.worldbank.org/
- **HS Codes:**
  - `4001`: Natural rubber (latex form)
  - `4002`: Synthetic rubber
  - `4003`: Reclaimed rubber
  - `4004`: Waste/scrap rubber

**Données à extraire:**
```python
# Cambodia exports (reporter: KHM)
{
    "year": 2024,
    "product_code": "4001",
    "export_tons": 120000,
    "export_value_usd": 219_000_000,
    "avg_unit_price_usd_ton": 1825,
    "partners": {
        "China": {"tons": 72000, "share": 0.60},
        "Vietnam": {"tons": 24000, "share": 0.20},
        "Singapore": {"tons": 12000, "share": 0.10},
        "Others": {"tons": 12000, "share": 0.10}
    }
}
```

**Tâches:**
1. **Script ETL WITS:**
   - Reporter: `KHM` (Cambodia)
   - Product: `4001` (Natural rubber)
   - Years: 2020-2024
   - Extract: volumes, values, partners

2. **Calcul prix unitaires:**
   ```python
   avg_price = export_value_usd / export_tons
   ```

#### B) **Articles de presse / rapports**

**Sources gratuites à scraper:**
- ProduceReport.com (rubber news)
- Vietnamnet.vn (Vietnam rubber imports)
- Rubber Asia (industry reports)
- Cambodia Ministry of Agriculture (rapports PDF)

**Exemple données à extraire:**
```
"Cambodia exported 120,000 tons of natural rubber in 2024,
 valued at $219 million, primarily to China (60%)..."
```

**Tâches:**
- WebSearch pour articles récents (last 30 days)
- Extraire volumes, destinations, prix mentionnés
- Valider vs WITS data

---

### 1.4 **Prix Domestiques / Farmgate (Proxy Gratuit)**

**Source:** FAO GIEWS / FPMA

**URL:** http://www.fao.org/giews/food-prices/

**Approche:**
1. Checker FPMA pour séries "rubber" pays producteurs Asie :
   - Thaïlande (leader mondial)
   - Vietnam
   - Laos
   - Indonesia

2. Si dispo pour pays voisins, créer **proxy Cambodia :**
   ```python
   # Thailand farmgate rubber: 55 THB/kg (from FPMA)
   # Convert to Cambodia estimate
   thb_usd_rate = 0.029
   farmgate_usd_kg = 55 * 0.029  # = 1.595 USD/kg

   # Cambodia likely 10-15% lower (less processed)
   cambodia_farmgate_estimate = farmgate_usd_kg * 0.85  # = 1.36 USD/kg

   # Convert to KHR
   cambodia_farmgate_khr = 1.36 * 4050  # = 5,508 KHR/kg
   ```

**Tâches:**
- Download FAO FPMA CSV pour Thaïlande/Vietnam rubber
- Calculer proxy Cambodia avec décote 10-15%
- Afficher avec disclaimer: "Estimated from regional data"

---

## 🔧 ÉQUIVALENTS GRATUITS AUX APIs PAYANTES

| API Payante | Équivalent Gratuit | Effort |
|-------------|-------------------|--------|
| **Vietnam/Cambodia Customs API** | WITS + Articles citant "Vietnam Customs" | 🛠️ Medium |
| **TradingEconomics Premium** | Scraping page ou Free Tier (500 req/mois) | 🛠️ Low |
| **Prix privés (ICE, SGX)** | TradingEconomics + Articles broker | 🛠️ Medium |
| **Farmgate prices Cambodia** | FAO FPMA proxy (Thaïlande -10%) | 🛠️ Low |

---

## 📝 LOGIQUE D'ANALYSE À IMPLÉMENTER

### 3.1 **Market Trends - Rubber**

**Affichage requis:**

```markdown
## Rubber Market Trends (Cambodia)

**Global Price (TradingEconomics):**
- Spot: 182.5 cents/kg (1,825 USD/ton)
- Change 24h: -1.2% ▼
- Range 30d: 179-185 cents/kg
- Source: TradingEconomics, updated 2026-01-01

**Cambodia Context:**
- Production: ~120,000 tons/year (2024)
- Exports: ~115,000 tons (95% of production)
- Main destinations:
  * China: 60% (72,000 tons)
  * Vietnam: 20% (24,000 tons)
  * Singapore: 10% (12,000 tons)
- Export value: $219 million USD (2024)

**Farmgate Estimate (Cambodia):**
- 5,100-5,500 KHR/kg (based on regional proxy)
- ~1.26-1.36 USD/kg
- Note: Estimated from Thailand/Vietnam data (-10-15%)

**Macro Indicators:**
- USD/KHR: 4,050 (stable)
- CSX Index: 1,234 (+2.5%)
- Impact: Neutral for rubber exports
```

**Règles de robustesse:**

```python
# 1. Sentiment Twitter si 0 tweets
if tweet_count == 0:
    sentiment = {
        "label": "Non calculé (aucun tweet)",
        "confidence": 0,
        "icon": "❓"
    }
else:
    # Calculate normally
    pass

# 2. Pas de "50% neutre" artificiel
# Ne PAS inventer de sentiment si données manquantes

# 3. Toujours afficher la source du prix
price_display = f"""
**Spot Price:** {price} USD/ton
**Source:** TradingEconomics
**Updated:** {timestamp}
"""
```

---

### 3.2 **Scénarios (Pessimiste / Réaliste / Optimiste)**

**Template avec Impact Cambodge:**

```python
scenario_template = f"""
## {{scenario_type}} Scenario (3-6 months) - Rubber Cambodia

**Global Price Forecast:**
- Range: {{price_low}}-{{price_high}} USD/ton
- Driver: {{main_driver}}

**Cambodia Impact:**

**Export Revenue:**
- Volume: 115,000 tons (assumption: stable production)
- Price: {{avg_price}} USD/ton
- Total value: ${{export_value}} million
- Change vs current: {{change_percent}}%

**Farmgate Prices:**
- Estimated: {{farmgate_khr_low}}-{{farmgate_khr_high}} KHR/kg
- Impact on farmers: {{farmer_impact}}

**FX Effect (USD/KHR):**
- If KHR weakens to {{usd_khr_weak}}: Farmers gain +{{gain_pct}}% in local currency
- If KHR strengthens to {{usd_khr_strong}}: Farmers lose -{{loss_pct}}% in local currency

**Sector Impact:**
- ~{{farmer_count}} farming families affected
- Main provinces: Kampong Cham, Kratié, Mondulkiri
- Livelihood dependency: {{dependency_level}}

**Drivers:**
1. {{driver_1}}
2. {{driver_2}}
3. {{driver_3}}

**Risks:**
- {{risk_1}}
- {{risk_2}}
"""
```

**Exemple Scenario Réaliste:**

```markdown
## Realistic Scenario (3-6 months) - Rubber Cambodia

**Global Price Forecast:**
- Range: 1,750-1,900 USD/ton (175-190 cents/kg)
- Driver: Moderate demand growth (China auto +3%), stable supply

**Cambodia Impact:**

**Export Revenue:**
- Volume: 115,000 tons
- Price: 1,825 USD/ton (avg)
- Total value: $209.9 million
- Change vs 2024: -4.2% (vs $219M)

**Farmgate Prices:**
- Estimated: 4,900-5,300 KHR/kg
- Impact on farmers: Slight pressure (-5-10% vs peak)

**FX Effect (USD/KHR):**
- Current rate 4,050 stable
- If KHR weakens to 4,150: Farmers gain +2.5% in KHR terms
- If KHR strengthens to 3,950: Farmers lose -2.5% in KHR terms

**Sector Impact:**
- ~80,000 farming families affected
- Main provinces: Kampong Cham (35%), Kratié (25%), Mondulkiri (20%)
- Livelihood dependency: HIGH (rubber = primary cash crop)

**Drivers:**
1. China auto production +3% (steady tire demand)
2. No major supply shocks (Thailand/Vietnam stable)
3. Synthetic rubber competition (price parity)

**Risks:**
- China economic slowdown → Demand drop
- EV adoption acceleration → Tire demand shift
- Currency volatility (USD/KHR swings)

**Cambodia Position:**
- Price-taker (no processing capacity)
- 95% exports raw (no value addition)
- Dependency: 60% China exposure
```

---

## 🛠️ ARCHITECTURE TECHNIQUE

### **Phase 1 : Scraping + Validation (5-7 jours)**

#### 1.1 **TradingEconomics Scraper**

**Nouveau fichier:** `app/collectors/tradingeconomics_collector.py`

```python
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from datetime import datetime

class TradingEconomicsCollector:
    """
    Scraper for TradingEconomics commodity prices.

    Free tier: 500 requests/month or web scraping.
    """

    BASE_URL = "https://tradingeconomics.com/commodity"

    async def fetch_rubber_price(self) -> Dict:
        """
        Scrape rubber spot price from TradingEconomics.

        Returns:
            {
                "price_cents_per_kg": 182.5,
                "price_usd_per_ton": 1825,
                "change_percent_day": -1.2,
                "date": "2026-01-01",
                "source": "TradingEconomics"
            }
        """
        url = f"{self.BASE_URL}/rubber"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract price (example selector, adjust based on actual HTML)
            price_elem = soup.select_one('.price-value')
            price_cents = float(price_elem.text.strip())

            # Extract change %
            change_elem = soup.select_one('.price-change')
            change_pct = float(change_elem.text.replace('%', '').strip())

            return {
                "price_cents_per_kg": price_cents,
                "price_usd_per_ton": price_cents * 10,
                "change_percent_day": change_pct,
                "date": datetime.now().isoformat(),
                "source": "TradingEconomics"
            }

    async def fetch_history_30d(self) -> List[Dict]:
        """
        Scrape 30-day price history.

        Returns:
            [{
                "date": "2025-12-02",
                "price_cents_kg": 185.0,
                "price_usd_ton": 1850
            }, ...]
        """
        # Similar scraping for historical data
        pass
```

#### 1.2 **WITS Collector (déjà existe, à étendre)**

**Fichier:** `app/collectors/wits_collector.py`

**Ajouter rubber support:**

```python
class WITSCollector(BaseCollector):
    """Extended to support rubber (HS 4001)."""

    async def fetch_cambodia_rubber_exports(
        self,
        year: int = 2024
    ) -> Dict:
        """
        Fetch Cambodia rubber exports via WITS API.

        Product: HS 4001 (Natural rubber, latex form)
        Reporter: KHM (Cambodia)

        Returns:
            {
                "year": 2024,
                "product": "4001",
                "total_export_tons": 120000,
                "total_export_value_usd": 219000000,
                "avg_price_usd_ton": 1825,
                "top_partners": {
                    "CHN": {"tons": 72000, "value_usd": 131400000},
                    "VNM": {"tons": 24000, "value_usd": 43800000},
                    ...
                }
            }
        """
        url = f"{self.api_url}/country/KHM/year/{year}/product/4001"
        # Fetch and parse
        pass
```

#### 1.3 **FAO GIEWS Proxy Farmgate**

**Nouveau fichier:** `app/collectors/fao_giews_collector.py`

```python
class FAOGIEWSCollector:
    """
    Collector for FAO GIEWS farmgate prices (proxy).

    Strategy:
    1. Fetch Thailand rubber farmgate (FAO FPMA)
    2. Apply -10-15% discount for Cambodia estimate
    """

    async def fetch_thailand_rubber_farmgate(self) -> Dict:
        """
        Download Thailand rubber prices from FAO FPMA.

        Returns:
            {
                "country": "Thailand",
                "product": "Rubber (sheet)",
                "price_local": 55,  # THB/kg
                "price_usd_kg": 1.595,
                "date": "2024-12-01",
                "source": "FAO FPMA"
            }
        """
        # Download CSV from FPMA tool
        # Parse Thailand rubber row
        pass

    def estimate_cambodia_farmgate(
        self,
        thailand_price_usd_kg: float
    ) -> Dict:
        """
        Estimate Cambodia farmgate from Thailand data.

        Assumption: Cambodia -10-15% vs Thailand (less processing)
        """
        discount = 0.125  # Average -12.5%
        cambodia_usd_kg = thailand_price_usd_kg * (1 - discount)
        cambodia_khr_kg = cambodia_usd_kg * 4050  # USD/KHR rate

        return {
            "estimated_price_usd_kg": cambodia_usd_kg,
            "estimated_price_khr_kg": cambodia_khr_kg,
            "basis": "Thailand FAO FPMA -12.5%",
            "disclaimer": "Estimated from regional data"
        }
```

---

### **Phase 2 : Validation et Scénarios (3-5 jours)**

#### 2.1 **Validation Prix Rubber**

**Fichier:** `app/services/market_trends_service.py`

**Ajouter validation rubber:**

```python
def _validate_rubber_prices(self, analysis: Dict) -> Dict:
    """
    Validate rubber price ranges.

    Expected ranges (2024-2025):
    - Global spot: 170-190 cents/kg (1,700-1,900 USD/ton)
    - FOB Cambodia: Similar to global (minimal processing)
    - Farmgate Cambodia: 4,500-6,000 KHR/kg
    """

    warnings = []

    if spot_price_usd_ton > 2500:
        warnings.append(f"⚠️ Rubber price ${spot_price_usd_ton}/t seems high (expected 1,700-1,900)")

    if farmgate_khr_kg < 3000:
        warnings.append(f"⚠️ Farmgate {farmgate_khr_kg} KHR/kg seems low (expected 4,500-6,000)")

    clarification = """

📌 RUBBER PRICE REFERENCE (Cambodia)

**Product Type:**
- Natural rubber (latex/sheet form)
- Minimal processing in Cambodia (exported raw)

**Typical Ranges (2024-2025):**
- Global spot: 170-190 cents/kg (1,700-1,900 USD/ton)
- FOB Cambodia: ~1,800-1,900 USD/ton
- Farmgate Cambodia: 4,500-6,000 KHR/kg (estimated)

**Market Structure:**
- Cambodia production: ~120,000 tons/year
- 95% exports raw (China 60%, Vietnam 20%)
- Price-taker (follows global TSR20/RSS3 benchmarks)
    """

    analysis["price_validation_warnings"] = warnings
    analysis["price_clarification"] = clarification

    return analysis
```

#### 2.2 **Refonte Prompts Perplexity Rubber**

**Fichier:** `app/services/perplexity_service.py`

**Nouveau prompt rubber:**

```python
async def research_rubber_cambodia(self, commodity: str = "rubber") -> Dict:
    """
    Research rubber market with Cambodia focus.
    """

    prompt = f"""Analyze rubber market for Cambodia (natural rubber production):

🔍 CRITICAL: Cambodia-specific context required

**Cambodia Rubber Profile:**
- Production: ~120,000 tons/year natural rubber
- Exports: ~115,000 tons (95% of production)
- Main destinations: China (60%), Vietnam (20%), Singapore (10%)
- Processing: Minimal (exports raw latex/sheets, no value addition)

**Data Points to Find:**

A) Global rubber prices (TSR20/RSS3 benchmarks)
   - Search: "rubber price TSR20" site:tradingeconomics.com
   - Search: "natural rubber price Singapore" site:sgx.com
   - Typical range: 170-190 cents/kg (1,700-1,900 USD/ton)

B) Cambodia export data
   - Search: "Cambodia rubber exports 2024" site:wits.worldbank.org
   - Search: "Cambodia natural rubber China" (volumes, destinations)
   - Reference: WITS HS code 4001

C) Farmgate prices Cambodia
   - Search: "Cambodia rubber farmer price KHR"
   - Search: FAO GIEWS Thailand rubber farmgate (for proxy)
   - Estimate: Thailand price × 0.85-0.90

D) China demand (main buyer)
   - Search: "China rubber imports 2024"
   - Search: "China tire production forecast"
   - Auto industry trends (+3-5% = bullish for rubber)

E) Macro Cambodia
   - USD/KHR rate impact (current ~4,050)
   - Farmer income in local currency
   - CSX index (financial conditions)

**Output Format:**
- Global price: X cents/kg (Y USD/ton) - Source: Z
- Cambodia exports: XX,XXX tons @ $YYY/ton - Source: WITS
- Farmgate estimate: X,XXX KHR/kg (based on Thailand -12%) - Disclaimer
- China demand trend: +X% imports - Source: China Customs

**Cambodia Context (MANDATORY):**
For each scenario, discuss:
1. Export revenue impact (tons × price)
2. Farmgate price effect (KHR/kg for ~80,000 families)
3. FX sensitivity (USD/KHR movements)
4. Dependency risk (60% China exposure)

Focus on factual data from last 30 days. Include citations.
"""

    return await self._query(prompt, commodity, query_type="rubber_market")
```

---

## 📋 PLAN D'IMPLÉMENTATION - DÉLÉGATION AGENTS

### **PHASE 1 : Backend Data Collection (Agent Backend/Data)**

**Responsable:** Agent `backend-developer` ou `data-engineer`

**Tâches:**
- [ ] 1.1 - Implémenter `TradingEconomicsCollector` (scraping rubber)
- [ ] 1.2 - Étendre `WITSCollector` pour rubber (HS 4001)
- [ ] 1.3 - Créer `FAOGIEWSCollector` (proxy farmgate Thailand)
- [ ] 1.4 - Ajouter job scheduler mensuel rubber data collection
- [ ] 1.5 - Tests ETL: TradingEconomics → Supabase

**Fichiers créés:**
- `app/collectors/tradingeconomics_collector.py`
- `app/collectors/fao_giews_collector.py` (if not exists)

**Fichiers modifiés:**
- `app/collectors/wits_collector.py` (add rubber support)
- `app/scheduler/jobs.py` (add monthly rubber collection)

---

### **PHASE 2 : Services & Validation (Agent Backend)**

**Responsable:** Agent `backend-developer`

**Tâches:**
- [ ] 2.1 - Refonte prompt Perplexity rubber (`research_rubber_cambodia()`)
- [ ] 2.2 - Ajouter validation `_validate_rubber_prices()`
- [ ] 2.3 - Créer scénarios rubber Cambodia (optimiste/réaliste/pessimiste)
- [ ] 2.4 - Intégrer macro context (USD/KHR, CSX) dans rubber analysis

**Fichiers modifiés:**
- `app/services/perplexity_service.py`
- `app/services/market_trends_service.py`
- `app/api/routes/trends.py` (endpoint `/scenario`)

---

### **PHASE 3 : Frontend UI (Agent Frontend)**

**Responsable:** Agent `frontend-developer`

**Tâches:**
- [ ] 3.1 - Market Trends UI rubber: Afficher prix TradingEconomics
- [ ] 3.2 - Afficher farmgate estimate avec disclaimer
- [ ] 3.3 - Corriger sentiment Twitter (si 0 tweets → "Non calculé")
- [ ] 3.4 - Ajouter sources prix (TradingEconomics, WITS, FPMA)
- [ ] 3.5 - Visualisation exports Cambodia (chart destinations)

**Fichiers modifiés:**
- `ui/pages/5_Market_Trends.py` (section Rubber)
- `ui/pages/6_Scenario_Analysis.py` (rubber scenarios)

---

### **PHASE 4 : Tests & Validation (Agent Testing)**

**Responsable:** Agent `test-engineer` ou vous-même

**Tâches:**
- [ ] 4.1 - Test scraping TradingEconomics (prix récupéré OK)
- [ ] 4.2 - Test WITS rubber Cambodia (exports 2024 OK)
- [ ] 4.3 - Test farmgate estimate (Thailand → Cambodia -12%)
- [ ] 4.4 - Test scénarios UI (impact Cambodia visible)
- [ ] 4.5 - Validation E2E: Collection → Stockage → Affichage

---

## 🎯 MÉTRIQUES DE SUCCÈS

| Métrique | Avant | Après |
|----------|-------|-------|
| **Prix rubber source** | ❌ Non spécifié | ✅ TradingEconomics + source affichée |
| **Contexte Cambodia** | ❌ Absent | ✅ Exports, destinations, impact mentionnés |
| **Farmgate prices** | ❌ Absent | ✅ Estimé (Thailand proxy + disclaimer) |
| **Sentiment si 0 tweets** | ❌ "Neutre 50%" artificiel | ✅ "Non calculé" |
| **Validation prix** | ❌ Aucune | ✅ Warnings si hors ranges |
| **Sources données** | Perplexity seul | ✅ TradingEcon + WITS + FPMA |

---

## 💰 COÛT TOTAL

**Phase 1-4 :** **$0** (scraping gratuit + APIs gratuites)

---

## ⏱️ TIMELINE

| Phase | Durée | Tâches |
|-------|-------|--------|
| **Phase 1** | 3-5 jours | Collectors (TradingEcon, WITS, FPMA) |
| **Phase 2** | 3-5 jours | Services, validation, scénarios |
| **Phase 3** | 2-3 jours | Frontend UI updates |
| **Phase 4** | 2 jours | Tests E2E |
| **Total** | **10-15 jours** | |

---

## 🚦 PRÊT POUR DÉLÉGATION APEX

Ce brief contient toutes les informations pour lancer le workflow APEX et déléguer aux agents spécialisés.

**Prochaine étape:** Lancer `/analyze` puis `/plan` puis `/implement` avec délégation.
