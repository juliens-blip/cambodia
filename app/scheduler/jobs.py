"""APScheduler jobs for daily and weekly data collection and analysis."""
import asyncio
import json
import logging
from datetime import datetime, date

from app.config import settings
from app.collectors import MEFCollector, WITSCollector, ODCCollector, GDriveCollector
from app.services import (
    PerplexityService,
    ClaudeMockService,
    ChromaDBService,
    SupabaseService,
    CHROMADB_AVAILABLE
)

logger = logging.getLogger(__name__)


# Initialize services (will be set by main app)
supabase: SupabaseService = None
chromadb: ChromaDBService = None
perplexity: PerplexityService = None
claude_mock: ClaudeMockService = None


def _normalize_metadata(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def _clean_chroma_metadata(metadata: dict) -> dict:
    if not metadata:
        return {}
    cleaned = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = json.dumps(value, ensure_ascii=True)
    return cleaned


def _build_price_context(price_data: dict) -> str:
    meta = _normalize_metadata(price_data.get("metadata"))
    metric_type = meta.get("metric_type")
    value_unit = meta.get("value_unit")

    if metric_type == "export_value_usd" and value_unit == "thousand_usd":
        context = f"Export value ${price_data['price_usd_per_unit']:,.2f}k USD on {price_data['date']}"
    elif metric_type == "export_value_usd":
        context = f"Export value ${price_data['price_usd_per_unit']:,.2f} USD on {price_data['date']}"
    else:
        context = f"Price ${price_data['price_usd_per_unit']:,.2f}/ton on {price_data['date']}"

    if price_data.get("destination_country"):
        context += f" to {price_data['destination_country']}"

    return context


def init_services(
    supabase_instance: SupabaseService,
    chromadb_instance: ChromaDBService
):
    """Initialize services for jobs."""
    global supabase, chromadb, perplexity, claude_mock

    supabase = supabase_instance
    chromadb = chromadb_instance

    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=settings.perplexity_max_requests_per_month
    )

    claude_mock = ClaudeMockService(mock_mode=settings.claude_mock_mode)

    logger.info("✅ Services initialized for scheduler jobs")


async def run_collectors() -> dict:
    """Run all 4 data collectors in parallel."""
    logger.info("🔄 Starting data collection from all sources...")

    # Import Google Drive folder IDs configuration
    from app.config_gdrive import GDRIVE_FOLDER_IDS

    # Initialize collectors
    mef = MEFCollector(settings.mef_api_url)
    wits = WITSCollector(settings.wits_api_url)
    odc = ODCCollector(settings.odc_base_url)
    gdrive = GDriveCollector(
        api_key=settings.google_drive_api_key,
        folder_ids=GDRIVE_FOLDER_IDS
    )

    # Run collectors in parallel
    try:
        results = await asyncio.gather(
            mef.run(),
            wits.run(),
            odc.run(),
            gdrive.run(),
            return_exceptions=True
        )

        # Process results
        mef_data = results[0] if not isinstance(results[0], Exception) else []
        wits_data = results[1] if not isinstance(results[1], Exception) else []
        odc_data = results[2] if not isinstance(results[2], Exception) else []
        gdrive_data = results[3] if not isinstance(results[3], Exception) else []

        logger.info(f"✅ Collection complete: MEF={len(mef_data)}, WITS={len(wits_data)}, ODC={len(odc_data)}, GDrive={len(gdrive_data)}")

        return {
            "mef": mef_data,
            "wits": wits_data,
            "odc": odc_data,
            "gdrive": gdrive_data
        }

    except Exception as e:
        logger.error(f"❌ Collection error: {e}")
        raise


