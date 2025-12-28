# Architecture - Production Data Collection System

Documentation technique de l'architecture du système de collecte de données de production.

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
├─────────────────────────────────────────────────────────────────┤
│  ODC Datasets      │  Google Drive PDFs  │  Google Drive KML   │
│  (CSV/JSON)        │  (Khmer/English)    │  (Geographic)       │
└──────┬─────────────┴──────────┬───────────┴─────────┬───────────┘
       │                        │                     │
       ▼                        ▼                     ▼
┌──────────────┐    ┌────────────────────┐    ┌─────────────┐
│ ODCCollector │    │ GDriveCollector    │    │ KMLParser   │
│              │    │                    │    │ (utility)   │
│ - Scrape web │    │ - Download files   │    │             │
│ - Parse CSV  │    │ - OCR Tesseract    │    │ - Parse XML │
│ - Parse JSON │    │ - Pattern matching │    │ - Extract   │
│ - Sample gen │    │ - Use KMLParser    │    │   data      │
└──────┬───────┘    └────────┬───────────┘    └──────┬──────┘
       │                     │                       │
       └─────────────────────┼───────────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │  BaseCollector.run() │
                  │  - Validate records  │
                  │  - Error handling    │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ store_data_dual()    │
                  │ (scheduler/jobs.py)  │
                  └──────────┬───────────┘
                             ▼
              ┌──────────────┴───────────────┐
              ▼                              ▼
    ┌─────────────────┐           ┌─────────────────┐
    │ Supabase        │           │ ChromaDB        │
    │ upsert_         │           │ store_          │
    │ production()    │           │ production_     │
    │                 │           │ context()       │
    │ Natural key:    │           │                 │
    │ commodity_id +  │           │ Semantic search │
    │ year + province │           │ + embeddings    │
    │ + source        │           │                 │
    └─────────────────┘           └─────────────────┘
```

## Components

### 1. Data Sources

#### Open Development Cambodia (ODC)
- **URL:** https://data.opendevelopmentcambodia.net/en/dataset
- **Format:** CSV, JSON
- **Data types:** Production statistics, agricultural data
- **Access:** Public HTTP scraping

**Datasets searched:**
```python
{
    "cashew": [
        "/cashew-production-statistics",
        "/agricultural-production-cashew"
    ],
    "rubber": [
        "/rubber-production-statistics",
        "/agricultural-production-rubber"
    ]
}
```

#### Google Drive PDFs
- **Folders:**
  - Cashew: `1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC`
  - Rubber: `1eNhCNEKzGRrBOUEiE3dcdudb0bQL8XY-`
- **Format:** PDF (Khmer + English)
- **Processing:** OCR via Tesseract
- **Extraction:** Pattern matching

#### Google Drive KML
- **Format:** KML (Keyhole Markup Language)
- **Data:** Placemarks with geographic coordinates + production metadata
- **Processing:** XML parsing via ElementTree

### 2. Collectors

#### ODCCollector
**Location:** `app/collectors/odc_collector.py`

**Workflow:**
```python
1. Fetch dataset page (HTML)
2. Extract resource URLs (CSV/JSON)
3. Download resources
4. Parse based on format:
   - CSV → DictReader
   - JSON → json.loads()
5. Extract fields:
   - year, province, production_tons, area_hectares
6. Fallback: Generate sample data if no real data found
```

**Sample data generation:**
```python
provinces = ["Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri"]
years = [2021, 2022, 2023]
commodities = ["cashew", "rubber"]

# Total: 5 × 3 × 2 = 30 records
```

**Field mapping (flexible):**
- Year: `year`, `Year`, `YEAR`, `yr`
- Province: `province`, `Province`, `PROVINCE`, `region`
- Production: `production_tons`, `production`, `Production`, `tons`
- Area: `area_hectares`, `area`, `Area`, `hectares`

#### GDriveCollector
**Location:** `app/collectors/gdrive_collector.py`

**PDF Processing:**
```python
1. Download PDF via Drive API
2. Try text extraction (PyPDF)
3. If text < 50 chars → OCR:
   - Convert PDF to images (pdf2image + Poppler)
   - OCR each image (Tesseract khm+eng)
