# Quick Start: Upsert Implementation

## TL;DR

The project now prevents duplicate price records when re-running data collection. Use this guide to apply the changes.

## 60-Second Setup

### For NEW Databases

```bash
# 1. Apply the updated schema in Supabase Dashboard > SQL Editor
# Execute: scripts/supabase_schema.sql

# 2. Run seeding (can now run multiple times safely)
python scripts/seed_collectors.py

# 3. Verify no duplicates
# Run in Supabase SQL Editor:
SELECT COUNT(*) FROM prices;
```

### For EXISTING Databases

```bash
# 1. BACKUP YOUR DATABASE FIRST!

# 2. Apply migration in Supabase Dashboard > SQL Editor
# Execute: scripts/migrations/001_add_unique_constraint_prices.sql

# 3. Re-deploy your application (if running)
# The code changes are already in place

# 4. Test by running seed twice
python scripts/seed_collectors.py
# Note the count
python scripts/seed_collectors.py
# Count should be the same
```

## What Changed?

### Before
```python
# Every re-seed created duplicates
await supabase.insert_price(price_data)
```

### After
```python
# Now uses upsert - no duplicates
await supabase.upsert_price(price_data)
```

## Natural Key

Records are uniquely identified by:
```
commodity_id + date + source + destination_country
```

**Examples:**
- ✅ `cashew, 2024-01-01, MEF, NULL` (unique)
- ✅ `cashew, 2024-01-01, WITS, World` (unique - different source)
- ✅ `cashew, 2024-01-01, WITS, USA` (unique - different destination)
- ❌ `cashew, 2024-01-01, MEF, NULL` (duplicate of first - will upsert)

## Verification

### Check for duplicates (should return 0 rows)
```sql
SELECT
    commodity_id,
    date,
    source,
    COALESCE(destination_country, 'NULL') as destination,
    COUNT(*) as count
FROM prices
GROUP BY commodity_id, date, source, COALESCE(destination_country, 'NULL')
HAVING COUNT(*) > 1;
```

### View logs
Look for "Upserted price" messages:
```
INFO - Upserted price: uuid-here on 2024-01-01 from MEF (no destination)
INFO - Upserted price: uuid-here on 2024-01-01 from WITS to World
```

## Files Changed

```
✅ app/services/supabase_service.py      (new upsert_price method)
✅ app/scheduler/jobs.py                 (uses upsert instead of insert)
✅ scripts/supabase_schema.sql           (unique indexes)
✅ scripts/migrations/*.sql              (migration for existing DBs)
```

## Rollback

If needed, remove constraints:
```sql
DROP INDEX IF EXISTS idx_prices_unique_with_destination;
DROP INDEX IF EXISTS idx_prices_unique_without_destination;
```

Then change code back to `insert_price()`.

## Need More Details?

See: `docs/UPSERT_IMPLEMENTATION.md` for comprehensive documentation.

## Support

If you encounter issues:
1. Check that migration was applied successfully
2. Verify unique indexes exist:
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'prices';
   ```
3. Review troubleshooting section in `docs/UPSERT_IMPLEMENTATION.md`

---

**Last Updated:** 2025-12-25
**Status:** ✅ Ready for production
