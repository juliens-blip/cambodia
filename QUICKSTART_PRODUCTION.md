# Quick Start - Production Data Collection

Guide rapide pour activer la collecte de données de production.

## Étape 1: Appliquer les migrations (REQUIS)

Aller sur Supabase Dashboard → SQL Editor et exécuter:

### Migration 1: Prices (si pas déjà fait)
```sql
-- Copier/coller depuis: scripts/migrations/001_add_unique_constraint_prices.sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_with_destination
ON prices(commodity_id, date, source, destination_country)
WHERE destination_country IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_without_destination
ON prices(commodity_id, date, source)
WHERE destination_country IS NULL;
```

### Migration 2: Production (NOUVEAU)
```sql
-- Copier/coller depuis: scripts/migrations/002_add_unique_constraint_production.sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_production_unique
ON production(commodity_id, year, province, source);
```

## Étape 2: Tester le système (OPTIONNEL)

```powershell
# Tester ODC, GDrive collectors + Supabase upsert
.\.venv311\Scripts\python.exe scripts\test_production_seeding.py
```

Résultat attendu:
```
✅ ODC collector returned 30 records
✅ GDrive collector returned X records
✅ Supabase Upsert: PASS
```

## Étape 3: Seed production data

```powershell
# Collecte depuis MEF + WITS + GDrive + ODC
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

Résultat attendu:
```
INFO: Collected X raw records from ODC
INFO: Collected X raw records from GDrive
INFO: Upserted production: Kampong Cham 2023 from ODC
INFO: ✅ Data stored successfully
```

## Étape 4: Vérifier les données

Sur Supabase Dashboard → Table Editor → production:

```sql
-- Compter les records
SELECT COUNT(*) FROM production;

-- Par commodity
SELECT
    c.name,
    COUNT(*) as records,
    MIN(p.year) as first_year,
    MAX(p.year) as last_year
FROM production p
JOIN commodities c ON p.commodity_id = c.id
GROUP BY c.name;

-- Provinces
SELECT DISTINCT province FROM production ORDER BY province;
```

## Étape 5: Visualiser dans Dashboard

```powershell
# Si pas déjà lancé
.\.venv311\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8501
```

Aller sur: http://localhost:8501
→ Page "Production Maps"

## Sources de données production

| Source | Type | Records attendus | Notes |
|--------|------|------------------|-------|
| ODC | CSV/JSON scraping | 30+ | Sample data si datasets non accessibles |
| GDrive PDF | OCR + pattern | Variable | Dépend des PDFs dans folders |
| GDrive KML | XML parsing | Variable | Si fichiers KML présents |

## Troubleshooting rapide

### "No ODC data found"
→ Normal, le collector génère 30 sample records (5 provinces × 3 ans × 2 commodities)

### "Duplicate key violation"
→ Appliquer migration 002_add_unique_constraint_production.sql

### "Error extracting production from PDF"
→ Vérifier TESSERACT_CMD et POPPLER_PATH dans .env

### ChromaDB error
→ Utiliser flag `--skip-chroma` ou lancer `docker-compose up -d chroma`

## Re-seeding safe

Grâce à upsert, vous pouvez re-run sans créer duplicates:

```powershell
# Safe - pas de duplicates
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc
```

## Structure production record

```json
{
  "commodity": "cashew|rubber",
  "year": 2023,
  "province": "Kampong Cham",
  "production_tons": 1500.0,
  "area_hectares": 750.0,
  "geolocation": {"lat": 12.1234, "lon": 105.5678},
  "source": "ODC|GDrive"
}
```

## Documentation complète

Voir: `PRODUCTION_DATA_SETUP.md` pour guide détaillé

## Support

1. RESUME_CODEX.md - Contexte global projet
2. MEMOIRE_CLAUDE.md - Logs sessions
3. PRODUCTION_DATA_SETUP.md - Guide complet production
4. scripts/migrations/README.md - Documentation migrations

---

**Version:** 1.0
**Date:** 2025-12-25
**Status:** ✅ Ready to use
