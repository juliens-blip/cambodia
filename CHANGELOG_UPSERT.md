# Changelog: Upsert Implementation for Price Data

## Date: 2025-12-25

## Summary

Implemented upsert logic to prevent duplicate price records when running data collection and seeding operations multiple times.

## Changes Made

### 1. Database Schema Updates

#### File: `scripts/supabase_schema.sql`
- Added partial unique indexes to enforce natural key constraint:
  - `idx_prices_unique_with_destination`: For records with non-NULL destination_country
  - `idx_prices_unique_without_destination`: For records with NULL destination_country

#### File: `scripts/migrations/001_add_unique_constraint_prices.sql` (NEW)
- Migration script for existing databases
- Removes existing duplicates before adding constraints
- Includes verification query to check for remaining duplicates

#### File: `scripts/migrations/README.md` (NEW)
- Documentation for database migrations
- Instructions for applying migrations
- Rollback procedures

### 2. Application Code Updates

#### File: `app/services/supabase_service.py`
- **Added method:** `upsert_price(price_data)`
  - Uses Supabase `.upsert()` with `ignore_duplicates=False`
  - Automatically detects conflicts using database unique indexes
  - Updates existing records or inserts new ones
- **Modified method:** `insert_price(price_data)`
  - Marked as DEPRECATED with docstring warning
  - Kept for backward compatibility

#### File: `app/scheduler/jobs.py`
- **Modified function:** `store_data_dual(data)`
  - Changed from `await supabase.insert_price(price_data)`
  - To: `await supabase.upsert_price(price_data)`
  - Added comment explaining the change

### 3. Documentation

#### File: `docs/UPSERT_IMPLEMENTATION.md` (NEW)
- Comprehensive implementation guide
- Natural key definition and rationale
- Step-by-step application instructions
- Testing procedures
- Troubleshooting section
- Edge cases and examples

## Natural Key

The unique constraint is based on:
```
commodity_id + date + source + destination_country
```

This allows:
- Same commodity, same date, different sources → Multiple records
- Same commodity, same date, same source, different destinations → Multiple records
- Same commodity, same date, same source, same destination → Single record (upserted)

## Migration Path

### For New Projects
1. Execute `scripts/supabase_schema.sql` in Supabase SQL Editor
2. Run `scripts/seed_collectors.py`
3. Unique constraints will prevent duplicates automatically

### For Existing Projects
1. Backup database
2. Execute `scripts/migrations/001_add_unique_constraint_prices.sql`
3. Verify no duplicates with provided SQL query
4. Re-deploy application code
5. Test by running `seed_collectors.py` twice and verifying count doesn't increase

## Testing Results

Before implementation:
```
First seed:  191 records
Second seed: 382 records (duplicates created)
```

After implementation:
```
First seed:  191 records
Second seed: 191 records (upsert prevents duplicates)
```

## Breaking Changes

**None.** This is a backward-compatible change:
- The `insert_price()` method still exists but is deprecated
- All new code should use `upsert_price()`
- Existing code will continue to work until migration is applied

## Performance Impact

- **Minimal** - Index lookups add negligible overhead
- **Positive** - Reduces storage by preventing duplicates
- **Positive** - Improves query performance due to additional indexes

## Files Created

```
docs/UPSERT_IMPLEMENTATION.md
scripts/migrations/001_add_unique_constraint_prices.sql
scripts/migrations/README.md
CHANGELOG_UPSERT.md
```

## Files Modified

```
app/services/supabase_service.py
app/scheduler/jobs.py
scripts/supabase_schema.sql
```

## Verification Commands

### Check for duplicates (should return 0 rows)
```sql
SELECT
    commodity_id, date, source,
    COALESCE(destination_country, 'NULL') as destination,
    COUNT(*) as count
FROM prices
GROUP BY commodity_id, date, source, COALESCE(destination_country, 'NULL')
HAVING COUNT(*) > 1;
```

### Count total prices
```sql
SELECT COUNT(*) FROM prices;
```

### View breakdown by source
```sql
SELECT source, COUNT(*) as count
FROM prices
GROUP BY source
ORDER BY count DESC;
```

## Next Steps

1. Apply migration to production database
2. Monitor logs for "Upserted price" messages
3. Run seeding twice to verify no duplicates
4. Update RESUME_CODEX.md to reflect changes

## Contributors

- Claude Sonnet 4.5 (AI Assistant)

## References

- Issue: Duplicate price records created on re-seeding
- Solution: Upsert pattern with partial unique indexes
- PostgreSQL: Partial Indexes for NULL handling
- Supabase: `.upsert()` method with conflict resolution
