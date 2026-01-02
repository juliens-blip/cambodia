# Brief: Ameliorations Logique Financiere - Scenarios Cashew & Rubber

## Date: 2026-01-02
## Priorite: Haute
## Budget: 0 EUR (pas de nouvelles APIs)

---

## OBJECTIF GLOBAL

Renforcer la coherence financiere et l'analyse de risque dans les scenarios, avec une vue agregee des revenus agricoles Cambodia (cashew + rubber).

---

## 1. CASHEW - Logique de marche et risque

### 1.1 Relier Market Trends ↔ Scenarios
- Ajouter bloc "Baseline Market Trends" dans Scenario Analysis cashew:
  - RCN FOB Cambodia: $1,950-2,150/ton
  - Kernels W320 FOB Vietnam: $6,300-6,700/ton
  - Trend global (Neutral) + confidence score
- Calculer scenarios (pessimiste/optimiste) = ±15% autour du baseline

### 1.2 Standardiser les probabilites
- Pessimistic: 20%
- Realistic: 60%
- Optimistic: 20%
- Afficher en badge ou tableau par scenario
- Stocker dans la base (optionnel pour MVP)

### 1.3 Indicateurs de risque familles
- Revenue total familles = volume RCN (~815,000 t) x farmgate moyen (KHR/kg)
- Impact choc ±10% sur RCN FOB: variation % revenu
- Bloc "Stress Test":
  - Ex: "Si RCN < $1,500/t, revenu agrege tombe sous X M USD"

---

## 2. RUBBER - Symetrie avec cashew

### 2.1 Memes blocs que cashew
- Baseline Market Trends (prix spot ~$1,800/ton, trend, confiance)
- Scenarios pessimiste/realiste/optimiste (±15%)
- Cambodia Impact (exports 115k t, farmgate KHR/kg, revenus, 80k familles)

---

## 3. VUE AGREGEE - Revenus agricoles totaux Cambodia

### 3.1 Module combine cashew + rubber
- Revenus exports cashew + rubber (USD)
- Nombre total familles dependantes (~580k cashew + 80k rubber)
- Part cashew vs rubber (%)
- Vision "macro revenu agricole" pour usage financier

---

## FICHIERS CONCERNES (estimation)

| Fichier | Modifications |
|---------|---------------|
| ui/pages/6_Scenario_Analysis.py | Baseline bloc, probabilites, stress test, vue agregee |
| app/api/routes/trends.py | Ajustements scenarios avec baseline |
| app/services/market_trends_service.py | Calculs revenus, stress test |

---

## LIVRABLES

1. Bloc "Baseline Market Trends" dans Scenario Analysis (cashew + rubber)
2. Probabilites affichees par scenario (20%/60%/20%)
3. Bloc "Stress Test" avec indicateurs risque familles
4. Section "Revenus Agricoles Totaux Cambodia" agregee
5. Documentation MEMOIRE_CLAUDE.md
