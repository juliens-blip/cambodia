# Plan d'Implémentation: ODC Scraper Improvement

## 📋 Informations
**Date:** 2025-12-25
**Basé sur:** 01_analysis.md
**Approche:** Découverte dynamique via search ODC + parsing BeautifulSoup4
**Complexité:** Moyenne (1 fichier modifié, 0 nouvelles dépendances)

## 🎯 Objectif Final
Passer de **30 sample records** à **50-150 production records** réels d'Open Development Cambodia en implémentant:
1. Découverte dynamique de datasets via recherche ODC
2. Parsing HTML robuste avec BeautifulSoup4 + lxml
3. Support multi-formats (CSV/JSON/XLS) pour extraction de données

## 📊 Gap Analysis

| État Actuel | État Cible | Action Requise |
|-------------|------------|----------------|
| 4 URLs hardcodées (404) | Découverte dynamique | Search "cashew/rubber" dans catalogue ODC |
| Regex fragile `re.findall()` | BeautifulSoup parsing | Remplacer par `soup.find_all()` |
| 30 sample records | 50-150 real records | Download + parse datasets découverts |
| Logs DEBUG seulement pour 404 | Logs INFO pour découverte | Améliorer visibilité |
| Limite 5 ressources/dataset | Limite 10 ressources | Augmenter coverage |

**Note:** ODC contient **9 datasets cashew** et **118 datasets rubber** selon recherche du 2025-12-25

## 🏗️ Architecture Proposée

```
┌──────────────────────────────────────────────────────────────┐
│                    ODCCollector.collect()                     │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐               ┌──────────────┐
│  PHASE 1      │               │  FALLBACK    │
│  Discovery    │───── fail ────►  Sample Data │
└───────┬───────┘               └──────────────┘
        │ success
        │
        ▼
┌─────────────────────────────────────────┐
│ _discover_datasets(commodity)           │
│ ├─ Search ODC: q="agriculture {commodity}" │
│ ├─ Parse HTML avec BeautifulSoup       │
│ ├─ Extract dataset URLs                 │
│ └─ Filter keywords + validate           │
└───────┬─────────────────────────────────┘
        │ returns List[str] dataset_urls
        │
        ▼
┌─────────────────────────────────────────┐
│ For each dataset_url:                   │
│ ├─ GET dataset page                     │
│ ├─ _extract_resource_urls(html)         │
│ │   └─ BeautifulSoup find CSV/JSON/XLS  │
│ ├─ Download resource                    │
│ └─ _parse_resource() → records          │
└─────────────────────────────────────────┘
```

**Flux Amélioré:**
```
Cashew/Rubber → Discovery Search → 3-5 URLs valides → Extract resources → Parse → 50-150 records
```

## 📝 Checklist Technique (Step-by-Step)

### Phase 1: Découverte Dynamique de Datasets

#### 1.1 - Créer méthode `_discover_datasets()`
**Fichier:** `app/collectors/odc_collector.py`
**Ligne d'insertion:** Après `_create_sample_data()` (ligne ~315)
**Longueur estimée:** ~60 lignes

- [ ] Créer méthode async `_discover_datasets(client, commodity)`
- [ ] Build search URL: `{base_url}?q=agriculture+{commodity}`
- [ ] GET search results avec retry (2 attempts)
- [ ] Parse HTML avec BeautifulSoup + lxml backend
- [ ] Find dataset links: `<a href="/en/(dataset|library_record)/">`
- [ ] Filter par keywords: ["production", "statistics", "agriculture", commodity]
- [ ] Deduplicate + limit 5 URLs max
- [ ] Log INFO: URLs découvertes
- [ ] Return List[str]

**Validation:**
- [ ] Code compile sans erreur
- [ ] Retourne liste de strings (URLs)
- [ ] Log INFO affiche URLs découvertes
- [ ] Max 5 URLs retournées
- [ ] Retry logic 2 attempts

---

#### 1.2 - Intégrer découverte dans `collect()`
**Fichier:** `app/collectors/odc_collector.py`
**Lignes à modifier:** 31-41 (suppression self.dataset_urls) + 56-57 (appel discovery)

