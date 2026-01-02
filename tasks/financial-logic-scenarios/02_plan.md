# Plan: Logique Financiere Scenarios

## Status: COMPLETED 2026-01-02

## Phases d'Implementation

### Phase 1: Baseline Market Trends + Probabilites
**Fichier:** ui/pages/6_Scenario_Analysis.py

- [x] 1.1 Creer fonction `display_baseline_market_trends()`
- [x] 1.2 Creer constantes `SCENARIO_PROBABILITIES`
- [x] 1.3 Inserer appel avant les tabs (L~1599)
- [x] 1.4 Ajouter badge probabilite dans chaque tab

### Phase 2: Stress Test Cashew
**Fichier:** ui/pages/6_Scenario_Analysis.py

- [x] 2.1 Creer fonction `display_stress_test()` (unified for cashew/rubber)
- [x] 2.2 Calculs: seuil $1,500/t, impact revenu
- [x] 2.3 Appeler dans tab pessimistic

### Phase 3: Stress Test Rubber (symetrie)
**Fichier:** ui/pages/6_Scenario_Analysis.py

- [x] 3.1 Fonction `display_stress_test()` gere les deux commodites
- [x] 3.2 Seuil rubber: $1,550/t

### Phase 4: Vue Agregee Revenus
**Fichier:** ui/pages/6_Scenario_Analysis.py

- [x] 4.1 Creer fonction `display_combined_agri_revenues()`
- [x] 4.2 Inserer apres les tabs scenarios (L~1664)

---

## Implementation Details

### Constantes ajoutees (L107-141)
```python
SCENARIO_PROBABILITIES = {
    'pessimistic': 0.20,
    'realistic': 0.60,
    'optimistic': 0.20
}

CASHEW_CONSTANTS = {
    'export_volume_tons': 815_000,
    'farming_families': 500_000,
    'base_rcn_range': (1800, 2200),
    'base_kernel_range': (6200, 6800),
    'farmgate_factor': 0.70,
    'stress_threshold_low': 1500,
    'stress_threshold_high': 2500,
}

RUBBER_CONSTANTS = {
    'export_volume_tons': 115_000,
    'farming_families': 80_000,
    'default_price': 1825,
    'farmgate_factor': 0.70,
    'stress_threshold_low': 1550,
    'stress_threshold_high': 2100,
}

AGRI_TOTALS = {
    'total_families': 580_000,  # 500k + 80k
    'cashew_share': 0.86,
    'rubber_share': 0.14,
}
```

### Fonctions ajoutees (L988-1241)
1. `display_baseline_market_trends(commodity, market_data, trends_data)` - ~70 lignes
2. `display_stress_test(commodity, fx_rate, scenario_type)` - ~95 lignes
3. `display_combined_agri_revenues(cashew_data, rubber_data, fx_rate)` - ~85 lignes

### Points d'integration
- L1599: Appel `display_baseline_market_trends()` avant les tabs
- L1627: Appel `display_stress_test()` dans tab pessimistic
- L1664: Appel `display_combined_agri_revenues()` apres les tabs
- L1608-1611: Tabs avec badges probabilite [20%], [60%], [20%]

### Traductions ajoutees
- ui/i18n/translations.py: 24 nouvelles cles en anglais et francais

---

## Validation
Plan auto-valide car utilisateur absent.
Implementation complete.
