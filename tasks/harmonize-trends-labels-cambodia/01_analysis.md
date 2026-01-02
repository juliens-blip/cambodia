# Analyse: Harmonisation Labels & Contexte Cambodia

## Contexte
**Date:** 2026-01-02
**Demande initiale:** Harmoniser labels visuels avec synthese IA + exposer contexte Cambodia
**Objectif:** Coherence UI/IA pour cashew et rubber, ajout Cambodia Snapshot

---

## Etat Actuel de la Codebase

### Fichiers Concernes

| Fichier | Type | Role | Lignes cles |
|---------|------|------|-------------|
| ui/pages/5_Market_Trends.py | UI | Affichage trends | L120-181, L469-634 |
| app/services/market_trends_service.py | Service | Parsing et validation | L359-540 |
| app/api/routes/trends.py | API | Endpoints trends | L47-71, L364-459 |

### Architecture Actuelle

```
Perplexity AI (analyse texte)
       |
       v
market_trends_service._parse_analysis()
  |-- Extraction sentiment (bullish/bearish/neutral)
  |-- Validation prix (RCN vs Kernels pour cashew)
  |-- Calcul farmgate (pour rubber)
  |-- Storage en DB
       |
       v
API /latest/{commodity}
  |-- overall_trend, twitter_sentiment, tweet_count
  |-- stock_price_usd, price_type, price_context
  |-- farmgate_estimate_khr_kg, farmgate_estimate_usd_kg
  |-- ai_analysis (full text)
       |
       v
5_Market_Trends.py
  |-- validate_trend_label() for coherence check
  |-- Display labels + metrics
  |-- Show RCN/Kernels distinction (minimal)
  |-- Cambodia Snapshot (MANQUANT pour rubber)
```

---

## Code Snippets Cles

### 1. validate_trend_label (L120-181) - EXISTE DEJA
```python
def validate_trend_label(ai_analysis: str, current_label: str, price_change_pct: float = None) -> str:
    """
    Validate that trend label matches AI analysis content and price change.
    """
    neutral_indicators = ['neutral', 'stable', 'sideways', 'range-bound', '+/-3%', 'flat']
    bullish_indicators = ['bullish', 'upward', 'rising', 'increasing']
    bearish_indicators = ['bearish', 'downward', 'falling', 'decreasing']
    # Cross-validates with price change %
    # Returns validated label
```

### 2. Affichage Twitter Sentiment (L503-531)
```python
tweet_count = latest.get('tweet_count', 0)
if actual_count == 0:
    st.metric("Twitter Sentiment", "Non calcule", help="Aucun tweet trouve")
else:
    st.metric(..., help=f"Base sur {actual_count} tweets analyses")
```
**Probleme:** Help text seulement, pas de badge explicite

### 3. Affichage RCN/Kernels (L589-607)
```python
price_type = latest.get('price_type', 'Price')
price_context = latest.get('price_context', '')
if price_type:
    st.caption(f"Type: {price_type}")
if price_context:
    st.caption(price_context)
```
**Probleme:** Affichage minimaliste, pas de cartes separees

### 4. Farmgate Rubber (L618-633)
```python
if commodity == 'rubber':
    farmgate_khr = latest.get('farmgate_estimate_khr_kg')
    farmgate_usd = latest.get('farmgate_estimate_usd_kg')
    if farmgate_khr or farmgate_usd:
        st.markdown("**Farmgate Estimate (Cambodia):**")
```
**Manque:** Section "Cambodia Snapshot" apres cette zone

---

## Points d'Attention

### CASHEW
1. validate_trend_label() EXISTE mais feedback limie
2. RCN vs Kernels affiche en captions minimalistes
3. Public Price Data ne montre pas distinction RCN/Kernels
4. Alertes peuvent se declencher sur segments heterogenes

### RUBBER
1. tweet_count existe en DB mais affichage via help text seulement
2. Label "Neutral" sans explication si prix +11.7%
3. Cambodia Snapshot existe dans Scenario Analysis (L406-459) mais PAS dans Market Trends
4. Farmgate affiche mais sans contexte exports/familles

---

## Dependances

### Internes
- 5_Market_Trends.py -> market_trends_service (via API)
- market_trends_service -> supabase_service (DB storage)
- trends.py -> market_trends_service (analyze_and_store_trends)

### Externes (deja installes)
- streamlit: UI framework
- httpx: API calls
- plotly: Charts

---

## Opportunites Identifiees

1. **Reutiliser context Cambodia** de trends.py (L364-459) pour Market Trends
2. **Ameliorer validate_trend_label** avec message explicite si correction
3. **Ajouter badge volume tweets** (low/medium/high)
4. **Creer section Cambodia Snapshot** pour rubber dans Market Trends

---

## Resume Executif

1. La logique de validation labels EXISTE (validate_trend_label) mais feedback minimal
2. RCN vs Kernels detection EXISTE dans service mais affichage UI minimaliste
3. Cambodia context EXISTE dans scenario API mais absent de Market Trends
4. Tweet count EXISTE en DB mais pas de badge volume explicite
5. Modifications principalement UI (5_Market_Trends.py) + enrichissement data service
