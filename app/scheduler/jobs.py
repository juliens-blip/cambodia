"""
Background Jobs with APScheduler
Daily market analysis for cambodian agricultural commodities
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from app.config import settings


# Create scheduler instance (will be started in main.py)
scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)

# Shared services for data ingestion
_supabase_service = None
_chromadb_service = None


def init_services(supabase, chromadb=None) -> None:
    """Initialize shared services for ingestion helpers."""
    global _supabase_service, _chromadb_service
    _supabase_service = supabase
    _chromadb_service = chromadb


async def store_data_dual(
    data: Dict[str, List[Dict[str, Any]]],
    supabase=None,
    chromadb=None
) -> Dict[str, int]:
    """Store collector data into Supabase (and ChromaDB when available)."""
    supabase = supabase or _supabase_service
    chromadb = chromadb or _chromadb_service

    if supabase is None:
        raise ValueError("Supabase service not initialized")

    commodity_cache: Dict[str, str] = {}
    summary = {"prices": 0, "production": 0, "documents": 0}

    def normalize_volume_tons(value: Any) -> Optional[int]:
        """Supabase prices.volume_tons is integer; round floats safely."""
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(round(value))
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        try:
            return int(round(float(text)))
        except ValueError:
            return None

    async def get_commodity_id(name: str) -> Optional[str]:
        if name in commodity_cache:
            return commodity_cache[name]
        category = "nut" if name == "cashew" else "latex"
        record = await supabase.get_or_create_commodity(name, category)
        commodity_cache[name] = record["id"]
        return commodity_cache[name]

    for source, records in data.items():
        for record in records:
            commodity = record.get("commodity")
            if commodity not in ["cashew", "rubber"]:
                continue

            if record.get("document_type") == "context":
                await supabase.upsert_context_document(record)
                summary["documents"] += 1
                continue

            if record.get("type") == "document" and chromadb:
                try:
                    await chromadb.store_document(
                        commodity=record.get("commodity"),
                        file_name=record.get("file_name"),
                        content=record.get("content", ""),
                        file_type=record.get("file_type", ""),
                        metadata=record.get("metadata")
                    )
                except Exception as exc:
                    logger.warning("Chroma document store failed: %s", exc)
                continue

            if "year" in record and "province" in record:
                commodity_id = await get_commodity_id(commodity)
                production_data = {
                    "commodity_id": commodity_id,
                    "year": record.get("year"),
                    "province": record.get("province"),
                    "area_hectares": record.get("area_hectares"),
                    "production_tons": record.get("production_tons"),
                    "yield_kg_per_ha": record.get("yield_kg_per_ha"),
                    "geolocation": record.get("geolocation"),
                    "source": record.get("source", source)
                }
                await supabase.upsert_production(production_data)
                summary["production"] += 1
                continue

            if "date" in record and ("price_usd" in record or "price_usd_per_unit" in record):
                commodity_id = await get_commodity_id(commodity)
                price_value = record.get("price_usd_per_unit")
                if price_value is None:
                    price_value = record.get("price_usd")
                if price_value is None:
                    continue
                volume_tons = normalize_volume_tons(record.get("volume_tons"))
                price_data = {
                    "commodity_id": commodity_id,
                    "date": record.get("date"),
                    "price_usd_per_unit": price_value,
                    "volume_tons": volume_tons,
                    "source": record.get("source", source),
                    "destination_country": record.get("destination_country"),
                    "quality_grade": record.get("quality_grade"),
                    "metadata": record.get("metadata")
                }
                await supabase.upsert_price(price_data)
                summary["prices"] += 1

    return summary


async def run_collectors(
    collectors: Optional[List[Any]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Run collectors in parallel and return results by source."""
    if collectors is None:
        from app.collectors import GDriveCollector, MEFCollector, WITSCollector, ODCCollector
        from app.config_gdrive import GDRIVE_FOLDER_IDS

        collectors = [
            MEFCollector(settings.mef_api_url),
            WITSCollector(settings.wits_api_url),
            ODCCollector(settings.odc_base_url)
        ]
        if settings.google_drive_api_key:
            collectors.append(
                GDriveCollector(
                    api_key=settings.google_drive_api_key,
                    folder_ids=GDRIVE_FOLDER_IDS
                )
            )
        else:
            logger.warning("GDrive collector skipped: missing API key")

    results = await asyncio.gather(
        *[collector.run() for collector in collectors],
        return_exceptions=True
    )

    data: Dict[str, List[Dict[str, Any]]] = {}
    for collector, result in zip(collectors, results):
        key = collector.source_name.lower()
        if isinstance(result, Exception):
            logger.warning("Collector %s failed: %s", collector.source_name, result)
            data[key] = []
        else:
            data[key] = result

    return data


