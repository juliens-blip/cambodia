"""Seed Supabase and ChromaDB from external collectors."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.collectors import GDriveCollector, MEFCollector, WITSCollector, ODCCollector
from app.config import settings
from app.config_gdrive import GDRIVE_FOLDER_IDS
from app.scheduler.jobs import init_services, store_data_dual
from app.services import ChromaDBService, SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Seed data from collectors.")
    parser.add_argument("--include-odc", action="store_true", help="Include ODC placeholder data.")
    parser.add_argument("--skip-chroma", action="store_true", help="Skip ChromaDB storage.")
    return parser.parse_args()


async def run() -> None:
    """Run collectors and store data."""
    args = build_args()

    supabase = SupabaseService(
        url=settings.supabase_url,
        key=settings.supabase_key
    )

    chromadb = None
    if not args.skip_chroma:
        try:
            chromadb = ChromaDBService(
                host=settings.chroma_host,
                port=settings.chroma_port
            )
            chromadb.init_collections()
        except Exception as exc:
            logger.warning("ChromaDB not available, skipping: %s", exc)
            chromadb = None

    init_services(supabase, chromadb)

    collectors = [
        MEFCollector(settings.mef_api_url),
        WITSCollector(settings.wits_api_url),
        GDriveCollector(
            api_key=settings.google_drive_api_key,
            folder_ids=GDRIVE_FOLDER_IDS
        )
    ]

    if args.include_odc:
        collectors.append(ODCCollector(settings.odc_base_url))

    results = await asyncio.gather(
        *[collector.run() for collector in collectors],
        return_exceptions=True
    )

    data = {}
    for collector, result in zip(collectors, results):
        key = collector.source_name.lower()
        if isinstance(result, Exception):
            logger.warning("Collector %s failed: %s", collector.source_name, result)
            data[key] = []
        else:
            data[key] = result

    await store_data_dual(data)

    summary = {key: len(records) for key, records in data.items()}
    logger.info("Seed complete: %s", summary)


if __name__ == "__main__":
    asyncio.run(run())
