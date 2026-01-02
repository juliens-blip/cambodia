# Analyse: Logique Financiere Scenarios

## Fichiers Concernes

### 1. ui/pages/6_Scenario_Analysis.py

**Fonctions existantes:**
- `display_cambodia_metrics_cashew()` (L955-1067): Affiche impact cashew
- `display_cambodia_impact_rubber()` (L1069-1196): Affiche impact rubber
- `display_scenario_analysis()` (L1199-1232): Wrapper affichage scenario

**Points d'insertion:**
- **Baseline bloc**: Avant L1309 (avant les tabs scenarios)
- **Probabilites**: Dans chaque tab (L1316, L1332, L1348)
- **Stress Test**: Dans `display_cambodia_metrics_cashew()` (apres L1066)
- **Vue agregee**: Apres L1362 (apres les 3 tabs)

### 2. Constantes financieres (deja definies)

**Cashew:**
- `export_volume_tons = 815_000` (L980)
- `families = 500_000` (L986)
- `base_rcn_range = (1800, 2200)` (L957)
- `base_kernel_range = (6200, 6800)` (L958)
- `farmgate_factor = 0.70` (L969)

**Rubber:**
- `EXPORT_VOLUME_TONS = 115_000` (L1086)
- `FARMING_FAMILIES = 80_000` (L1087)
- `current_price = 1825` (L1074)
- `RUBBER_FARMGATE_FACTOR = 0.70` (importé)

---

## Architecture Cible

```
Scenario Analysis Page
|
+-- Header + Commodity Selector
+-- Data Sources Summary
+-- Macro Indicators (FX, CSX)
+-- Documents Used
+-- Key Tweet
|
+-- [NOUVEAU] Baseline Market Trends
|   +-- Current prices (RCN/Kernels ou Rubber spot)
|   +-- Overall trend + confidence
|   +-- Scenario probabilities badge
|
+-- Scenario Tabs
|   +-- Pessimistic [20%] avec Stress Test
|   +-- Realistic [60%]
|   +-- Optimistic [20%]
|
+-- [NOUVEAU] Vue Agregee Revenus Agricoles Cambodia
    +-- Total exports cashew + rubber
    +-- Total familles (580k)
    +-- Part cashew vs rubber (%)
```

---

## Elements a Implementer

### 1. Fonction display_baseline_market_trends()
```python
def display_baseline_market_trends(commodity: str, market_data: dict, trends_data: dict):
    # Affiche:
    # - Prix courant (RCN/Kernels ou Rubber)
    # - Trend label (Neutral/Bullish/Bearish)
    # - Confidence score
    # - Scenario probabilities (20%/60%/20%)
```

### 2. Fonction display_scenario_probabilities()
```python
SCENARIO_PROBABILITIES = {
    'pessimistic': 0.20,
    'realistic': 0.60,
    'optimistic': 0.20
}
```

### 3. Fonction display_stress_test_cashew()
```python
def display_stress_test_cashew(fx_rate: float):
    # Calcule:
    # - Revenue total familles = 815k t x farmgate moyen
    # - Impact choc ±10% sur RCN FOB
    # - Seuil critique: "Si RCN < $1,500/t, revenu < X M USD"
```

### 4. Fonction display_combined_agri_revenues()
```python
def display_combined_agri_revenues(cashew_data: dict, rubber_data: dict, fx_rate: float):
    # Agregation:
    # - Revenus cashew + rubber (USD)
    # - Familles totales: 580k (500k + 80k)
    # - Part: cashew 87% / rubber 13%
```

---

## Calculs Financiers

### Revenus Cashew
```
Volume RCN: 815,000 t
Farmgate moyen: ~$1.40/kg (70% de $2,000/t FOB)
Revenu total: 815,000 t x 1,400 USD/t = $1.14B
```

### Revenus Rubber
```
Volume: 115,000 t
Prix spot: ~$1,825/t
Farmgate: 70% = $1,277/t
Revenu total: 115,000 t x 1,277 USD/t = $147M
```

### Agregation
```
Total exports: $1.14B + $147M = $1.29B
Familles: 500,000 + 80,000 = 580,000
Part cashew: 88% / rubber: 12%
```

---

## Stress Tests

### Cashew
- Seuil bas: RCN < $1,500/t
- Impact: Revenu tombe a ~$855M (-25%)
- Familles touchees: 500,000

### Rubber
- Seuil bas: Prix < $1,550/t (-15%)
- Impact: Revenu tombe a ~$125M (-15%)
- Familles touchees: 80,000