async def monthly_free_sources_collection() -> None:
    """Collect free-source data (FAO GIEWS/FPMA, CAC, WITS) monthly."""
    from app.collectors import FAOGIEWSCollector, CACCollector, WITSCollector
    from app.services.supabase_service import SupabaseService
    from app.services.chromadb_service import ChromaDBService

    print(f"[SCHEDULER] Starting monthly free-source collection at {datetime.now()}", flush=True)

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        print(f"[SCHEDULER] Supabase unavailable: {exc}", flush=True)
        return

    chromadb = None
    try:
        chromadb = ChromaDBService(
            host=settings.chroma_host,
            port=settings.chroma_port,
            persist_path=settings.chroma_persist_path
        )
        chromadb.init_collections()
    except Exception as exc:
        print(f"[SCHEDULER] ChromaDB unavailable: {exc}", flush=True)
        chromadb = None

    init_services(supabase, chromadb)

    wits_collector = WITSCollector(
        api_url=settings.wits_api_url,
        reporter="KHM",
        partner="vnm",
        product_map={"cashew": "080130"}
    )
    collectors = [
        FAOGIEWSCollector(commodity="cashew"),
        FAOGIEWSCollector(commodity="rubber", country_filter="Thailand"),  # Thailand as proxy for Cambodia
        CACCollector(commodity="cashew"),
        CACCollector(commodity="rubber"),  # CAC rubber reports if available
        wits_collector
    ]

    data = await run_collectors(collectors)
    summary = await store_data_dual(data, supabase, chromadb)

    print(f"[SCHEDULER] Monthly collection complete: {summary}", flush=True)


async def daily_market_analysis():
    """
    Run daily market analysis for all commodities at 9:00 AM
    This job:
    1. Analyzes Twitter/X sentiment
    2. Fetches stock market data
    3. Generates AI analysis via Perplexity
    4. Stores results in Supabase
    """
    from app.services.market_trends_service import MarketTrendsService
    from app.services.perplexity_service import PerplexityService
    from app.services.supabase_service import SupabaseService

    print(f"[SCHEDULER] Starting daily market analysis at {datetime.now()}", flush=True)

    commodities = ["cashew", "rubber"]

    for commodity in commodities:
        try:
            print(f"[SCHEDULER] Analyzing {commodity}...", flush=True)

            # Get services
            supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
            perplexity = PerplexityService(
                api_key=settings.perplexity_api_key,
                max_requests_per_month=settings.perplexity_max_requests_per_month
            )
            trends_service = MarketTrendsService(supabase, perplexity)

            # Run analysis (force_refresh=True to ensure new analysis)
            result = await trends_service.analyze_and_store_trends(
                commodity=commodity,
                force_refresh=True
            )

            print(f"[SCHEDULER] ✅ {commodity} analysis completed: {result}", flush=True)

        except Exception as e:
            print(f"[SCHEDULER] ❌ Error analyzing {commodity}: {e}", flush=True)

    print(f"[SCHEDULER] Daily market analysis completed at {datetime.now()}", flush=True)


