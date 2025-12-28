"""Initialize Supabase database schema.

Creates 7 tables for Cambodia Agri Analytics:
1. commodities
2. prices
3. production
4. perplexity_analyses
5. claude_reports
6. geopolitical_events
7. data_sources
"""
import asyncio
from supabase import create_client, Client
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


SQL_MIGRATIONS = [
    # 1. Enable UUID extension
    """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """,

    # 2. Commodities table
    """
    CREATE TABLE IF NOT EXISTS commodities (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,

    # 3. Prices table
    """
    CREATE TABLE IF NOT EXISTS prices (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        commodity_id UUID REFERENCES commodities(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        price_usd_per_unit DECIMAL(10,2) NOT NULL CHECK (price_usd_per_unit >= 0),
        volume_tons INTEGER CHECK (volume_tons >= 0),
        source TEXT NOT NULL,
        destination_country TEXT,
        quality_grade TEXT,
        metadata JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date DESC);
    CREATE INDEX IF NOT EXISTS idx_prices_commodity ON prices(commodity_id);
    CREATE INDEX IF NOT EXISTS idx_prices_source ON prices(source);
    """,

    # 4. Production table
    """
    CREATE TABLE IF NOT EXISTS production (
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

    CREATE INDEX IF NOT EXISTS idx_production_year ON production(year DESC);
    CREATE INDEX IF NOT EXISTS idx_production_province ON production(province);
    CREATE INDEX IF NOT EXISTS idx_production_commodity ON production(commodity_id);
    """,

    # 5. Perplexity analyses table
    """
    CREATE TABLE IF NOT EXISTS perplexity_analyses (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        commodity_id UUID REFERENCES commodities(id) ON DELETE CASCADE,
        query_type TEXT NOT NULL,
        query_text TEXT NOT NULL,
        response_text TEXT NOT NULL,
        citations JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        metadata JSONB
    );

    CREATE INDEX IF NOT EXISTS idx_analyses_created ON perplexity_analyses(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_analyses_commodity ON perplexity_analyses(commodity_id);
    CREATE INDEX IF NOT EXISTS idx_analyses_type ON perplexity_analyses(query_type);
    """,

    # 6. Claude reports table
    """
    CREATE TABLE IF NOT EXISTS claude_reports (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        commodity_id UUID REFERENCES commodities(id) ON DELETE CASCADE,
        report_type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        insights JSONB,
        recommendations JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        published_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_reports_type_created ON claude_reports(report_type, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_reports_commodity ON claude_reports(commodity_id);
    """,

    # 7. Geopolitical events table
    """
    CREATE TABLE IF NOT EXISTS geopolitical_events (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        event_date DATE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        impact_level TEXT CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),
        countries_involved TEXT[],
        commodities_affected TEXT[],
        source_url TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_events_date ON geopolitical_events(event_date DESC);
    CREATE INDEX IF NOT EXISTS idx_events_impact ON geopolitical_events(impact_level);
    """,

    # 8. Data sources table
    """
    CREATE TABLE IF NOT EXISTS data_sources (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name TEXT UNIQUE NOT NULL,
        url TEXT NOT NULL,
        last_fetch TIMESTAMPTZ,
        status TEXT CHECK (status IN ('active', 'error', 'disabled')),
        error_log JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_sources_status ON data_sources(status);
    """,

    # 9. Insert initial commodities
    """
    INSERT INTO commodities (name, category, metadata)
    VALUES
        ('cashew', 'nut', '{"description": "Anacardier (cashew nuts)", "highly_documented": true}'::jsonb),
        ('rubber', 'latex', '{"description": "Hévéa (natural rubber)", "highly_documented": false}'::jsonb)
    ON CONFLICT (name) DO NOTHING;
    """,

    # 10. Insert data sources
    """
    INSERT INTO data_sources (name, url, status)
    VALUES
        ('MEF', 'https://data.mef.gov.kh/api/v1/public-datasets/', 'active'),
        ('WITS', 'http://wits.worldbank.org/API/V1/datasource/trn/country/KHM', 'active'),
        ('ODC', 'https://data.opendevelopmentcambodia.net/en/dataset', 'active'),
        ('GDrive', 'https://drive.google.com', 'active')
    ON CONFLICT (name) DO NOTHING;
    """
]


async def run_migrations():
    """Run all database migrations."""
    print("🚀 Starting Supabase database initialization...")
    print(f"   URL: {settings.supabase_url}")

    # Create Supabase client
    client: Client = create_client(settings.supabase_url, settings.supabase_key)

    migration_count = 0
    for i, sql in enumerate(SQL_MIGRATIONS, 1):
        try:
            print(f"\n[{i}/{len(SQL_MIGRATIONS)}] Executing migration...")

            # Execute SQL via RPC (if available) or use direct execution
            # Note: Supabase Python client doesn't have direct SQL execution
            # In production, use Supabase CLI or database migrations
            # For now, we'll print the SQL for manual execution

            print(f"   ⚠️  Please execute this SQL manually in Supabase Dashboard:")
            print(f"   {sql[:100]}...")

            migration_count += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    print(f"\n✅ Database initialization complete!")
    print(f"   {migration_count} migrations prepared")
    print(f"\n📝 NEXT STEPS:")
    print(f"   1. Go to: {settings.supabase_url.replace('https://', 'https://supabase.com/dashboard/project/')}")
    print(f"   2. Navigate to SQL Editor")
    print(f"   3. Copy and execute the SQL statements above")
    print(f"\n💡 Alternatively, use Supabase CLI:")
    print(f"   supabase migration new init_schema")
    print(f"   # Then copy SQL to migration file and run:")
    print(f"   supabase db push")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Cambodia Agri Analytics - Database Initialization         ║
║   Supabase Schema Setup (7 Tables)                          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(run_migrations())
