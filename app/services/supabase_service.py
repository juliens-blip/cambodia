"""Supabase service wrapper for database operations."""
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    Service wrapper for Supabase database operations.

    Manages 7 tables:
    1. commodities
    2. prices
    3. production
    4. perplexity_analyses
    5. claude_reports
    6. geopolitical_events
    7. data_sources
    """

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase service.

        Args:
            url: Supabase project URL
            key: Supabase anon/service key
        
        Raises:
            ValueError: If url or key is empty
        """
        if not url or not key:
            raise ValueError("Supabase URL and key are required. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
        
        self.client: Client = create_client(url, key)
        logger.info(f"Supabase service initialized ({url})")

    # ========== COMMODITIES ==========

    async def get_or_create_commodity(self, name: str, category: str) -> Dict[str, Any]:
        """
        Get existing commodity or create new one.

        Args:
            name: 'cashew' or 'rubber'
            category: 'nut' or 'latex'

        Returns:
            Commodity record
        """
        # Try to get existing
        result = self.client.table("commodities").select("*").eq("name", name).execute()

        if result.data:
            return result.data[0]

        # Create new
        new_commodity = {
            "name": name,
            "category": category
        }

        result = self.client.table("commodities").insert(new_commodity).execute()
        logger.info(f"Created commodity: {name}")
        return result.data[0]

    # ========== PRICES ==========

    async def insert_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert price record.

        DEPRECATED: Use upsert_price instead to avoid duplicates.
        """
        result = self.client.table("prices").insert(price_data).execute()
        logger.info(f"Inserted price: {price_data.get('commodity_id')} on {price_data.get('date')}")
        return result.data[0] if result.data else None

    async def upsert_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert price record (insert or update if exists).

        Uses Supabase .upsert() with partial unique indexes:
        - idx_prices_unique_with_destination: (commodity_id, date, source, destination_country) WHERE destination_country IS NOT NULL
        - idx_prices_unique_without_destination: (commodity_id, date, source) WHERE destination_country IS NULL

        This prevents duplicate entries when re-seeding data while properly handling NULL destination_country values.

        The natural key is: commodity_id + date + source + destination_country (with NULL treated distinctly)

        Args:
            price_data: Price data dictionary

        Returns:
            Upserted price record
        """
        # Supabase upsert will automatically use the partial unique indexes
        # The indexes ensure that duplicates are detected correctly based on whether destination_country is NULL or not
        result = self.client.table("prices").upsert(
            price_data,
            ignore_duplicates=False
        ).execute()

        dest_info = f"to {price_data.get('destination_country')}" if price_data.get('destination_country') else "(no destination)"
        logger.info(
            f"Upserted price: {price_data.get('commodity_id')} on {price_data.get('date')} "
            f"from {price_data.get('source')} {dest_info}"
        )
        return result.data[0] if result.data else None

    async def get_latest_prices(
        self,
        commodity_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get latest prices for commodity."""
        result = self.client.table("prices")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .order("date", desc=True)\
            .limit(limit)\
            .execute()

        return result.data

    async def get_price_range(
        self,
        commodity_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get prices within date range."""
        result = self.client.table("prices")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .order("date", desc=True)\
            .execute()

        return result.data

    # ========== PRODUCTION ==========

    async def insert_production(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert production record.

        DEPRECATED: Use upsert_production instead to avoid duplicates.
        """
        result = self.client.table("production").insert(production_data).execute()
        logger.info(f"Inserted production: {production_data.get('province')} {production_data.get('year')}")
        return result.data[0] if result.data else None

    async def upsert_production(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert production record (insert or update if exists).

        Uses natural key: commodity_id + year + province + source
        This prevents duplicate entries when re-seeding data.

        Note: Requires a unique constraint on production table:
        CREATE UNIQUE INDEX IF NOT EXISTS idx_production_unique
        ON production(commodity_id, year, province, source);

        Args:
            production_data: Production data dictionary

        Returns:
            Upserted production record
        """
        result = self.client.table("production").upsert(
            production_data,
            ignore_duplicates=False
        ).execute()

        logger.info(
            f"Upserted production: {production_data.get('province')} {production_data.get('year')} "
            f"from {production_data.get('source')}"
        )
        return result.data[0] if result.data else None

    async def get_production_by_year(
        self,
        commodity_id: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """Get production data for specific year."""
        result = self.client.table("production")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .eq("year", year)\
            .execute()

        return result.data

    async def get_production_by_province(
        self,
        commodity_id: str,
        province: str
    ) -> List[Dict[str, Any]]:
        """Get production data for specific province."""
        result = self.client.table("production")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .eq("province", province)\
            .order("year", desc=True)\
            .execute()

        return result.data

    # ========== PERPLEXITY ANALYSES ==========

    async def insert_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert Perplexity analysis."""
        result = self.client.table("perplexity_analyses").insert(analysis_data).execute()
        logger.info(f"Inserted analysis: {analysis_data.get('commodity_id')} ({analysis_data.get('query_type')})")
        return result.data[0] if result.data else None

    async def get_recent_analyses(
        self,
        commodity_id: str,
        query_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent Perplexity analyses."""
        query = self.client.table("perplexity_analyses")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .order("created_at", desc=True)\
            .limit(limit)

        if query_type:
            query = query.eq("query_type", query_type)

        result = query.execute()
        return result.data

    # ========== CLAUDE REPORTS ==========

    async def insert_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert Claude report."""
        result = self.client.table("claude_reports").insert(report_data).execute()
        logger.info(f"Inserted report: {report_data.get('title')}")
        return result.data[0] if result.data else None

    async def get_reports(
        self,
        commodity_id: str,
        report_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get Claude reports."""
        query = self.client.table("claude_reports")\
            .select("*")\
            .eq("commodity_id", commodity_id)\
            .order("created_at", desc=True)\
            .limit(limit)

        if report_type:
            query = query.eq("report_type", report_type)

        result = query.execute()
        return result.data

    # ========== GEOPOLITICAL EVENTS ==========

    async def insert_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert geopolitical event."""
        result = self.client.table("geopolitical_events").insert(event_data).execute()
        logger.info(f"Inserted event: {event_data.get('title')}")
        return result.data[0] if result.data else None

    async def get_recent_events(
        self,
        limit: int = 10,
        impact_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent geopolitical events."""
        query = self.client.table("geopolitical_events")\
            .select("*")\
            .order("event_date", desc=True)\
            .limit(limit)

        if impact_level:
            query = query.eq("impact_level", impact_level)

        result = query.execute()
        return result.data

    # ========== DATA SOURCES ==========

    async def update_source_status(
        self,
        source_name: str,
        status: str,
        error_log: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update data source status."""
        update_data = {
            "last_fetch": datetime.utcnow().isoformat(),
            "status": status
        }

        if error_log:
            update_data["error_log"] = error_log

        result = self.client.table("data_sources")\
            .update(update_data)\
            .eq("name", source_name)\
            .execute()

        logger.info(f"Updated source status: {source_name} -> {status}")
        return result.data[0] if result.data else None

    async def get_source_status(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Get data source status."""
        result = self.client.table("data_sources")\
            .select("*")\
            .eq("name", source_name)\
            .execute()

        return result.data[0] if result.data else None

    # ========== AGGREGATIONS ==========

    async def get_week_data(
        self,
        commodity_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get aggregated data for a week."""
        # Get prices in range
        prices = await self.get_price_range(commodity_id, start_date, end_date)

        if not prices:
            return {
                "avg_price_usd": 0,
                "total_volume_tons": 0,
                "trend": "stable"
            }

        # Calculate aggregations
        avg_price = sum(p["price_usd_per_unit"] for p in prices) / len(prices)
        total_volume = sum(p["volume_tons"] or 0 for p in prices)

        # Determine trend (simple: compare first vs last)
        if len(prices) >= 2:
            first_price = prices[-1]["price_usd_per_unit"]
            last_price = prices[0]["price_usd_per_unit"]

            if last_price > first_price * 1.05:
                trend = "increasing"
            elif last_price < first_price * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "avg_price_usd": float(avg_price),
            "total_volume_tons": total_volume,
            "trend": trend,
            "num_records": len(prices)
        }

    # ========== CONTEXT DOCUMENTS ==========

    async def upsert_context_document(self, doc_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Upsert context document (insert or update if exists).

        These documents contain crucial contextual information from PDFs
        and reports even when they don't have structured production data.
        Examples: Economic Land Concessions, iTrade bulletins, agricultural reports.

        Uses natural key: source + title + url (if exists)

        Args:
            doc_data: Document data with keys:
                - document_type: 'context'
                - source: 'ODC', 'GDrive', etc.
                - commodity: commodity name (optional)
                - title: document title/filename
                - text_content: extracted text
                - url: source URL (optional)
                - scraped_at: timestamp
                - char_count: character count
                - extraction_method: 'ocr' or 'text'

        Returns:
            Inserted/updated document record or None if failed
        """
        try:
            # Check if table exists first
            result = self.client.table("context_documents").select("id").limit(1).execute()
        except Exception as e:
            logger.warning(f"context_documents table may not exist yet: {e}")
            return None

        try:
            # Try to find existing document by source + title
            existing = self.client.table("context_documents")\
                .select("*")\
                .eq("source", doc_data.get("source"))\
                .eq("title", doc_data.get("title"))\
                .execute()

            if existing.data:
                # Update existing
                doc_id = existing.data[0]["id"]
                result = self.client.table("context_documents")\
                    .update(doc_data)\
                    .eq("id", doc_id)\
                    .execute()
                logger.info(f"Updated context document: {doc_data.get('title')}")
            else:
                # Insert new
                result = self.client.table("context_documents")\
                    .insert(doc_data)\
                    .execute()
                logger.info(f"Inserted context document: {doc_data.get('title')} ({doc_data.get('char_count')} chars)")

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Failed to upsert context document: {e}")
            return None

    async def get_context_documents(
        self,
        source: Optional[str] = None,
        commodity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get context documents with optional filtering.

        Args:
            source: Filter by source (ODC, GDrive, etc.)
            commodity: Filter by commodity
            limit: Maximum number of documents to return

        Returns:
            List of context documents
        """
        try:
            query = self.client.table("context_documents").select("*")

            if source:
                query = query.eq("source", source)
            if commodity:
                query = query.eq("commodity", commodity)

            result = query.order("scraped_at", desc=True).limit(limit).execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get context documents: {e}")
            return []

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        tables = ["commodities", "prices", "production", "perplexity_analyses",
                  "claude_reports", "geopolitical_events", "data_sources", "context_documents"]

        for table in tables:
            try:
                result = self.client.table(table).select("id", count="exact").execute()
                stats[table] = result.count
            except Exception as e:
                logger.error(f"Error getting stats for {table}: {e}")
                stats[table] = 0

        return stats
