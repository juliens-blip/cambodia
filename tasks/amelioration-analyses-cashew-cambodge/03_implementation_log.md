# Journal d'Implementation: Amelioration Analyses Cashew Cambodge

## Informations
**Date debut:** 2026-01-01
**Base sur:** 02_plan.md (valide)
**Statut:** Phase 1 complete, Phase 2 in progress

---

## Progression

### Phase 1.1: Refonte Prompts Perplexity
- [x] **1.1.1** - Modifier `research_daily_prices()` dans `perplexity_service.py`
  - Fichier: `app/services/perplexity_service.py` L36-84
  - Ajout: Distinction RCN vs Kernels, FOB vs farmgate, grades qualite
  - Ajout: Contexte cambodgien (2e producteur, 90% Vietnam)
  - Notes: Prompt conditionnel selon commodity (cashew vs rubber)

- [x] **1.1.2** - Modifier `analyze_market_trends()` dans `perplexity_service.py`
  - Fichier: `app/services/perplexity_service.py` L523-618
  - Ajout: Block contexte cambodgien avant INTEGRATED SYNTHESIS
  - Ajout: Exigence de clarifier RCN vs Kernels dans output
  - Notes: Contexte injecte dynamiquement si commodity == 'cashew'

---

### Phase 1.2: Validation Prix
- [x] **1.2.1** - Creer fonction `_validate_prices_cambodia()` dans `market_trends_service.py`
  - Fichier: `app/services/market_trends_service.py` L317-390
  - Detection automatique: RCN ($1,500-2,500) vs Kernels ($5,000-9,000)
  - Ajout: price_type, price_context, price_segment, price_clarification
  - Ajout: price_warnings pour cas limites

- [x] **1.2.2** - Appeler `_validate_prices_cambodia()` dans `_parse_analysis()`
  - Fichier: `app/services/market_trends_service.py` L312-313
  - Appel automatique apres parsing standard
  - Notes: Validation appliquee uniquement pour cashew

---

### Phase 1.3: Scenarios Cambodgiens
- [x] **1.3.1** - Creer template contexte cambodgien dans `trends.py`
  - Fichier: `app/api/routes/trends.py` L340-382
  - Block complet: Global ranking, export structure, producer profile
  - Block: Market vulnerabilities et price reference guide
  - Notes: Injecte uniquement si commodity == 'cashew'

- [x] **1.3.2** - Modifier scenario_prompts dans `trends.py`
  - Fichier: `app/api/routes/trends.py` L384-444
  - 3 scenarios modifies: pessimistic, realistic, optimistic
  - Ajout: Focus sur impact farmers, RCN vs Kernels, farmgate KHR/kg
  - Limite: 350 mots (augmente de 300)

---

### Phase 1.4: Alignement Labels UI
- [x] **1.4.1** - Creer fonction `validate_trend_label()` dans `5_Market_Trends.py`
  - Fichier: `ui/pages/5_Market_Trends.py` L83-144
  - Detection: neutral_indicators, bullish_indicators, bearish_indicators
  - Cross-validation: avec price_change_pct
  - Notes: Retourne label corrige si incoherence detectee

- [x] **1.4.2** - Appeler validation dans affichage trend
  - Fichier: `ui/pages/5_Market_Trends.py` L436-463
  - Validation appelee avant affichage metric
  - Debug log si label corrige
  - Notes: Ne modifie pas la base, juste l'affichage

---

### Phase 2.1: Collecteurs Sources Gratuites
- [x] **2.1** - Creer `app/collectors/fao_giews_collector.py`
  - CSV discovery via price tool + URLs configurees
  - Parsing CSV (Cambodia + cashew) et normalisation
  - Metadata: currency, unit, market, product

- [x] **2.2** - Creer `app/collectors/cac_collector.py`
  - Scraping CAC pour liens PDF
  - Extraction texte via PDFParser
  - Enregistrement documents context + production si detectee

---

### Phase 2.2: Ingestion et Scheduler
- [x] **2.3** - Ajout helpers ingestion dans `app/scheduler/jobs.py`
  - `run_collectors()` + `store_data_dual()` + `init_services()`
  - Mapping prix / production / context_documents

- [x] **2.4** - Ajout note latence des sources dans les prompts
  - FAO GIEWS = mensuel, WITS/Comtrade = annuel
  - Fichier: `app/services/perplexity_service.py`

- [x] **2.5** - Job mensuel "free sources"
  - FAO GIEWS + CAC + WITS (HS 080130, partner VNM)
  - Cron: day 1, 03:00 UTC

## Problemes Rencontres
| Etape | Probleme | Solution | Temps perdu |
|-------|----------|----------|-------------|
| - | Aucun probleme majeur | - | 0min |

---

## Modifications Apportees

