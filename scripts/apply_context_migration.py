"""Apply context_documents table migration to Supabase.

This script creates the context_documents table for storing PDF and document extracts
that provide crucial contextual information for agricultural analysis.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from supabase import create_client, Client


MIGRATION_SQL = """
-- Create context_documents table for storing PDF and document extracts
-- These documents provide crucial contextual information for agricultural analysis

CREATE TABLE IF NOT EXISTS public.context_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT NOT NULL DEFAULT 'context',
    source TEXT NOT NULL,
    commodity TEXT,
    title TEXT NOT NULL,
    text_content TEXT NOT NULL,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    char_count INTEGER,
    extraction_method TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_context_documents_source ON public.context_documents(source);
CREATE INDEX IF NOT EXISTS idx_context_documents_commodity ON public.context_documents(commodity);
CREATE INDEX IF NOT EXISTS idx_context_documents_scraped_at ON public.context_documents(scraped_at DESC);

-- Enable Row Level Security
ALTER TABLE public.context_documents ENABLE ROW LEVEL SECURITY;

-- Create policy for read access (public read)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'context_documents'
        AND policyname = 'Allow public read access on context_documents'
    ) THEN
        CREATE POLICY "Allow public read access on context_documents"
            ON public.context_documents
            FOR SELECT
            USING (true);
    END IF;
END $$;

-- Create policy for insert access (authenticated users)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'context_documents'
        AND policyname = 'Allow authenticated insert on context_documents'
    ) THEN
        CREATE POLICY "Allow authenticated insert on context_documents"
            ON public.context_documents
            FOR INSERT
            WITH CHECK (true);
    END IF;
END $$;

-- Create policy for update access (authenticated users)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'context_documents'
        AND policyname = 'Allow authenticated update on context_documents'
    ) THEN
        CREATE POLICY "Allow authenticated update on context_documents"
            ON public.context_documents
            FOR UPDATE
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_context_documents_updated_at ON public.context_documents;
CREATE TRIGGER update_context_documents_updated_at
    BEFORE UPDATE ON public.context_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE public.context_documents IS 'Stores extracted text from PDFs and documents for contextual analysis. These documents provide crucial background information about agricultural policies, concessions, market reports, and industry context even when they do not contain structured production data.';
"""


async def apply_migration():
    """Apply the context_documents migration."""
    print("🚀 Applying context_documents migration...")
    print(f"   URL: {settings.supabase_url}")

    # Note: Supabase Python client doesn't support direct DDL execution
    # The SQL must be executed via:
    # 1. Supabase Dashboard SQL Editor
    # 2. Supabase CLI (supabase db push)
    # 3. Direct PostgreSQL connection

    print("\n📝 Migration SQL:")
    print("=" * 80)
    print(MIGRATION_SQL)
    print("=" * 80)

    print("\n⚠️  IMPORTANT: Supabase Python client doesn't support direct DDL execution.")
    print("\n📌 To apply this migration, choose one of these methods:")
    print("\n   METHOD 1: Supabase Dashboard (Recommended)")
    print("   1. Go to: https://supabase.com/dashboard")
    print("   2. Navigate to: SQL Editor")
    print("   3. Copy the SQL above and execute it")

    print("\n   METHOD 2: Supabase CLI")
    print("   1. Install: npm install -g supabase")
    print("   2. Link project: supabase link --project-ref <your-ref>")
    print("   3. Run: supabase db push")

    print("\n   METHOD 3: Direct PostgreSQL Connection")
    print("   1. Use pgAdmin or psql with your Supabase connection string")
    print("   2. Execute the SQL above")

    print("\n💡 The migration SQL has been saved to:")
    print("   supabase/migrations/20251226000000_create_context_documents.sql")

    print("\n✅ Once applied, you can verify with:")
    print("   python scripts/seed_collectors.py --include-odc")
    print("   # Check logs for 'Upserted context document' messages")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Cambodia Agri Analytics - Context Documents Migration     ║
║   Create table for PDF contextual information               ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(apply_migration())