4. Call _extract_production_from_text()
```

**Pattern Matching:**
```python
# Pattern 1: Province + nearby numbers
Context window: ±200-500 chars around province name

Regex patterns:
- Production: r'(\d+[\d,]*\.?\d*)\s*(?:tons|tonnes|metric tons|MT)'
- Area: r'(\d+[\d,]*\.?\d*)\s*(?:ha|hectares|hectare)'
- Year: r'20[0-9]{2}'

# Pattern 2: Tabular data
"Province  Year  Production  Area"
r'([A-Za-z\s]+)\s+(20[0-9]{2})\s+(\d+...)\s+(\d+...)'
```

**KML Processing:**
```python
1. Download KML via Drive API
2. Call _extract_kml_coordinates() → geolocation
3. Call _extract_production_from_kml() → production data
4. Use KMLParser for parsing
```

**Provinces supported (24):**
```
Kampong Cham, Kampong Thom, Kratie, Mondulkiri, Ratanakiri,
Stung Treng, Preah Vihear, Kampong Speu, Pursat, Battambang,
Banteay Meanchey, Oddar Meanchey, Pailin, Siem Reap, Kampot,
Kep, Koh Kong, Preah Sihanouk, Takeo, Kandal, Prey Veng,
Svay Rieng, Tbong Khmum, Phnom Penh
```

#### KMLParser
**Location:** `app/utils/kml_parser.py`

**Methods:**
- `parse()` - Full KML parsing
- `extract_production_data()` - Production-specific extraction
- `_extract_placemarks()` - Placemark parsing
- `_extract_all_coordinates()` - Coordinate extraction
- `_extract_extended_data()` - ExtendedData parsing
- `_calculate_centroid()` - Polygon centroid calculation

**KML Structure:**
```xml
<Placemark>
  <name>Kampong Cham</name>
  <description>Production: 1500 tons, Area: 750 ha</description>
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

**Geometry support:**
- Point → Single lat/lon
- Polygon → List of coordinates + centroid

### 3. Storage Layer

#### SupabaseService
**Location:** `app/services/supabase_service.py`

**Method: `upsert_production()`**
```python
Natural key: (commodity_id, year, province, source)

Behavior:
- If record exists → UPDATE
- If record not exists → INSERT
- No duplicates created

Database constraint required:
CREATE UNIQUE INDEX idx_production_unique
ON production(commodity_id, year, province, source);
```

**Upsert logic:**
```python
result = self.client.table("production").upsert(
    production_data,
    ignore_duplicates=False  # Update instead of ignore
).execute()
```

#### ChromaDBService
**Location:** `app/services/chromadb_service.py`

**Method: `store_production_context()`**
```python
Collection: production_data

Context format:
"{province}: {production_tons} tons in {year}"

Metadata:
- commodity
- year
- province
- source
- production_tons
- area_hectares
```

### 4. Pipeline Integration

#### store_data_dual()
**Location:** `app/scheduler/jobs.py`

**Production record detection:**
```python
if "production_tons" in record or "area_hectares" in record:
    # Build production data dict
    prod_data = {
        "commodity_id": commodity_id,
        "year": record.get("year", datetime.now().year),
        "province": record.get("province", "Unknown"),
        "area_hectares": record.get("area_hectares"),
        "production_tons": record.get("production_tons"),
        "yield_kg_per_ha": record.get("yield_kg_per_ha"),
        "geolocation": record.get("geolocation"),
        "source": record["source"]
    }

    # Upsert to Supabase
    await supabase.upsert_production(prod_data)

    # Store in ChromaDB
    context = f"{province}: {production_tons} tons"
    await chromadb.store_production_context(...)
```

#### daily_pipeline()
**Location:** `app/scheduler/jobs.py`

**Workflow (automatic):**
```python
1. run_collectors() → MEF, WITS, ODC, GDrive
2. store_data_dual() → Supabase + ChromaDB
3. Perplexity analyses → research_daily_prices()
4. Claude reports → generate_daily_report()
```