| Fichier | Type | Description |
|---------|------|-------------|
| `app/services/perplexity_service.py` | Modifie | Prompts RCN/Kernels + contexte Cambodge |
| `app/services/market_trends_service.py` | Modifie | Validation prix + clarification |
| `app/api/routes/trends.py` | Modifie | Scenarios cambodgiens detailles |
| `ui/pages/5_Market_Trends.py` | Modifie | Validation coherence labels |
| `app/collectors/fao_giews_collector.py` | Cree | Collector FAO GIEWS / FPMA (CSV) |
| `app/collectors/cac_collector.py` | Cree | Collector CAC (PDFs) |
| `app/collectors/__init__.py` | Modifie | Exports nouveaux collecteurs |
| `app/scheduler/jobs.py` | Modifie | Ingestion + job mensuel |
| `.env.example` | Modifie | Variables FAO/CAC |
| `app/config.py` | Modifie | Settings FAO/CAC |
| `tasks/amelioration-analyses-cashew-cambodge/01_analysis.md` | Cree | Analyse codebase |
| `tasks/amelioration-analyses-cashew-cambodge/02_plan.md` | Cree | Plan implementation |
| `tasks/amelioration-analyses-cashew-cambodge/03_implementation_log.md` | Cree | Ce fichier |

---

## Resultat Final
**Statut:** Phase 2 en cours (collecteurs + scheduler ajoutes)

---

## Checklist de Validation
- [x] Code modifie (4 fichiers)
- [ ] Tests manuels (a faire apres deploy)
- [ ] Aucune regression (a verifier)
- [x] Documentation a jour (journal cree)

---

## Resume des Ameliorations

### 1. Prompts Perplexity (perplexity_service.py)
**Avant:**
```
Analyze current market conditions for {commodity} in Cambodia:
1. Latest export prices (USD per ton)
...
```

**Apres:**
```
**Price Segmentation Requirements:**
1. RCN (Raw Cashew Nuts) vs Kernels (processed)
   - RCN FOB Cambodia: Typical range $1,500-2,500/ton
   - Kernels FOB Vietnam: Typical range $6,000-7,000/ton (W320 grade)

**Cambodia Context (MANDATORY):**
- 2nd largest RCN producer globally (~850,000 tonnes/year)
- 90% exports to Vietnam for processing
...
```

### 2. Validation Prix (market_trends_service.py)
**Nouveau:**
- Detection automatique type produit selon range prix
- Ajout price_type, price_context, price_clarification
- Guide de reference pour affichage UI

### 3. Scenarios (trends.py)
**Avant:** Scenarios generiques sans contexte Cambodge
**Apres:**
- Block contexte cambodgien (global ranking, export structure, vulnerabilities)
- Focus sur impact farmers (farmgate KHR/kg)
- Distinction RCN vs Kernels obligatoire

### 4. Labels UI (5_Market_Trends.py)
**Nouveau:**
- Fonction validate_trend_label()
- Cross-validation avec contenu analyse et price_change
- Correction automatique si incoherence detectee

---

## Prochaines Etapes Recommandees

1. **Tests manuels** apres deploy sur Railway
   - POST /api/v1/trends/analyze/cashew?force_refresh=true
   - Verifier presence contexte cambodgien
   - Verifier prix RCN vs Kernels distincts

2. **Phase 2**: Tests ingestion free sources
   - Lancer collecteurs FAO/CAC
   - Verifier stockage Supabase + indexation context_documents

3. **Monitoring**: Verifier qualite analyses pendant 1 semaine

---

*Journal complete le 2026-01-01*

---

## ADDENDUM (2026-01-01) - PHASE 2 UPDATE

Phase 2 implementation started:
- FAO GIEWS/FPMA CSV collector added.
- CAC PDF collector added.
- Monthly scheduler job added (free sources).

Remaining:
- Run ingestion tests.
- Confirm WITS HS 080130 coverage and adjust if needed.

---

## ADDENDUM (2026-01-01) - PHASE 2 API + CRAWL

Updates:
- FAO collector now uses FPMA API (FpmaSerie + FpmaSeriePrice via uuid__in).
- CAC collector now crawls /report and /news pages to find PDF attachments.
- WITS collector now supports HS6 download (Download.aspx) for product 080130.
- New settings in config/.env.example: FAO_GIEWS_API_BASE_URL, CAC_MAX_PAGES.

Tests (local):
- FAO FPMA, Cambodia filter: 0 records (no cashew series for KHM).
- FAO FPMA, GNB filter (sanity): records returned, price_value_dollar parsed.
- CAC collector with seed /report, max_pages=10: 1 PDF found (context doc).
- WITS HS6 download (KHM->VNM, 080130): records returned for 2021-2023.

Fixes:
- Supabase prices.volume_tons expects integer: normalize/round volume_tons before upsert.
- Supabase production upsert now uses on_conflict (commodity_id,year,province,source).
- WITS HS6 rows now store unit price (USD/ton) instead of total trade value to avoid numeric overflow.
- Supabase price upsert now uses select+update/insert to avoid partial index conflicts.
- Market trends storage now updates existing (commodity, trend_date) rows instead of failing on duplicates.
- Scenario prompts now label cashew benchmark price as kernel FOB Vietnam (W320) to avoid ambiguity.
- Market trends now use Cambodia timezone date to avoid stale trend_date after local day rollover.

Ingestion (monthly_free_sources_collection):
- Completed with summary: prices=3, production=3, documents=6.

Scenario refresh (local):
- Generated scenarios via `generate_scenario_analysis` for cashew:
  - pessimistic, realistic, optimistic.
- Remote Railway endpoints returned 403; ran locally instead.
