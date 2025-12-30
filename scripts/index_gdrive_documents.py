"""
Script d'urgence pour indexer les documents Google Drive.

Ce script:
1. Collecte les documents depuis Google Drive
2. Les stocke dans Supabase context_documents
3. Lance le pipeline daily pour indexer tout

Usage:
    python scripts/index_gdrive_documents.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scheduler.jobs import run_collectors, store_data_dual, init_services
from app.services.supabase_service import SupabaseService
from app.services.chromadb_service import ChromaDBService
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Collecte et indexe les documents Google Drive."""
    logger.info("🚀 Starting Google Drive documents indexation...")

    # Initialize services
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    chromadb = None  # ChromaDB not available on Python 3.14+

    init_services(supabase, chromadb)

    # Step 1: Collect documents from Google Drive
    logger.info("📥 Collecting documents from Google Drive...")
    data = await run_collectors()

    gdrive_data = data.get("gdrive", [])
    logger.info(f"✅ Collected {len(gdrive_data)} records from Google Drive")

    # Step 2: Store in Supabase
    logger.info("💾 Storing documents in Supabase...")
    await store_data_dual(data)

    logger.info("✅ Google Drive documents indexed successfully!")
    logger.info(f"📊 Total records processed: {len(gdrive_data)}")

    # Print summary
    context_docs = [d for d in gdrive_data if d.get("document_type") == "context"]
    logger.info(f"📄 Context documents (PDFs): {len(context_docs)}")

    for doc in context_docs[:5]:  # Show first 5
        logger.info(f"   - {doc.get('title', 'Unknown')}: {doc.get('char_count', 0)} chars")


if __name__ == "__main__":
    asyncio.run(main())