## Data Flow

### Example: ODC Sample Data

**Input:** No ODC datasets found

**ODCCollector generates:**
```python
{
    "commodity": "cashew",
    "year": 2023,
    "province": "Kampong Cham",
    "production_tons": 3245,  # hash-based
    "area_hectares": 1678,     # hash-based
    "source": "ODC",
    "metadata": {
        "note": "Sample data - no real ODC dataset found",
        "scraped_at": "2025-12-25T10:30:00Z"
    }
}
```

**store_data_dual():**
```python
prod_data = {
    "commodity_id": "uuid-cashew",
    "year": 2023,
    "province": "Kampong Cham",
    "production_tons": 3245.0,
    "area_hectares": 1678.0,
    "source": "ODC"
}

# Supabase upsert
await supabase.upsert_production(prod_data)

# ChromaDB store
await chromadb.store_production_context(
    commodity="cashew",
    year=2023,
    province="Kampong Cham",
    context="Kampong Cham: 3245.0 tons",
    metadata={"production_tons": 3245.0, "area_hectares": 1678.0}
)
```

**Result in Supabase:**
```sql
id              | uuid-xxx
commodity_id    | uuid-cashew
year            | 2023
province        | Kampong Cham
production_tons | 3245.00
area_hectares   | 1678.00
source          | ODC
created_at      | 2025-12-25 10:30:00
```

### Example: GDrive PDF Extraction

**Input:** PDF "cashew_report_2023.pdf" contains:
```
Province: Kampong Thom
Production in 2023: 1,500 metric tons
Cultivated area: 850 hectares
```

**GDriveCollector extracts:**
```python
{
    "commodity": "cashew",
    "year": 2023,
    "province": "Kampong Thom",
    "production_tons": 1500.0,
    "area_hectares": 850.0,
    "source": "GDrive",
    "metadata": {
        "filename": "cashew_report_2023.pdf",
        "extracted_method": "pdf_pattern_matching",
        "extraction_date": "2025-12-25T10:35:00Z"
    }
}
```

**Pattern matching steps:**
1. Find "Kampong Thom" in text
2. Extract context window: 200 chars before → 500 chars after
3. Regex match: `1,500 metric tons` → 1500.0
4. Regex match: `850 hectares` → 850.0
5. Regex match: `2023` → 2023

### Example: KML with Geolocation

**Input:** KML file "cashew_locations.kml"
```xml
<Placemark>
  <name>Ratanakiri</name>
  <description>Cashew: 2500 tons, Area: 1200 ha</description>
  <ExtendedData>
    <Data name="year"><value>2023</value></Data>
  </ExtendedData>
  <Point>
    <coordinates>106.9867,13.7373,0</coordinates>
  </Point>
</Placemark>
```

**KMLParser extracts:**
```python
{
    "commodity": "cashew",
    "year": 2023,
    "province": "Ratanakiri",
    "production_tons": 2500.0,
    "area_hectares": 1200.0,
    "geolocation": {
        "lat": 13.7373,
        "lon": 106.9867
    },
    "source": "GDrive",
    "metadata": {
        "extracted_method": "kml_parsing",
        "placemark_name": "Ratanakiri"
    }
}
```

## Database Schema

### production table

```sql
CREATE TABLE production (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commodity_id UUID REFERENCES commodities(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 1900 AND year <= 2100),
    province TEXT NOT NULL,
    area_hectares DECIMAL(12,2) CHECK (area_hectares >= 0),
    production_tons DECIMAL(12,2) CHECK (production_tons >= 0),
    yield_kg_per_ha DECIMAL(10,2) CHECK (yield_kg_per_ha >= 0),
    geolocation JSONB,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_production_year ON production(year DESC);
CREATE INDEX idx_production_province ON production(province);
CREATE INDEX idx_production_commodity ON production(commodity_id);

-- Unique constraint (upsert support)
CREATE UNIQUE INDEX idx_production_unique
ON production(commodity_id, year, province, source);
```

**Natural key:** `(commodity_id, year, province, source)`