- [ ] Supprimer hardcoded URLs (lignes 31-41)
- [ ] Remplacer par `self.dataset_urls = {}`
- [ ] Dans `collect()`: itérer sur `["cashew", "rubber"]`
- [ ] Appeler `await self._discover_datasets(client, commodity)`
- [ ] Gérer cas discovery retourne []
- [ ] Log WARNING si aucun dataset découvert

**Validation:**
- [ ] Boucle itère sur ["cashew", "rubber"]
- [ ] Appelle `_discover_datasets()` pour chaque commodity
- [ ] Gère cas où discovery retourne []
- [ ] Aucun hardcoded URL restant

---

### Phase 2: Parsing HTML avec BeautifulSoup4

#### 2.1 - Ajouter imports nécessaires
**Fichier:** `app/collectors/odc_collector.py`
**Ligne:** 7 (après `import json`)

- [ ] Import: `from bs4 import BeautifulSoup`
- [ ] Import: `import asyncio` (pour retry sleep)

**Validation:**
- [ ] Import BeautifulSoup présent
- [ ] Import asyncio présent
- [ ] Pas d'erreur ImportError au lancement

---

#### 2.2 - Remplacer regex par BeautifulSoup dans `_extract_resource_urls()`
**Fichier:** `app/collectors/odc_collector.py`
**Méthode:** `_extract_resource_urls()` (lignes 126-149)

- [ ] Supprimer regex: `re.findall(csv_pattern, html)`
- [ ] Parse HTML: `soup = BeautifulSoup(html, 'lxml')`
- [ ] Find links: `soup.find_all('a', href=re.compile(...))`
- [ ] Supporter: .csv, .json, .xls, .xlsx, .zip, /download/
- [ ] Créer helper `_normalize_url(href)` pour URLs relatives
- [ ] Augmenter limite: 5 → 10 ressources
- [ ] Deduplicate avec `dict.fromkeys()`
- [ ] Log DEBUG: nombre URLs extraites

**Validation:**
- [ ] Code utilise BeautifulSoup au lieu de regex
- [ ] Support .csv, .json, .xls, .xlsx, .zip
- [ ] URLs relatives converties en absolues
- [ ] Limite augmentée: 5 → 10 ressources
- [ ] Déduplication implémentée

---

### Phase 3: Support Multi-Formats

#### 3.1 - Améliorer détection de formats dans `_download_and_parse()`
**Fichier:** `app/collectors/odc_collector.py`
**Méthode:** `_download_and_parse()` (lignes 152-215)

- [ ] Ajouter condition: `elif url.endswith(('.xls', '.xlsx')):`
- [ ] Appeler nouvelle méthode `_parse_excel(data, commodity, url)`
- [ ] Garder existing logic pour JSON + CSV
- [ ] Try/except robuste pour chaque format

**Validation:**
- [ ] Support JSON (détection par extension + content)
- [ ] Support CSV (default)
- [ ] Support Excel (.xls, .xlsx) - NOUVEAU
- [ ] Fallback robuste en cas d'erreur

---

#### 3.2 - Créer méthode `_parse_excel()`
**Fichier:** `app/collectors/odc_collector.py`
**Ligne d'insertion:** Après `_parse_json()` (~276)

- [ ] Créer méthode `_parse_excel(data: bytes, commodity, url)`
- [ ] Import pandas (déjà installé)
- [ ] Read Excel: `df = pd.read_excel(io.BytesIO(data))`
- [ ] Iterate rows: `for _, row in df.iterrows():`
- [ ] Réutiliser `_parse_csv_row()` pour mapping
- [ ] Log INFO: nombre records parsés
- [ ] Try/except + log WARNING si échec

**Validation:**
- [ ] Méthode `_parse_excel()` créée
- [ ] Utilise pandas.read_excel()
- [ ] Réutilise `_parse_csv_row()` pour mapping
- [ ] Log WARNING si parsing échoue

---

### Phase 4: Amélioration Logging & Resilience

#### 4.1 - Augmenter logging pour découverte
**Fichier:** `app/collectors/odc_collector.py`

- [ ] Log INFO: "Searching ODC for '{commodity}' datasets..."
- [ ] Log INFO: "Search URL: {search_url}"
- [ ] Log INFO: "Discovered {n} datasets for {commodity}"
- [ ] Log WARNING si aucun dataset trouvé
- [ ] Log INFO résumé total datasets découverts

