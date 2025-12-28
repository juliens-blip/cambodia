-- Migration: Add unique constraint to prices table to prevent duplicates
-- Date: 2025-12-25
-- Purpose: Ensure that re-seeding data doesn't create duplicate price records

-- Step 1: Remove any existing duplicates before adding the constraint
-- This identifies duplicates based on the natural key: commodity_id, date, source, destination_country

WITH duplicates AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY commodity_id, date, source, COALESCE(destination_country, '')
            ORDER BY created_at DESC
        ) as rn
    FROM prices
)
DELETE FROM prices
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- Step 2: Create partial unique indexes to prevent future duplicates
-- These indexes handle NULL destination_country values correctly

-- For records WITH a destination_country
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_with_destination
ON prices(commodity_id, date, source, destination_country)
WHERE destination_country IS NOT NULL;

-- For records WITHOUT a destination_country (NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_without_destination
ON prices(commodity_id, date, source)
WHERE destination_country IS NULL;

-- Step 3: Verify the migration
-- This query should return 0 if there are no duplicates
SELECT
    commodity_id,
    date,
    source,
    COALESCE(destination_country, 'NULL') as destination,
    COUNT(*) as count
FROM prices
GROUP BY commodity_id, date, source, COALESCE(destination_country, 'NULL')
HAVING COUNT(*) > 1;

-- If the above query returns any rows, there are still duplicates that need manual review
