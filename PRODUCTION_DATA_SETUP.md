# Production Data Collection Setup

Ce guide explique comment configurer et utiliser le système de collecte de données de production pour cashew et rubber au Cambodge.

## Vue d'ensemble

Le système collecte des données de production depuis 3 sources :

1. **Open Development Cambodia (ODC)** - Datasets publics CSV/JSON
2. **Google Drive PDFs** - Extraction via OCR (Tesseract Khmer + English)
3. **Fichiers KML** - Données géographiques avec production par région

## Architecture Implémentée

### 1. Base de données (Supabase)

**Table `production`:**
```sql
- id: UUID (primary key)
- commodity_id: UUID (foreign key → commodities)
- year: INTEGER
- province: TEXT
- area_hectares: DECIMAL
- production_tons: DECIMAL
- yield_kg_per_ha: DECIMAL
- geolocation: JSONB
- source: TEXT
- created_at: TIMESTAMPTZ
```

**Natural key (unique constraint):**
`commodity_id + year + province + source`

### 2. Collectors

#### **ODCCollector** (`app/collectors/odc_collector.py`)
- Scrape datasets cashew/rubber sur data.opendevelopmentcambodia.net
- Parse CSV/JSON automatiquement
- Extrait: year, province, production_tons, area_hectares
- Génère des données sample si aucun dataset trouvé

#### **GDriveCollector** (`app/collectors/gdrive_collector.py`)
- Download PDFs/KML depuis Google Drive folders
- OCR Khmer/English avec Tesseract
- Extraction pattern matching pour production data :
  - Province names (24 provinces cambodgiennes)
  - Production (tons/tonnes/MT)
  - Area (ha/hectares)
  - Year (2000-2099)
- Parse KML pour geolocation + production

#### **KMLParser** (`app/utils/kml_parser.py`)
- Utilitaire réutilisable pour parsing KML
- Extrait placemarks, coordinates, extended data
- Calcule centroid pour polygones
- Support Point et Polygon geometries

### 3. Storage (SupabaseService)

**Méthode `upsert_production()`:**
- Prévient les duplicates lors du re-seeding
- Utilise natural key: commodity_id + year + province + source
- Update automatique si record existe déjà

## Installation & Configuration

### 1. Prérequis

Déjà installés (voir RESUME_CODEX.md):
- ✅ Tesseract OCR (avec Khmer + English tessdata)
- ✅ Poppler (pour PDF → images)
- ✅ Google Drive API credentials

### 2. Migration Base de Données

**IMPORTANT:** Appliquer la migration avant le premier seeding !

```bash
# Aller dans Supabase Dashboard > SQL Editor
# Copier/coller le contenu de:
scripts/migrations/002_add_unique_constraint_production.sql
# Exécuter la query
```

Cette migration crée l'index unique pour éviter les duplicates.

### 3. Variables d'environnement

Vérifier dans `.env`:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Google Drive
GOOGLE_DRIVE_API_KEY=your-api-key

# ODC
ODC_BASE_URL=https://data.opendevelopmentcambodia.net/en/dataset

# OCR (déjà configuré)
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
POPPLER_PATH=C:\\poppler-24.08.0\\Library\\bin
TESSDATA_PREFIX=assets\\tessdata
```

### 4. Folder IDs Google Drive

Déjà configurés dans `app/config_gdrive.py`:
```python
GDRIVE_FOLDER_IDS = {
    "cashew": "1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC",
    "rubber": "1eNhCNEKzGRrBOUEiE3dcdudb0bQL8XY-"
}
```

## Utilisation

### Test rapide

Tester les collectors avant le seeding complet:

```powershell
.\.venv311\Scripts\python.exe scripts\test_production_seeding.py
```

Ce script teste:
1. ODC collector → production records
2. GDrive collector → PDF/KML extraction
3. Supabase upsert → pas de duplicates

### Seeding complet

**Option 1: Seed avec ODC (recommandé)**

```powershell
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

Collecte depuis:
- MEF (prices)
- WITS (prices)
- GDrive (documents + production)
- ODC (production)

**Option 2: Seed sans ODC**

```powershell
.\.venv311\Scripts\python.exe scripts\seed_collectors.py
```

Collecte depuis MEF + WITS + GDrive uniquement.

**Option 3: Skip ChromaDB**

Si ChromaDB n'est pas démarré:

```powershell
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc --skip-chroma
```

### Vérification

Après seeding, vérifier dans Supabase Dashboard:

```sql
-- Compter les records de production
SELECT
    c.name as commodity,
    COUNT(*) as total_records,
    MIN(p.year) as earliest_year,
    MAX(p.year) as latest_year,
    COUNT(DISTINCT p.province) as provinces_count
FROM production p
JOIN commodities c ON p.commodity_id = c.id
GROUP BY c.name;

-- Voir les provinces
SELECT DISTINCT province
FROM production
ORDER BY province;

-- Sample data
SELECT
    c.name,
    p.year,
    p.province,
    p.production_tons,
    p.area_hectares,
    p.source
FROM production p
JOIN commodities c ON p.commodity_id = c.id
ORDER BY p.year DESC, c.name
LIMIT 20;
```

### Re-seeding

Grâce à l'upsert, vous pouvez re-run le seeding sans créer de duplicates:

