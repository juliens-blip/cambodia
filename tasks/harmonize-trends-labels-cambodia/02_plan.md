# Plan d'Implementation: Harmonisation Labels & Contexte Cambodia

## Informations
**Date:** 2026-01-02
**Base sur:** 01_analysis.md
**Approche:** Modifications UI + enrichissement service, 4 phases

---

## Objectif Final

Assurer coherence entre:
- Labels visuels (Strong Bullish/Neutral/etc) et synthese IA
- Affichage prix RCN vs Kernels pour cashew
- Contexte Cambodia visible dans Market Trends pour rubber
- Volume tweets explicite

---

## Gap Analysis

| Etat Actuel | Etat Cible | Action Requise |
|-------------|------------|----------------|
| Label valide silencieusement | Feedback utilisateur si correction | Ajouter message UI |
| RCN/Kernels en captions | Cartes separees ou section claire | Refactorer affichage |
| Tweet count en help text | Badge explicite avec volume | Ajouter indicateur |
| Trend label sans contexte | Phrase explicative si discrepancy | Ajouter sous-titre |
| Cambodia Snapshot absent | Section visible Market Trends | Creer nouvelle section |

---

## Checklist Technique (Step-by-Step)

### Phase 1: CASHEW - Label Harmonisation

- [ ] **1.1** - Ameliorer feedback validate_trend_label
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: ~485
  - Action: Si label corrige, afficher st.warning() avec explication
  - Code:
    ```python
    if trend != raw_trend:
        st.warning(f"Label ajuste: {raw_trend} -> {trend} (base sur analyse IA)")
    ```

- [ ] **1.2** - Ajouter phrase explicative sous label si discrepancy
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: ~500
  - Action: Ajouter caption avec contexte prix
  - Code:
    ```python
    if price_change and abs(price_change) > 5 and 'neutral' in trend:
        st.caption(f"Short-term: {price_change:+.1f}% but AI analysis: stable outlook")
    ```

### Phase 2: CASHEW - RCN vs Kernels Display

- [ ] **2.1** - Creer section distincte pour prix par segment
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: Apres ~607 (section Stock Market)
  - Action: Afficher deux colonnes si cashew
  - Code pattern:
    ```python
    if commodity == 'cashew' and price_type:
        col_rcn, col_kern = st.columns(2)
        with col_rcn:
            st.markdown("**RCN (Raw Cashew Nuts)**")
            st.caption("FOB Cambodia: $1,500-2,500/ton")
        with col_kern:
            st.markdown("**Kernels (Processed)**")
            st.caption("FOB Vietnam: $6,000-7,000/ton (W320)")
    ```

- [ ] **2.2** - Indiquer segment actuel dans Public Price Data
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: Section Public Price (~670-751)
  - Action: Ajouter badge indiquant si prix = RCN ou Kernels
  - Code:
    ```python
    if commodity == 'cashew' and price_type:
        st.info(f"Prix affiches: {price_type} ({price_context})")
    ```

### Phase 3: RUBBER - Tweet Volume & Trend Clarity

- [ ] **3.1** - Ajouter badge volume tweets explicite
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: ~520 (apres affichage sentiment)
  - Action: Badge coloré selon volume
  - Code:
    ```python
    if commodity == 'rubber' and actual_count > 0:
        volume_level = "low" if actual_count < 5 else "medium" if actual_count < 15 else "high"
        color = {"low": "orange", "medium": "blue", "high": "green"}[volume_level]
        st.markdown(f":{color}[{actual_count} tweets analyses ({volume_level} volume)]")
    ```

- [ ] **3.2** - Ajouter phrase explicative sous trend label
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: ~502
  - Action: Si rubber et discrepancy, expliquer
  - Code:
    ```python
    if commodity == 'rubber' and price_change:
        if abs(price_change) > 10 and 'neutral' in trend.lower():
            st.caption(f"Short-term: {price_change:+.1f}% on 30d | Forecast: stable range")
        elif price_change > 5 and 'neutral' in trend.lower():
            st.caption("Slightly bullish momentum, fundamentals stable")
    ```

### Phase 4: RUBBER - Cambodia Snapshot

- [ ] **4.1** - Enrichir service avec donnees Cambodia
  - Fichier: `app/services/market_trends_service.py`
  - Fonction: `_validate_rubber_prices()` (~L359-465)
  - Action: Ajouter fields constants
  - Code:
    ```python
    # Cambodia rubber context (static data)
    parsed['cambodia_exports_tons'] = 115000
    parsed['cambodia_farming_families'] = 80000
    parsed['cambodia_export_destinations'] = {
        'China': 60, 'Vietnam': 20, 'Singapore': 10, 'Others': 10
    }
    parsed['cambodia_main_provinces'] = ['Kampong Cham', 'Kratie', 'Mondulkiri']
    ```

- [ ] **4.2** - Creer section Cambodia Snapshot dans UI
  - Fichier: `ui/pages/5_Market_Trends.py`
  - Ligne: Apres ~634 (apres Farmgate Estimate)
  - Action: Nouvelle section avec metriques
  - Code pattern:
    ```python
    if commodity == 'rubber':
        st.markdown("---")
        st.markdown("### Cambodia Rubber Snapshot")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Annual Exports", "115,000 t")
        with col2:
            st.metric("Farming Families", "80,000")
        with col3:
            farmgate = latest.get('farmgate_estimate_khr_kg', 0)
            st.metric("Farmgate", f"{farmgate:,.0f} KHR/kg")

        st.caption("Destinations: China 60% | Vietnam 20% | Singapore 10%")
        st.caption("Provinces: Kampong Cham, Kratie, Mondulkiri")
    ```

---

## Risques Identifies

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Donnees Cambodia hardcodees | Moyen | Acceptable pour MVP, planifier API future |
| Surcharge UI si trop d'infos | Moyen | Utiliser expanders/tabs si necessaire |
| Performance si calculs lourds | Faible | Donnees deja en cache DB |

---

## Points de Validation

- [ ] Labels coherents entre UI et synthese IA
- [ ] RCN vs Kernels clairement distingues pour cashew
- [ ] Volume tweets visible pour rubber
- [ ] Trend label avec contexte si discrepancy
- [ ] Cambodia Snapshot visible pour rubber
- [ ] Pas de regression sur fonctionnalites existantes

---

## Estimation

- **Complexite:** Moyenne
- **Fichiers modifies:** 2 (5_Market_Trends.py, market_trends_service.py)
- **Lignes ajoutees:** ~100-150
- **Dependances:** Aucune nouvelle

---

## Pret pour Implementation

- [x] Analyse complete (01_analysis.md)
- [ ] Plan valide par l'utilisateur
- [x] Toutes les dependances identifiees
- [x] Strategie claire et sans ambiguite
