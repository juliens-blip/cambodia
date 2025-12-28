# Database Migrations

This directory contains SQL migrations for the Cambodia Agri Analytics project.

## How to Apply Migrations

### Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Open the migration file you want to apply
4. Copy the SQL content
5. Paste it into the SQL Editor
6. Click **Run** to execute the migration

### Using Supabase CLI

```bash
supabase db push
```

## Available Migrations

### 001_add_unique_constraint_prices.sql

**Purpose:** Prevents duplicate price records when re-seeding data from collectors.

**What it does:**
1. Removes existing duplicates based on natural key: `commodity_id + date + source + destination_country`
2. Creates partial unique indexes to prevent future duplicates
3. Handles NULL `destination_country` values correctly

**Natural Key Definition:**
- `commodity_id`: UUID of the commodity (cashew or rubber)
- `date`: Date of the price record
- `source`: Data source (MEF, WITS, GDrive, ODC)
- `destination_country`: Destination country (can be NULL)

**When to apply:**
- After initial schema setup if you're experiencing duplicate issues
- Before running `seed_collectors.py` multiple times

**Rollback:**
If you need to remove the unique constraints:
```sql
DROP INDEX IF EXISTS idx_prices_unique_with_destination;
DROP INDEX IF EXISTS idx_prices_unique_without_destination;
```

### 002_add_unique_constraint_production.sql

**Purpose:** Prevents duplicate production records when re-seeding data from collectors.

**What it does:**
1. Creates unique index on natural key: `commodity_id + year + province + source`
2. Supports the `upsert_production()` method in SupabaseService

**Natural Key Definition:**
- `commodity_id`: UUID of the commodity (cashew or rubber)
- `year`: Production year
- `province`: Cambodian province name
- `source`: Data source (ODC, GDrive)

**When to apply:**
- Before running production data collection
- Before seeding production data with `--include-odc` flag

**Rollback:**
If you need to remove the unique constraint:
```sql
DROP INDEX IF EXISTS idx_production_unique;
```

## Migration Status

| Migration | Applied | Date | Notes |
|-----------|---------|------|-------|
| 001_add_unique_constraint_prices.sql | ⏳ Pending | - | Prevents duplicate price records |
| 002_add_unique_constraint_production.sql | ⏳ Pending | 2025-12-25 | Prevents duplicate production records |

## Best Practices

1. Always backup your database before applying migrations
2. Test migrations on a development/staging environment first
3. Review the verification query output after applying migrations
4. Keep this README updated with migration status