**Example:**
- Record 1: (uuid-cashew, 2023, "Kampong Cham", "ODC")
- Record 2: (uuid-cashew, 2023, "Kampong Cham", "GDrive") ← Different source, allowed
- Record 3: (uuid-cashew, 2023, "Kampong Cham", "ODC") ← UPDATE Record 1

## Error Handling

### Per-file error handling (GDrive)
```python
try:
    content = await self._download_file(client, file["id"])
    text = await self._extract_text_from_pdf(content)
    # ...
except Exception as exc:
    logger.error("Error processing file %s: %s", file.get("name"), exc)
    continue  # Don't abort, process next file
```

### Per-collector error handling
```python
results = await asyncio.gather(
    mef.run(),
    wits.run(),
    odc.run(),
    gdrive.run(),
    return_exceptions=True  # Continue even if one fails
)

for collector, result in zip(collectors, results):
    if isinstance(result, Exception):
        logger.warning("Collector %s failed: %s", collector.source_name, result)
        data[key] = []  # Empty data, continue
```

### Validation layer
```python
# BaseCollector.run()
validated_data = []
for record in raw_data:
    if await self.validate(record):
        validated_data.append(record)
    else:
        logger.warning(f"Invalid record: {record}")
```

## Testing

### Test script
**Location:** `scripts/test_production_seeding.py`

**Tests:**
1. ODC collector → returns 30+ records
2. GDrive collector → returns documents + production
3. Supabase upsert → same ID on duplicate

### Manual testing

```sql
-- Check for duplicates
SELECT commodity_id, year, province, source, COUNT(*)
FROM production
GROUP BY commodity_id, year, province, source
HAVING COUNT(*) > 1;

-- Should return 0 rows if upsert working correctly
```

## Performance Considerations

### ODC scraping
- Timeout: 30s per request
- Max 5 resources per dataset
- Async HTTP client (httpx)

### GDrive downloads
- Timeout: 60s per file
- Pagination: 1000 files per page
- OCR: Max 5 pages per PDF
- DPI: 300 for OCR quality

### ChromaDB
- Optional (use `--skip-chroma` if unavailable)
- Async operations
- Metadata cleaning (no None values)

## Configuration

### Environment variables
```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# Google Drive
GOOGLE_DRIVE_API_KEY=xxx

# OCR
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
POPPLER_PATH=C:\\poppler-24.08.0\\Library\\bin
TESSDATA_PREFIX=assets\\tessdata

# ODC
ODC_BASE_URL=https://data.opendevelopmentcambodia.net/en/dataset
```

### Folder configuration
**Location:** `app/config_gdrive.py`

```python
GDRIVE_FOLDER_IDS = {
    "cashew": "1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC",
    "rubber": "1eNhCNEKzGRrBOUiE3dcdudb0bQL8XY-"
}
```

## Deployment

### Initial setup
1. Apply migrations (001 + 002)
2. Configure .env
3. Run test script
4. Seed with `--include-odc`

### Daily operation
- Scheduler runs `daily_pipeline()` at 6:00 AM Cambodia Time
- Auto-collects from all sources
- Auto-upserts (no duplicates)
- Generates analyses + reports

### Re-seeding safe
```bash
# Can run multiple times without duplicates
python scripts/seed_collectors.py --include-odc
```

## Monitoring

### Log levels
- INFO: Successful operations
- WARNING: Non-critical issues (fallback to sample data, validation failures)
- ERROR: Failures (download errors, parsing errors)

### Key metrics
```python
stats = await supabase.get_database_stats()

print(f"Production records: {stats['production']}")
print(f"Commodities: {stats['commodities']}")
```

## Future Enhancements

### Possible improvements
1. Real-time ODC dataset monitoring (webhook/polling)
2. ML-based province name extraction (for misspellings)
3. Yield calculation from production/area
4. Historical trend analysis
5. Geolocation enrichment (reverse geocoding)
6. Multi-language support (Khmer OCR improvement)

---

**Version:** 1.0
**Date:** 2025-12-25
**Maintainer:** Claude Code
