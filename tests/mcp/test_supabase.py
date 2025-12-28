"""
Test script for Supabase MCP Server
Tests database queries for Cambodia Agri Analytics
"""

import asyncio
from datetime import datetime, timedelta


async def test_supabase_connection():
    """Test Supabase connection and basic queries"""

    print("=" * 60)
    print("TESTING SUPABASE MCP - Database Connection")
    print("=" * 60)

    print("\nProject Details:")
    print(f"   Project Ref: xqfozbocgyrelznccweh")
    print(f"   URL: https://xqfozbocgyrelznccweh.supabase.co")
    print(f"   Mode: READ-ONLY (via MCP)")

    print("\nRequired Environment Variables:")
    print("   SUPABASE_ACCESS_TOKEN - Get from Supabase Dashboard > Account > Access Tokens")

    print("\n" + "=" * 60)


async def test_cashew_prices_query():
    """Test querying cashew_prices table"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Cashew Prices Query")
    print("=" * 60)

    print("\n1. Table: cashew_prices")
    print("\n2. Sample queries:")

    # Query 1: Recent prices
    print("\n   a. Get last 10 prices:")
    print("      SELECT * FROM cashew_prices")
    print("      ORDER BY date DESC")
    print("      LIMIT 10;")

    # Query 2: Price by destination
    print("\n   b. Vietnam exports this week:")
    print("      SELECT date, price_usd_per_ton, volume_tons")
    print("      FROM cashew_prices")
    print("      WHERE country_destination = 'Vietnam'")
    print("        AND date >= CURRENT_DATE - INTERVAL '7 days'")
    print("      ORDER BY date DESC;")

    # Query 3: Average price by grade
    print("\n   c. Average prices by quality grade:")
    print("      SELECT quality_grade,")
    print("             AVG(price_usd_per_ton) as avg_price,")
    print("             COUNT(*) as num_transactions")
    print("      FROM cashew_prices")
    print("      WHERE date >= CURRENT_DATE - INTERVAL '30 days'")
    print("      GROUP BY quality_grade")
    print("      ORDER BY avg_price DESC;")

    # Query 4: Price trends
    print("\n   d. Daily price trends (last 30 days):")
    print("      SELECT date,")
    print("             AVG(price_usd_per_ton) as avg_daily_price,")
    print("             SUM(volume_tons) as total_volume")
    print("      FROM cashew_prices")
    print("      WHERE date >= CURRENT_DATE - INTERVAL '30 days'")
    print("      GROUP BY date")
    print("      ORDER BY date;")

    print("\n" + "=" * 60)


async def test_production_data_query():
    """Test querying production_data table"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Production Data Query")
    print("=" * 60)

    print("\n1. Table: production_data")
    print("\n2. Sample queries:")

    # Query 1: Top producing provinces
    print("\n   a. Top 5 producing provinces (2023):")
    print("      SELECT province,")
    print("             production_tons,")
    print("             area_hectares,")
    print("             yield_kg_per_hectare")
    print("      FROM production_data")
    print("      WHERE year = 2023")
    print("      ORDER BY production_tons DESC")
    print("      LIMIT 5;")

    # Query 2: Year-over-year growth
    print("\n   b. Year-over-year growth by province:")
    print("      WITH current_year AS (")
    print("        SELECT province, production_tons")
    print("        FROM production_data WHERE year = 2023")
    print("      ),")
    print("      previous_year AS (")
    print("        SELECT province, production_tons")
    print("        FROM production_data WHERE year = 2022")
    print("      )")
    print("      SELECT c.province,")
    print("             c.production_tons as production_2023,")
    print("             p.production_tons as production_2022,")
    print("             ((c.production_tons - p.production_tons) / p.production_tons * 100) as growth_pct")
    print("      FROM current_year c")
    print("      JOIN previous_year p ON c.province = p.province")
    print("      ORDER BY growth_pct DESC;")

    print("\n" + "=" * 60)


