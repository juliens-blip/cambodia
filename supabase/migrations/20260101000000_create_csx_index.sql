-- Migration: Create CSX Index table for persistent macro indicators
-- Date: 2026-01-01
-- Purpose: Store Cambodia Stock Exchange index values for fallback when MEF API returns null

-- Create csx_index table
CREATE TABLE IF NOT EXISTS public.csx_index (
    id SERIAL PRIMARY KEY,
    value NUMERIC(10, 2) NOT NULL,
    change_percent NUMERIC(5, 2),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add index on updated_at for fast retrieval of latest value
CREATE INDEX IF NOT EXISTS idx_csx_index_updated_at ON public.csx_index(updated_at DESC);

-- Add comment
COMMENT ON TABLE public.csx_index IS 'Stores Cambodia Stock Exchange (CSX) index values for persistence and fallback';
COMMENT ON COLUMN public.csx_index.value IS 'CSX index value (e.g., 1234.56)';
COMMENT ON COLUMN public.csx_index.change_percent IS 'Percentage change from previous day';
COMMENT ON COLUMN public.csx_index.updated_at IS 'Timestamp when the index value was fetched from MEF API';

-- Enable Row Level Security (RLS)
ALTER TABLE public.csx_index ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users (read-only for now)
CREATE POLICY "Allow public read access to csx_index"
    ON public.csx_index
    FOR SELECT
    USING (true);

-- Create policy for service role (full access for API)
CREATE POLICY "Allow service role full access to csx_index"
    ON public.csx_index
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Insert initial placeholder value if needed (optional)
-- INSERT INTO public.csx_index (value, change_percent) VALUES (0.00, 0.00);