**Validation:**
- [ ] Log INFO pour début de search
- [ ] Log INFO pour URLs découvertes
- [ ] Log WARNING si aucun dataset trouvé
- [ ] Log résumé total de découverte

---

#### 4.2 - Améliorer fallback sample data
**Fichier:** `app/collectors/odc_collector.py`
**Ligne:** ~98 (condition fallback)

- [ ] Améliorer message: "No ODC data found after discovery + parsing..."
- [ ] Lister causes possibles dans log WARNING
- [ ] Ajouter metadata: `fallback_reason = "discovery_failed_or_no_parseable_resources"`
- [ ] Garder fallback pour resilience

**Validation:**
- [ ] Message warning plus explicite
- [ ] Causes possibles listées
- [ ] Metadata enrichie avec `fallback_reason`

---

### Phase 5: Tests & Validation

#### 5.1 - Test manuel découverte
**Command:**
```bash
cd D:\Projects\cambodia

python -c "
import asyncio
import httpx
from app.collectors.odc_collector import ODCCollector
from app.config import settings

async def test():
    collector = ODCCollector(settings.odc_base_url)
    async with httpx.AsyncClient() as client:
        urls = await collector._discover_datasets(client, 'cashew')
        print(f'Cashew datasets: {urls}')

        urls = await collector._discover_datasets(client, 'rubber')
        print(f'Rubber datasets: {urls}')

asyncio.run(test())
"
```

**Validation attendue:**
- [ ] Au moins 2 URLs cashew découvertes
- [ ] Au moins 3 URLs rubber découvertes
- [ ] URLs format: https://data.opendevelopmentcambodia.net/en/...
- [ ] Aucune exception levée

---

#### 5.2 - Test collection complète
**Command:**
```bash
python scripts/seed_collectors.py --include-odc --skip-chroma
```

**Validation attendue:**
- [ ] ODC collector exécuté sans exception
- [ ] Au moins 20 production records collectés (objectif: 50+)
- [ ] Logs montrent "Discovered X datasets for cashew"
- [ ] Logs montrent "Discovered Y datasets for rubber"
- [ ] Si échec → fallback sample data généré

---

#### 5.3 - Vérifier données en DB
**SQL Query (Supabase dashboard):**
```sql
-- Count ODC records
SELECT COUNT(*) as total_records
FROM production
WHERE source = 'ODC';

-- Check metadata
SELECT
    commodity,
    COUNT(*) as count,
    MIN(year) as min_year,
    MAX(year) as max_year
FROM production
WHERE source = 'ODC'
GROUP BY commodity;

-- Check if sample vs real data
SELECT
    metadata->>'note' as note_type,
    COUNT(*) as count
FROM production
WHERE source = 'ODC'
GROUP BY metadata->>'note';
```

**Validation attendue:**
- [ ] Total records > 30 (amélioration vs baseline)
- [ ] Données pour cashew ET rubber
- [ ] Années couvrent au moins 2015-2023
- [ ] Ratio (real data / sample data) > 1.0

---

#### 5.4 - Test cas limites

- [ ] **Test 1:** Site ODC down → Fallback sample data, pas d'exception
- [ ] **Test 2:** Dataset sans ressources → Skip dataset + log WARNING
- [ ] **Test 3:** CSV malformé → Skip resource + log ERROR + continue

---

## ⚠️ Risques Identifiés & Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Structure HTML ODC change** | Haut | Moyenne | BeautifulSoup flexible + multi-patterns + logging détaillé |
| **Datasets PDF seulement (pas CSV)** | Haut | Haute | Accepter limitation, focus sur datasets avec CSV/JSON/XLS |
| **Rate limiting ODC** | Moyen | Faible | Retry logic + sleep 2s entre requêtes + limit 5 datasets |
| **Parsing errors CSV malformé** | Moyen | Moyenne | Try/except robuste + skip fichier invalide + log warning |
| **Aucun dataset découvert** | Haut | Faible | Fallback sample data (déjà implémenté) |
| **Discovery timeout** | Moyen | Faible | Timeout 30s + retry 1 fois + fallback |
| **Régression autres collectors** | Haut | Très faible | Aucun changement MEF/WITS collectors |

**Mitigation principale:** Garder fallback sample data pour resilience maximale

---

## 🔍 Points de Validation (Checklist Finale)