async def store_data_dual(data: dict):
    """Store data in both Supabase and ChromaDB."""
    if not CHROMADB_AVAILABLE:
        logger.warning("⚠️ ChromaDB not available (incompatible with Python 3.14+) - skipping semantic storage.")
    elif chromadb is None:
        logger.warning("⚠️ ChromaDB not initialized - skipping semantic storage.")

    storage_info = "Supabase + ChromaDB" if (CHROMADB_AVAILABLE and chromadb is not None) else "Supabase only"
    logger.info(f"💾 Storing data in {storage_info}...")

    # Get or create commodities
    cashew = await supabase.get_or_create_commodity("cashew", "nut")
    rubber = await supabase.get_or_create_commodity("rubber", "latex")

    commodity_map = {"cashew": cashew["id"], "rubber": rubber["id"]}

    # Store prices and production
    for source, records in data.items():
        for record in records:
            try:
                commodity = record.get("commodity")
                if commodity not in ["cashew", "rubber"]:
                    continue

                commodity_id = commodity_map[commodity]

                # Determine record type
                if "price_usd" in record:
                    # Price record
                    price_data = {
                        "commodity_id": commodity_id,
                        "date": record["date"],
                        "price_usd_per_unit": record["price_usd"],
                        "volume_tons": record.get("volume_tons"),
                        "source": record["source"],
                        "destination_country": record.get("destination_country"),
                        "quality_grade": record.get("quality_grade"),
                        "metadata": record.get("metadata", {})
                    }

                    # Store in Supabase using upsert to avoid duplicates
                    await supabase.upsert_price(price_data)

                    # Store in ChromaDB with context
                    if CHROMADB_AVAILABLE and chromadb is not None:
                        context = _build_price_context(price_data)
                        record_meta = _normalize_metadata(price_data.get("metadata"))
                        chroma_payload = {**price_data, **record_meta}
                        chroma_payload.pop("metadata", None)
                        chroma_metadata = _clean_chroma_metadata(chroma_payload)
                        await chromadb.store_price_with_context(
                            commodity=commodity,
                            date=price_data["date"],
                            price_usd=price_data["price_usd_per_unit"],
                            context=context,
                            metadata=chroma_metadata
                        )

                elif "production_tons" in record or "area_hectares" in record:
                    # Production record
                    prod_data = {
                        "commodity_id": commodity_id,
                        "year": record.get("year", datetime.now().year),
                        "province": record.get("province", "Unknown"),
                        "area_hectares": record.get("area_hectares"),
                        "production_tons": record.get("production_tons"),
                        "yield_kg_per_ha": record.get("yield_kg_per_ha"),
                        "geolocation": record.get("geolocation"),
                        "source": record["source"]
                    }

                    # Store in Supabase using upsert to avoid duplicates
                    await supabase.upsert_production(prod_data)

                    # Store in ChromaDB
                    if CHROMADB_AVAILABLE and chromadb is not None:
                        context = f"{prod_data['province']}: {prod_data.get('production_tons', 0)} tons"
                        await chromadb.store_production_context(
                            commodity=commodity,
                            year=prod_data["year"],
                            province=prod_data["province"],
                            context=context,
                            metadata=_clean_chroma_metadata(prod_data)
                        )

                elif record.get("type") == "document":
                    if not CHROMADB_AVAILABLE or chromadb is None:
                        continue

                    await chromadb.store_document(
                        commodity=commodity,
                        file_name=record.get("file_name", "unknown"),
                        content=record.get("content", ""),
                        file_type=record.get("file_type", "unknown"),
                        metadata=_clean_chroma_metadata(record.get("metadata", {}))
                    )

                elif record.get("document_type") == "context":
                    # Context document (PDFs without structured data but with crucial contextual information)
                    # Examples: Economic Land Concessions, iTrade bulletins, policy reports
                    context_data = {
                        "document_type": record.get("document_type"),
                        "source": record.get("source"),
                        "commodity": commodity,
                        "title": record.get("title"),
                        "text_content": record.get("text_content"),
                        "url": record.get("url"),
                        "scraped_at": record.get("scraped_at"),
                        "char_count": record.get("char_count"),
                        "extraction_method": record.get("extraction_method")
                    }

                    # Store in Supabase context_documents table
                    await supabase.upsert_context_document(context_data)

                    # Also store in ChromaDB for semantic search if available
                    if CHROMADB_AVAILABLE and chromadb is not None:
                        await chromadb.store_document(
                            commodity=commodity,
                            file_name=context_data["title"],
                            content=context_data["text_content"],
                            file_type="context_pdf",
                            metadata=_clean_chroma_metadata({
                                "source": context_data["source"],
                                "url": context_data.get("url"),
                                "char_count": context_data["char_count"],
                                "extraction_method": context_data.get("extraction_method")
                            })
                        )

            except Exception as e:
                logger.error(f"Error storing record: {e}")
                continue

    logger.info("✅ Data stored successfully")


