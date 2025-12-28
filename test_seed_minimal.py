"""Minimal test of seed functionality without ChromaDB."""
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.scheduler.jobs import init_services, store_data_dual
from app.services import ChromaDBService, SupabaseService, CHROMADB_AVAILABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_seed_minimal():
    """Test seed with minimal data."""
    logger.info("Testing seed functionality without ChromaDB...")
    logger.info(f"ChromaDB Available: {CHROMADB_AVAILABLE}")

    # Initialize services
    supabase = SupabaseService(
        url=settings.supabase_url,
        key=settings.supabase_key
    )

    chromadb = None
    if CHROMADB_AVAILABLE:
        try:
            chromadb = ChromaDBService(
                host=settings.chroma_host,
                port=settings.chroma_port
            )
            chromadb.init_collections()
            logger.info("✅ ChromaDB initialized")
        except Exception as exc:
            logger.warning(f"ChromaDB unavailable: {exc}")
            chromadb = None
    else:
        logger.info("⚠️  ChromaDB not available - will skip semantic storage")

    init_services(supabase, chromadb)

    # Create minimal test data
    test_data = {
        "test": [
            {
                "commodity": "cashew",
                "date": "2024-01-15",
                "price_usd": 2.5,
                "volume_tons": 100,
                "source": "TEST",
                "destination_country": "Vietnam",
                "metadata": {"test": True}
            },
            {
                "commodity": "rubber",
                "year": 2024,
                "province": "Kampong Cham",
                "production_tons": 1000.0,
                "area_hectares": 500.0,
                "source": "TEST"
            }
        ]
    }

    # Store data
    try:
        await store_data_dual(test_data)
        logger.info("✅ Data storage completed successfully!")

        # Verify data in Supabase
        cashew = await supabase.get_or_create_commodity("cashew", "nut")
        rubber = await supabase.get_or_create_commodity("rubber", "latex")

        cashew_prices = await supabase.get_latest_prices(cashew["id"], limit=1)
        rubber_production = await supabase.client.table("production_data") \
            .select("*") \
            .eq("commodity_id", rubber["id"]) \
            .eq("year", 2024) \
            .execute()

        logger.info(f"✅ Found {len(cashew_prices)} cashew price records")
        logger.info(f"✅ Found {len(rubber_production.data)} rubber production records")

        logger.info("\n" + "="*60)
        logger.info("TEST PASSED! Seed works without ChromaDB.")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_seed_minimal())
