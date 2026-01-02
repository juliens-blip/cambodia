# Brief: Harmonisation Labels & Contexte Cambodia

## Date: 2026-01-02
## Source: Feedback utilisateur + Perplexity AI

---

## CASHEW - Axes d'amelioration

### 1) Harmoniser label visuel et synthese
**Probleme actuel:**
- Synthese IA: "Overall Market Trend: neutral (-3% a +3% attendu)"
- Dashboard: "Strong Bullish" avec +8% sur 24h

**Amelioration requise:**
- Ajouter fonction de reconciliation entre label UI et contenu IA
- Si incoherence detectee, ajuster le label ou ajouter disclaimer

### 2) Mieux exposer RCN vs Kernels
**Probleme actuel:**
- Prix affiches sans distinction claire RCN/Kernels
- Alertes (+8%, +16%) peuvent se declencher sur segments heterogenes

**Amelioration requise:**
- Afficher deux cartes separees ou legende claire:
  - "Public Price (RCN FOB Cambodia)"
  - "Public Price (Kernels W320 FOB Vietnam)"
- Verifier que les alertes se declenchent sur le meme segment

---

## RUBBER - Axes d'amelioration

### 1) Aligner sentiment Twitter avec synthese
**Probleme actuel:**
- Texte: "Overall Twitter Sentiment: Neutral (stable prices)"
- UI: Affichage sans contexte du volume de tweets

**Amelioration requise:**
- Afficher nombre de tweets analyses
- Tooltip ou badge "12 tweets analyses (low volume)"

### 2) Label de tendance neutre mais plus explicite
**Probleme actuel:**
- Label "Neutral" mais barres montrent +11.7% sur 30 jours
- Impression visuelle de rally vs synthese stable

**Amelioration requise:**
- Ajouter phrase courte sous le label:
  - "Short-term: +11.7% on 30 days, but long-term forecasts stable 175-185 c/kg"
- Regles de resolution:
  - Si price_change_30d entre -5% et +5% ET synthese = neutral -> label neutral
  - Si > +10% mais textes "stable" -> "Slightly Bullish", pas "Strong Bullish"

### 3) Mieux exposer l'impact Cambodge dans Market Trends
**Probleme actuel:**
- Impact Cambodge (115k t, 80k familles, farmgate) visible seulement dans Scenario Analysis
- Pas dans Market Trends

**Amelioration requise:**
- Ajouter encadre "Cambodia Snapshot" dans Market Trends (rubber):
  - "Exports: 115,000 t/an (mainly China/Vietnam)"
  - "Farmgate: ~3,500-4,000 KHR/kg (~1,000-1,150 $/t)"
  - "Households: 80,000 familles dependantes du rubber"

---

## Fichiers concernes (estimation)

| Fichier | Modifications |
|---------|---------------|
| ui/pages/5_Market_Trends.py | Label reconciliation, RCN/Kernels cards, Cambodia Snapshot |
| app/services/market_trends_service.py | Logique validation labels |
| app/api/routes/trends.py | Ajustements reponse API |

## Budget: 0 EUR (pas de nouvelles APIs)
## Priorite: Haute (UX coherence)