### Code Quality
- [ ] Aucune erreur Python syntax
- [ ] Imports BeautifulSoup + asyncio présents
- [ ] Type hints corrects (List[str], Dict[str, Any])
- [ ] Docstrings à jour pour nouvelles méthodes
- [ ] Aucun hardcoded URL restant

### Functionality
- [ ] Discovery retourne 3-5 URLs par commodity
- [ ] BeautifulSoup remplace regex partout
- [ ] Support CSV + JSON + Excel (.xls, .xlsx)
- [ ] Fallback sample data fonctionne
- [ ] Au moins 50 production records collectés (target)

### Logging & Monitoring
- [ ] Logs INFO pour discovery process
- [ ] Logs WARNING pour échecs parsing
- [ ] Logs ERROR pour exceptions HTTP
- [ ] Metadata enrichie (fallback_reason, scraped_at, url)

### Resilience
- [ ] Retry logic implémenté (2 attempts)
- [ ] Timeout HTTP configuré (30s)
- [ ] Try/except sur parsing errors
- [ ] Graceful degradation vers sample data

### No Regression
- [ ] MEF collector fonctionne toujours
- [ ] WITS collector fonctionne toujours
- [ ] GDrive collector fonctionne toujours
- [ ] DB schema inchangé

---

## 📚 Références Techniques

### BeautifulSoup4 Documentation
- **find_all():** https://www.crummy.com/software/BeautifulSoup/bs4/doc/#find-all
- **CSS selectors:** `soup.select('a[href*=".csv"]')`
- **Regex patterns:** `soup.find_all('a', href=re.compile(r'\.csv$'))`

### Open Development Cambodia
- **Catalogue:** https://data.opendevelopmentcambodia.net/en/dataset
- **Search cashew:** https://data.opendevelopmentcambodia.net/en/dataset?q=agriculture+cashew (9 résultats)
- **Search rubber:** https://data.opendevelopmentcambodia.net/en/dataset?q=agriculture+rubber (118 résultats)

### Python Libraries (Déjà Installées)
- `beautifulsoup4==4.14.3` (requirements.txt)
- `lxml==6.0.2` (requirements.txt)
- `httpx==0.28.1` (requirements.txt)
- `pandas==2.1.0+` (requirements.txt)

---

## 📊 Estimation Détaillée

| Phase | Tâche | Complexité | Lignes Code | Temps Estimé |
|-------|-------|------------|-------------|--------------|
| 1.1 | Créer `_discover_datasets()` | Moyenne | ~60 | 20 min |
| 1.2 | Intégrer discovery dans `collect()` | Faible | ~15 | 10 min |
| 2.1 | Import BeautifulSoup + asyncio | Triviale | 2 | 1 min |
| 2.2 | Remplacer regex → bs4 | Moyenne | ~45 | 15 min |
| 3.1 | Support Excel detection | Faible | ~10 | 5 min |
| 3.2 | Créer `_parse_excel()` | Moyenne | ~25 | 15 min |
| 4.1 | Améliorer logging | Faible | ~8 | 5 min |
| 4.2 | Améliorer fallback | Faible | ~5 | 3 min |
| 5.1-5.4 | Tests | N/A | 0 | 25 min |

**Total:**
- **Complexité globale:** Moyenne
- **Fichiers modifiés:** 1 (`app/collectors/odc_collector.py`)
- **Nouvelles dépendances:** 0 (tout déjà installé)
- **Lignes code ajoutées:** ~180
- **Temps total:** **1.5-2 heures**

---

## 🚦 Prêt pour Implémentation

### Pré-requis Validés
- [x] Analyse complète (01_analysis.md ✓)
- [x] BeautifulSoup4 4.14.3 installé
- [x] lxml 6.0.2 installé
- [x] httpx 0.28.1 installé
- [x] pandas 2.1.0+ installé
- [x] Aucune nouvelle dépendance requise

### Stratégie Validée
- [x] Approche découverte dynamique définie
- [x] Fallback sample data préservé
- [x] Parsing multi-formats (CSV/JSON/XLS)
- [x] Logging & resilience améliorés
- [x] Aucun impact sur autres collectors

### En Attente
- [ ] **Validation utilisateur du plan**
- [ ] Go pour implémentation

---

**Plan créé:** 2025-12-25
**Status:** READY FOR REVIEW → Awaiting user validation