async def daily_rubber_price_collection():
    """
    Collect daily rubber spot price from TradingEconomics.

    This job:
    1. Scrapes TradingEconomics for rubber spot price
    2. Stores price in Supabase prices table
    3. Runs at 08:00 UTC (15:00 Cambodia time)
    """
    from app.collectors.tradingeconomics_collector import TradingEconomicsCollector
    from app.services.supabase_service import SupabaseService

    print(f"[SCHEDULER] Collecting rubber price from TradingEconomics at {datetime.now()}", flush=True)

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        print(f"[SCHEDULER] Supabase unavailable: {exc}", flush=True)
        return

    try:
        collector = TradingEconomicsCollector(commodity="rubber", timeout=30.0)
        records = await collector.collect()

        if not records:
            print("[SCHEDULER] ⚠️ No rubber price data collected", flush=True)
            return

        # Store in Supabase
        init_services(supabase)
        data = {"tradingeconomics": records}
        summary = await store_data_dual(data, supabase)

        print(f"[SCHEDULER] ✅ Rubber price collected: {summary}", flush=True)

        # Log price details
        for record in records:
            price_usd_ton = record.get("price_usd_per_unit", 0)
            price_cents_kg = record.get("price_cents_per_kg", 0)
            print(
                f"[SCHEDULER] 💰 Rubber: {price_usd_ton:.2f} USD/ton ({price_cents_kg:.2f} cents/kg)",
                flush=True
            )

    except Exception as e:
        print(f"[SCHEDULER] ❌ Rubber price collection failed: {e}", flush=True)


def schedule_daily_jobs():
    """Schedule all daily jobs"""
    import logging
    logger = logging.getLogger(__name__)

    # Daily market analysis at 9:00 AM (Cambodia time - UTC+7)
    # If Railway/server is UTC, this runs at 02:00 UTC = 09:00 Cambodia time
    scheduler.add_job(
        daily_market_analysis,
        trigger=CronTrigger(hour=2, minute=0),  # 02:00 UTC = 09:00 Cambodia
        id="daily_market_analysis",
        name="Daily Market Analysis (9:00 AM Cambodia)",
        replace_existing=True,
        max_instances=1,  # Prevent multiple concurrent runs
    )

    logger.info("[SCHEDULER] Scheduled job: Daily Market Analysis at 02:00 UTC (09:00 Cambodia)")
    print("[SCHEDULER] Scheduled job: Daily Market Analysis at 02:00 UTC (09:00 Cambodia)", flush=True)

    # Daily rubber price collection at 08:00 UTC (15:00 Cambodia time)
    scheduler.add_job(
        daily_rubber_price_collection,
        trigger=CronTrigger(hour=8, minute=0),  # 08:00 UTC = 15:00 Cambodia
        id="daily_rubber_price",
        name="Daily Rubber Price (TradingEconomics)",
        replace_existing=True,
        max_instances=1,
    )

    logger.info("[SCHEDULER] Scheduled job: Daily Rubber Price at 08:00 UTC (15:00 Cambodia)")
    print("[SCHEDULER] Scheduled job: Daily Rubber Price at 08:00 UTC (15:00 Cambodia)", flush=True)


def schedule_monthly_jobs():
    """Schedule monthly free-source ingestion jobs."""
    scheduler.add_job(
        monthly_free_sources_collection,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        id="monthly_free_sources",
        name="Monthly Free Sources Collection (FAO/CAC/WITS)",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("[SCHEDULER] Scheduled job: Monthly free sources at day 1 03:00 UTC")
    print("[SCHEDULER] Scheduled job: Monthly free sources at day 1 03:00 UTC", flush=True)


def start_scheduler():
    """Start the scheduler"""
    import logging
    logger = logging.getLogger(__name__)

    if not scheduler.running:
        schedule_daily_jobs()
        schedule_monthly_jobs()
        scheduler.start()
        logger.info("[SCHEDULER] ✅ Scheduler started")
        print("[SCHEDULER] ✅ Scheduler started", flush=True)

        # Trigger immediate analysis on startup (non-blocking)
        logger.info("[SCHEDULER] 🚀 Triggering immediate analysis on startup...")
        print("[SCHEDULER] 🚀 Triggering immediate analysis on startup...", flush=True)
        scheduler.add_job(
            daily_market_analysis,
            id="startup_analysis",
            name="Startup Market Analysis (immediate)",
            replace_existing=True,
        )
    else:
        logger.warning("[SCHEDULER] ⚠️ Scheduler already running")
        print("[SCHEDULER] ⚠️ Scheduler already running", flush=True)


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        print("[SCHEDULER] 🛑 Scheduler stopped", flush=True)
