# Implementation Guide: Upsert Logic for Price Data

## Problem Statement

The Cambodia Agri Analytics project was experiencing duplicate price records when running the seeding script (`seed_collectors.py`) multiple times. Each execution would create new duplicate entries in the `prices` table, even though the data was identical.

## Solution Overview

We implemented an **upsert** (update-or-insert) pattern using Supabase's `.upsert()` method combined with unique database constraints. This ensures that:

1. New price records are inserted if they don't exist
2. Existing price records are updated if they already exist (based on natural key)
3. No duplicates are created when re-seeding data

## Natural Key Definition

The natural key for price records consists of:

```
commodity_id + date + source + destination_country
```

**Rationale:**
- **commodity_id**: Identifies whether it's cashew or rubber
- **date**: The date of the price record
- **source**: Data source (MEF, WITS, GDrive, ODC)
- **destination_country**: Export destination (can be NULL for domestic prices)

This combination uniquely identifies a price record because:
- The same commodity can have different prices on the same date from different sources
- The same commodity can have different prices to different destinations
- MEF and WITS may both provide export data for the same commodity on the same date

## Implementation Details

### 1. Database Schema Changes

**File:** `scripts/supabase_schema.sql` and `scripts/migrations/001_add_unique_constraint_prices.sql`

We added two partial unique indexes to handle NULL values correctly:

```sql
-- For records WITH a destination_country
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_with_destination
ON prices(commodity_id, date, source, destination_country)
WHERE destination_country IS NOT NULL;

-- For records WITHOUT a destination_country (NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_without_destination
ON prices(commodity_id, date, source)
WHERE destination_country IS NULL;
```

**Why partial indexes?**
PostgreSQL treats NULL as distinct in unique constraints. By using partial indexes, we ensure that:
- Records with NULL destination_country are compared only against other NULLs
- Records with non-NULL destination_country are compared with their specific value

### 2. Supabase Service Changes

**File:** `app/services/supabase_service.py`

Created new method `upsert_price()`:

```python
async def upsert_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert price record (insert or update if exists).

    Uses Supabase .upsert() with partial unique indexes.
    """
    result = self.client.table("prices").upsert(
        price_data,
        ignore_duplicates=False
    ).execute()

    return result.data[0] if result.data else None
```

The `ignore_duplicates=False` parameter ensures that existing records are **updated** rather than ignored.

### 3. Data Pipeline Changes

**File:** `app/scheduler/jobs.py`

Modified `store_data_dual()` function to use `upsert_price()` instead of `insert_price()`:

```python
# Before:
await supabase.insert_price(price_data)

# After:
await supabase.upsert_price(price_data)
```

## How to Apply

### For New Projects

If you're setting up a fresh Supabase database:

1. Run the updated schema:
   ```bash
   # In Supabase Dashboard > SQL Editor
   # Execute: scripts/supabase_schema.sql
   ```

2. The unique constraints will be created automatically

### For Existing Projects

If you already have data in your `prices` table:

1. **Backup your database** (important!)

2. Apply the migration to remove duplicates and add constraints:
   ```bash
   # In Supabase Dashboard > SQL Editor
   # Execute: scripts/migrations/001_add_unique_constraint_prices.sql
   ```

3. Verify no duplicates remain:
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
   This should return 0 rows.

## Testing

### Test Case 1: Initial Seed
```bash
python scripts/seed_collectors.py
```

Check the count:
```sql
SELECT COUNT(*) FROM prices;
-- Note the count (e.g., 191)
```

### Test Case 2: Re-seed (Should Not Create Duplicates)
```bash
python scripts/seed_collectors.py
```

Check the count again:
```sql
SELECT COUNT(*) FROM prices;
-- Should be the same count (e.g., 191)
```

### Test Case 3: Verify Upsert Updates
Check the logs - you should see "Upserted price" messages instead of "Inserted price":

```
INFO - Upserted price: <uuid> on 2024-01-01 from MEF (no destination)
INFO - Upserted price: <uuid> on 2024-01-01 from WITS to World
```

## Data Preservation

The upsert logic **preserves existing data** by updating records when conflicts occur. This means:

- If you re-seed with identical data, records are updated but values remain the same
- If you re-seed with modified data (e.g., corrected prices), the new values will replace the old ones
- The `created_at` timestamp is preserved (only Supabase managed fields are updated)

## Edge Cases Handled

### NULL Destination Country
- MEF data typically has `destination_country = NULL`
- WITS data has `destination_country = "World"` or specific countries
- The partial indexes ensure these are treated as distinct natural keys

### Same Commodity, Same Date, Different Sources
```
Record 1: cashew, 2024-01-01, MEF, NULL        -> Unique
Record 2: cashew, 2024-01-01, WITS, "World"    -> Unique (different source + destination)
Record 3: cashew, 2024-01-01, WITS, "USA"      -> Unique (different destination)
```

All three are valid and will coexist in the database.

### Metadata Changes
The `metadata` JSONB field is updated on upsert. If you collect additional metadata later, it will replace the previous metadata.

## Rollback Plan

If you need to remove the unique constraints:

```sql
DROP INDEX IF EXISTS idx_prices_unique_with_destination;
DROP INDEX IF EXISTS idx_prices_unique_without_destination;
```

Then revert the code changes:
1. In `app/scheduler/jobs.py`: Change `upsert_price()` back to `insert_price()`
2. Restart your API

**Warning:** This will allow duplicates to be created again.

## Performance Considerations

- **Insert Performance**: Slightly slower due to index lookups, but negligible for typical volumes
- **Query Performance**: Improved due to additional indexes on natural key columns
- **Storage**: Minimal overhead from two partial indexes

## Monitoring

To monitor the effectiveness of the upsert logic:

```sql
-- Check for any remaining duplicates (should be 0)
SELECT
    commodity_id,
    date,
    source,
    COALESCE(destination_country, 'NULL') as destination,
    COUNT(*) as count
FROM prices
GROUP BY commodity_id, date, source, COALESCE(destination_country, 'NULL')
HAVING COUNT(*) > 1;

-- Check total price records
SELECT COUNT(*) FROM prices;

-- Check breakdown by source
SELECT source, COUNT(*) as count
FROM prices
GROUP BY source
ORDER BY count DESC;
```

## Troubleshooting

### Issue: "Duplicate key value violates unique constraint"

**Cause:** Two records with identical natural key are being inserted simultaneously.

**Solution:** This is expected behavior. The second insert will update the first. If you see this error, it means the unique constraint is working correctly.

### Issue: "Function upsert_price not found"

**Cause:** Code changes not deployed or service not restarted.

**Solution:**
```bash
# Restart the API
uvicorn app.main:app --reload
```

### Issue: Migration fails with "constraint already exists"

**Cause:** Unique indexes already created.

**Solution:** This is safe to ignore. The `IF NOT EXISTS` clause prevents errors.

## Future Enhancements

Potential improvements for consideration:

1. **Audit Trail**: Add `updated_at` trigger to track when records are modified via upsert
2. **Conflict Resolution**: Add logic to compare and merge metadata on conflicts
3. **Soft Deletes**: Instead of deleting duplicates, mark them as superseded
4. **Version History**: Keep historical versions of updated price records

## References

- [Supabase Upsert Documentation](https://supabase.com/docs/reference/javascript/upsert)
- [PostgreSQL Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- [Handling NULL in Unique Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS)
