"""Test script for production data collection and seeding."""
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.collectors import ODCCollector, GDriveCollector
from app.config import settings
from app.config_gdrive import GDRIVE_FOLDER_IDS
from app.services import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_odc_collector():
    """Test ODC collector for production data."""
    logger.info("=" * 60)
    logger.info("Testing ODC Collector")
    logger.info("=" * 60)

    collector = ODCCollector(settings.odc_base_url)

    try:
        records = await collector.run()
        logger.info(f"✅ ODC collector returned {len(records)} records")

        # Show sample records
        for i, record in enumerate(records[:3]):
            logger.info(f"Sample {i+1}: {record.get('commodity')} - {record.get('province')} - {record.get('year')}")
            if record.get('production_tons'):
                logger.info(f"  Production: {record.get('production_tons')} tons")
            if record.get('area_hectares'):
                logger.info(f"  Area: {record.get('area_hectares')} ha")

        return records

    except Exception as e:
        logger.error(f"❌ ODC collector failed: {e}")
        return []


async def test_gdrive_collector():
    """Test Google Drive collector for production data."""
    logger.info("=" * 60)
    logger.info("Testing Google Drive Collector")
    logger.info("=" * 60)

    collector = GDriveCollector(
        api_key=settings.google_drive_api_key,
        folder_ids=GDRIVE_FOLDER_IDS
    )

    try:
        records = await collector.run()
        logger.info(f"✅ GDrive collector returned {len(records)} records")

        # Count by type
        documents = [r for r in records if r.get("type") == "document"]
        production = [r for r in records if "year" in r and "province" in r]

        logger.info(f"  Documents: {len(documents)}")
        logger.info(f"  Production records: {len(production)}")

        # Show sample production records
        for i, record in enumerate(production[:3]):
            logger.info(f"Sample {i+1}: {record.get('commodity')} - {record.get('province')} - {record.get('year')}")
            if record.get('production_tons'):
                logger.info(f"  Production: {record.get('production_tons')} tons")
            if record.get('area_hectares'):
                logger.info(f"  Area: {record.get('area_hectares')} ha")
            logger.info(f"  Method: {record.get('metadata', {}).get('extracted_method')}")

        return records

    except Exception as e:
        logger.error(f"❌ GDrive collector failed: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_supabase_upsert():
    """Test Supabase upsert for production data."""
    logger.info("=" * 60)
    logger.info("Testing Supabase Production Upsert")
    logger.info("=" * 60)

    supabase = SupabaseService(
        url=settings.supabase_url,
        key=settings.supabase_key
    )

    # Get or create cashew commodity
    cashew = await supabase.get_or_create_commodity("cashew", "nut")
    logger.info(f"✅ Cashew commodity ID: {cashew['id']}")

    # Test data
    test_record = {
        "commodity_id": cashew["id"],
        "year": 2023,
        "province": "Kampong Cham",
        "production_tons": 1500.0,
        "area_hectares": 750.0,
        "source": "TEST"
    }

    try:
        # First upsert
        result1 = await supabase.upsert_production(test_record)
        logger.info(f"✅ First upsert successful: {result1['id']}")

        # Second upsert (should update, not create duplicate)
        test_record["production_tons"] = 1600.0  # Changed value
        result2 = await supabase.upsert_production(test_record)
        logger.info(f"✅ Second upsert successful: {result2['id']}")

        if result1["id"] == result2["id"]:
            logger.info("✅ UPSERT working correctly - same ID returned")
        else:
            logger.warning("⚠️ UPSERT may have created duplicate - different IDs")

        # Clean up test record
        # (Optional: delete the test record)

        return True

    except Exception as e:
        logger.error(f"❌ Supabase upsert failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("🧪 Starting Production Data Collection Tests")
    logger.info("")

    # Test 1: ODC Collector
    odc_records = await test_odc_collector()
    logger.info("")

    # Test 2: Google Drive Collector
    gdrive_records = await test_gdrive_collector()
    logger.info("")

    # Test 3: Supabase Upsert
    upsert_ok = await test_supabase_upsert()
    logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"ODC Records: {len(odc_records)}")
    logger.info(f"GDrive Records: {len(gdrive_records)}")
    logger.info(f"Supabase Upsert: {'✅ PASS' if upsert_ok else '❌ FAIL'}")
    logger.info("")

    if odc_records and gdrive_records and upsert_ok:
        logger.info("✅ All tests passed!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Apply migration: scripts/migrations/002_add_unique_constraint_production.sql")
        logger.info("2. Run seed: python scripts/seed_collectors.py --include-odc")
        logger.info("3. Check production table in Supabase Dashboard")
    else:
        logger.warning("⚠️ Some tests failed - review errors above")


if __name__ == "__main__":
    asyncio.run(main())