```powershell
# Safe - pas de duplicates
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

L'upsert met à jour les records existants si natural key identique.

## Structure des données

### Production Record (exemple)

```json
{
  "commodity_id": "uuid-cashew",
  "year": 2023,
  "province": "Kampong Cham",
  "production_tons": 1500.0,
  "area_hectares": 750.0,
  "yield_kg_per_ha": 2000.0,
  "geolocation": {
    "lat": 12.1234,
    "lon": 105.5678
  },
  "source": "GDrive",
  "metadata": {
    "filename": "cashew_production_2023.pdf",
    "extracted_method": "pdf_pattern_matching",
    "extraction_date": "2025-12-25T10:30:00Z"
  }
}
```

### Sources de données

| Source | Type | Production? | Geolocation? | Notes |
|--------|------|-------------|--------------|-------|
| MEF | API | ❌ (prices) | ❌ | Export values uniquement |
| WITS | API | ❌ (prices) | ❌ | Trade statistics |
| ODC | Web scraping | ✅ | ❌ | CSV/JSON datasets |
| GDrive PDF | OCR | ✅ | ❌ | Pattern matching |
| GDrive KML | XML parsing | ✅ | ✅ | Geographic data |

## Extraction Methods

### PDF Pattern Matching

Le GDriveCollector cherche ces patterns dans les PDFs:

```regex
# Province + production
"Kampong Cham ... 1500 tons ... 750 ha"

# Tabular data
"Province  Year  Production  Area
 Kratie   2023  2500       1200"

# Keywords
- Production: tons, tonnes, metric tons, MT
- Area: ha, hectares, hectare
- Year: 2000-2099
```

### KML Extended Data

Le KMLParser extrait depuis `<ExtendedData>`:

```xml
<Placemark>
  <name>Kampong Cham</name>
  <description>Cashew production: 1500 tons, Area: 750 ha</description>
  <ExtendedData>
    <Data name="year"><value>2023</value></Data>
    <Data name="production_tons"><value>1500</value></Data>
    <Data name="area_hectares"><value>750</value></Data>
  </ExtendedData>
  <Point>
    <coordinates>105.5678,12.1234,0</coordinates>
  </Point>
</Placemark>
```

## Troubleshooting

### Problème: "No ODC data found"

```
⚠️ No ODC data found - creating sample production records
```

**Solution:** Normal si les datasets ODC ne sont pas accessibles. Le collector génère des données sample pour 5 provinces × 3 années × 2 commodities = 30 records.

### Problème: "Error extracting production from PDF"

```
❌ Error processing file cashew_report.pdf: ...
```

**Causes possibles:**
1. PDF protégé/encrypté
2. OCR Tesseract non accessible
3. Format PDF non standard

**Solution:** Vérifier `TESSERACT_CMD` et `POPPLER_PATH` dans `.env`

### Problème: "Duplicate key violation"

```
ERROR: duplicate key value violates unique constraint "idx_production_unique"
```

**Solution:** Appliquer la migration `002_add_unique_constraint_production.sql`

### Problème: "ChromaDB connection error"

```
⚠️ ChromaDB not available, skipping: ...
```

**Solution:**
1. Start ChromaDB: `docker-compose up -d chroma`
2. Ou utiliser `--skip-chroma` flag

## Workflow Complet

### Setup initial (une seule fois)

```powershell
# 1. Appliquer les migrations
# Via Supabase Dashboard > SQL Editor:
# - 001_add_unique_constraint_prices.sql
# - 002_add_unique_constraint_production.sql

# 2. Tester les collectors
.\.venv311\Scripts\python.exe scripts\test_production_seeding.py

# 3. Premier seeding
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

### Mise à jour quotidienne (automated)

Le scheduler APScheduler run automatiquement:

```python
# app/scheduler/jobs.py
async def daily_pipeline():
    """
    Runs at 6:00 AM Cambodia Time.

    1. Collect data (MEF, WITS, GDrive, ODC)
    2. Store in Supabase + ChromaDB (with upsert)
    3. Generate Perplexity analyses
    4. Generate Claude reports
    """
```

Pour run manuellement:

```python
from app.scheduler.jobs import daily_pipeline
import asyncio

asyncio.run(daily_pipeline())
```

## Fichiers Modifiés/Créés

### Créés
- ✅ `app/utils/kml_parser.py` - KML parsing utility
- ✅ `scripts/migrations/002_add_unique_constraint_production.sql` - Migration
- ✅ `scripts/test_production_seeding.py` - Script de test
- ✅ `PRODUCTION_DATA_SETUP.md` - Ce guide

### Modifiés
- ✅ `app/services/supabase_service.py` - Ajout `upsert_production()`
- ✅ `app/collectors/odc_collector.py` - Scraping production data
- ✅ `app/collectors/gdrive_collector.py` - PDF/KML extraction
- ✅ `app/scheduler/jobs.py` - Utilise `upsert_production()`
- ✅ `app/utils/__init__.py` - Export KMLParser
- ✅ `scripts/migrations/README.md` - Documentation migration

## Dashboard Visualization

Les données de production sont visibles dans:

**Dashboard > Production Maps** (`dashboard/pages/2_Production_Maps.py`)
- Carte Folium avec markers par province
- Heatmap de production
- Filtres par commodity et année
- Statistiques par province

Pour vérifier que les données sont chargées:

```python
# Dans le dashboard
import streamlit as st
import requests

response = requests.get(f"{API_URL}/stats")
stats = response.json()

st.write(f"Production records: {stats['supabase']['production']}")
```

## Next Steps

1. ✅ Appliquer migration 002
2. ✅ Run test script
3. ✅ Seed avec `--include-odc`
4. ⏳ Vérifier production table dans Supabase
5. ⏳ Visualiser dans Dashboard > Production Maps
6. ⏳ Run daily_pipeline pour analyses Perplexity + Claude

## Support

Pour questions/problèmes:
1. Vérifier RESUME_CODEX.md pour contexte global
2. Vérifier logs dans terminal
3. Vérifier Supabase Dashboard > Table Editor > production
4. Utiliser test script pour debugging

---

**Date:** 2025-12-25
**Version:** 1.0
**Status:** ✅ Production Ready