async def test_perplexity_analyses_query():
    """Test querying perplexity_analyses table"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Perplexity Analyses Query")
    print("=" * 60)

    print("\n1. Table: perplexity_analyses")
    print("\n2. Sample queries:")

    # Query 1: Recent analyses
    print("\n   a. Recent price trend analyses:")
    print("      SELECT query_text, response_text, citations, created_at")
    print("      FROM perplexity_analyses")
    print("      WHERE query_type = 'price_trend'")
    print("      ORDER BY created_at DESC")
    print("      LIMIT 5;")

    # Query 2: Geopolitical analyses
    print("\n   b. Geopolitical analyses this week:")
    print("      SELECT query_text,")
    print("             LEFT(response_text, 200) as summary,")
    print("             created_at")
    print("      FROM perplexity_analyses")
    print("      WHERE query_type = 'geopolitics'")
    print("        AND created_at >= CURRENT_DATE - INTERVAL '7 days'")
    print("      ORDER BY created_at DESC;")

    # Query 3: Citation counts
    print("\n   c. Most cited sources:")
    print("      SELECT jsonb_array_elements(citations)->>'url' as source_url,")
    print("             COUNT(*) as citation_count")
    print("      FROM perplexity_analyses")
    print("      WHERE citations IS NOT NULL")
    print("      GROUP BY source_url")
    print("      ORDER BY citation_count DESC")
    print("      LIMIT 10;")

    print("\n" + "=" * 60)


async def test_claude_reports_query():
    """Test querying claude_reports table"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Claude Reports Query")
    print("=" * 60)

    print("\n1. Table: claude_reports")
    print("\n2. Sample queries:")

    # Query 1: Latest reports
    print("\n   a. Latest daily reports:")
    print("      SELECT title, created_at, published_at")
    print("      FROM claude_reports")
    print("      WHERE report_type = 'daily'")
    print("      ORDER BY created_at DESC")
    print("      LIMIT 7;")

    # Query 2: Weekly reports
    print("\n   b. Weekly reports with insights:")
    print("      SELECT title,")
    print("             insights,")
    print("             recommendations,")
    print("             published_at")
    print("      FROM claude_reports")
    print("      WHERE report_type = 'weekly'")
    print("      ORDER BY published_at DESC;")

    print("\n" + "=" * 60)


async def test_geopolitical_events_query():
    """Test querying geopolitical_events table"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Geopolitical Events Query")
    print("=" * 60)

    print("\n1. Table: geopolitical_events")
    print("\n2. Sample queries:")

    # Query 1: High-impact events
    print("\n   a. High-impact events this month:")
    print("      SELECT event_date, title, description, impact_level")
    print("      FROM geopolitical_events")
    print("      WHERE impact_level IN ('high', 'critical')")
    print("        AND event_date >= DATE_TRUNC('month', CURRENT_DATE)")
    print("      ORDER BY event_date DESC;")

    # Query 2: Events by country
    print("\n   b. Events involving Vietnam or China:")
    print("      SELECT event_date, title, countries_involved, source_url")
    print("      FROM geopolitical_events")
    print("      WHERE 'Vietnam' = ANY(countries_involved)")
    print("         OR 'China' = ANY(countries_involved)")
    print("      ORDER BY event_date DESC")
    print("      LIMIT 10;")

    print("\n" + "=" * 60)


async def test_dashboard_queries():
    """Test complex queries for dashboard views"""

    print("\n" + "=" * 60)
    print("TESTING SUPABASE MCP - Dashboard Complex Queries")
    print("=" * 60)

    print("\n1. Market Overview Dashboard:")
    print("""
    SELECT
      (SELECT AVG(price_usd_per_ton)
       FROM cashew_prices
       WHERE date >= CURRENT_DATE - INTERVAL '7 days') as avg_price_week,

      (SELECT SUM(volume_tons)
       FROM cashew_prices
       WHERE date >= CURRENT_DATE - INTERVAL '7 days') as total_volume_week,

      (SELECT COUNT(*)
       FROM perplexity_analyses
       WHERE created_at >= CURRENT_DATE - INTERVAL '1 day') as analyses_today,

      (SELECT COUNT(*)
       FROM geopolitical_events
       WHERE impact_level IN ('high', 'critical')
         AND event_date >= CURRENT_DATE - INTERVAL '30 days') as critical_events_month;
    """)

    print("\n2. Price Alert Query:")
    print("""
    WITH price_stats AS (
      SELECT AVG(price_usd_per_ton) as avg_price,
             STDDEV(price_usd_per_ton) as stddev_price
      FROM cashew_prices
      WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    )
    SELECT cp.date, cp.price_usd_per_ton, cp.quality_grade,
           CASE
             WHEN cp.price_usd_per_ton > ps.avg_price + (2 * ps.stddev_price) THEN 'HIGH_ALERT'
             WHEN cp.price_usd_per_ton < ps.avg_price - (2 * ps.stddev_price) THEN 'LOW_ALERT'
             ELSE 'NORMAL'
           END as price_status
    FROM cashew_prices cp
    CROSS JOIN price_stats ps
    WHERE cp.date >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY cp.date DESC;
    """)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_supabase_connection())
    asyncio.run(test_cashew_prices_query())
    asyncio.run(test_production_data_query())
    asyncio.run(test_perplexity_analyses_query())
    asyncio.run(test_claude_reports_query())
    asyncio.run(test_geopolitical_events_query())
    asyncio.run(test_dashboard_queries())

    print("\n" + "=" * 60)
    print("ALL SUPABASE TESTS COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create Supabase Personal Access Token")
    print("2. Set SUPABASE_ACCESS_TOKEN in environment")
    print("3. Run queries via Claude Code with Supabase MCP")
    print("4. Verify READ-ONLY mode working correctly")