async def daily_pipeline():
    """
    Daily data collection and analysis pipeline.

    Runs at 6:00 AM Cambodia Time (GMT+7).
    """
    try:
        logger.info("🌅 Starting DAILY pipeline...")

        # 1. Collect data
        data = await run_collectors()

        # 2. Store in dual storage
        await store_data_dual(data)

        # 3. Perplexity analysis for both commodities
        cashew_analysis = await perplexity.research_daily_prices("cashew")
        rubber_analysis = await perplexity.research_daily_prices("rubber")

        # Store analyses in Supabase + ChromaDB
        cashew_commodity = await supabase.get_or_create_commodity("cashew", "nut")
        rubber_commodity = await supabase.get_or_create_commodity("rubber", "latex")

        cashew_analysis["commodity_id"] = cashew_commodity["id"]
        rubber_analysis["commodity_id"] = rubber_commodity["id"]

        await supabase.insert_analysis(cashew_analysis)
        await supabase.insert_analysis(rubber_analysis)

        if CHROMADB_AVAILABLE and chromadb is not None:
            await chromadb.store_analysis(cashew_analysis)
            await chromadb.store_analysis(rubber_analysis)

        # 4. Generate Claude MOCK reports
        # Get latest price data for context
        cashew_prices = await supabase.get_latest_prices(cashew_commodity["id"], limit=2)
        rubber_prices = await supabase.get_latest_prices(rubber_commodity["id"], limit=2)

        cashew_price_data = {
            "price_usd": float(cashew_prices[0]["price_usd_per_unit"]) if cashew_prices else 0,
            "previous_price_usd": float(cashew_prices[1]["price_usd_per_unit"]) if len(cashew_prices) > 1 else 0,
            "volume_tons": cashew_prices[0].get("volume_tons") if cashew_prices else 0,
            "destination_country": cashew_prices[0].get("destination_country") if cashew_prices else "Unknown"
        }

        rubber_price_data = {
            "price_usd": float(rubber_prices[0]["price_usd_per_unit"]) if rubber_prices else 0,
            "previous_price_usd": float(rubber_prices[1]["price_usd_per_unit"]) if len(rubber_prices) > 1 else 0,
            "volume_tons": rubber_prices[0].get("volume_tons") if rubber_prices else 0,
            "destination_country": rubber_prices[0].get("destination_country") if rubber_prices else "Unknown"
        }

        cashew_report = await claude_mock.generate_daily_report(
            "cashew",
            price_data=cashew_price_data,
            perplexity_analysis=cashew_analysis
        )

        rubber_report = await claude_mock.generate_daily_report(
            "rubber",
            price_data=rubber_price_data,
            perplexity_analysis=rubber_analysis
        )

        # Store reports
        cashew_report["commodity_id"] = cashew_commodity["id"]
        rubber_report["commodity_id"] = rubber_commodity["id"]

        await supabase.insert_report(cashew_report)
        await supabase.insert_report(rubber_report)

        if CHROMADB_AVAILABLE and chromadb is not None:
            await chromadb.store_report(cashew_report)
            await chromadb.store_report(rubber_report)

        logger.info("✅ DAILY pipeline complete!")

    except Exception as e:
        logger.error(f"❌ DAILY pipeline failed: {e}")
        raise


async def weekly_pipeline():
    """
    Weekly comprehensive analysis pipeline.

    Runs on Monday at 6:00 AM Cambodia Time.
    """
    try:
        logger.info("📅 Starting WEEKLY pipeline...")

        # Get commodities
        cashew_commodity = await supabase.get_or_create_commodity("cashew", "nut")
        rubber_commodity = await supabase.get_or_create_commodity("rubber", "latex")

        # 1. Aggregate 7-day data
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - 7)

        cashew_week = await supabase.get_week_data(
            cashew_commodity["id"],
            start_date,
            end_date
        )

        rubber_week = await supabase.get_week_data(
            rubber_commodity["id"],
            start_date,
            end_date
        )

        # 2. Perplexity deep research (comprehensive + geopolitics)
        cashew_deep = await perplexity.research_comprehensive("cashew")
        rubber_deep = await perplexity.research_comprehensive("rubber")

        # NEW: Geopolitical analysis (critical for price evolution & global harvest impact)
        cashew_geo = await perplexity.research_geopolitics("cashew")
        rubber_geo = await perplexity.research_geopolitics("rubber")

        # Store geopolitical analyses in Supabase
        cashew_geo["commodity_id"] = cashew_commodity["id"]
        rubber_geo["commodity_id"] = rubber_commodity["id"]

        await supabase.insert_analysis(cashew_geo)
        await supabase.insert_analysis(rubber_geo)

        if CHROMADB_AVAILABLE and chromadb is not None:
            await chromadb.store_analysis(cashew_geo)
            await chromadb.store_analysis(rubber_geo)

        # 3. Generate weekly reports (with geopolitical context)
        cashew_weekly = await claude_mock.generate_weekly_report(
            "cashew",
            week_data=cashew_week,
            perplexity_deep_dive=cashew_deep,
            geopolitical_analysis=cashew_geo
        )

        rubber_weekly = await claude_mock.generate_weekly_report(
            "rubber",
            week_data=rubber_week,
            perplexity_deep_dive=rubber_deep,
            geopolitical_analysis=rubber_geo
        )

        # Store reports
        cashew_weekly["commodity_id"] = cashew_commodity["id"]
        rubber_weekly["commodity_id"] = rubber_commodity["id"]

        await supabase.insert_report(cashew_weekly)
        await supabase.insert_report(rubber_weekly)

        if CHROMADB_AVAILABLE and chromadb is not None:
            await chromadb.store_report(cashew_weekly)
            await chromadb.store_report(rubber_weekly)

        logger.info("✅ WEEKLY pipeline complete!")

        # TODO: Email stakeholders with weekly digest

    except Exception as e:
        logger.error(f"❌ WEEKLY pipeline failed: {e}")
        raise


# Job wrappers for scheduler
def daily_job():
    """Wrapper for daily pipeline (sync)."""
    asyncio.run(daily_pipeline())


def weekly_job():
    """Wrapper for weekly pipeline (sync)."""
    asyncio.run(weekly_pipeline())
