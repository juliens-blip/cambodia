-- Migration: Add unique constraint to production table
-- Date: 2025-12-25
-- Purpose: Prevent duplicate production records when re-seeding data

-- Add unique constraint on natural key: commodity_id + year + province + source
-- This ensures that re-running seed_collectors.py will use UPSERT instead of INSERT
CREATE UNIQUE INDEX IF NOT EXISTS idx_production_unique
ON production(commodity_id, year, province, source);

-- Note: This index supports the upsert_production() method in SupabaseService
-- Natural key: commodity_id + year + province + source
