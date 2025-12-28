"""Initialize ChromaDB collections.

Creates 5 collections for semantic search:
1. commodity_documents - PDFs/KML from Google Drive
2. perplexity_analyses - Perplexity research results
3. claude_reports - Generated reports
4. commodity_prices - Prices with market context
5. production_data - Production stats with geospatial
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.chromadb_service import ChromaDBService


COLLECTIONS_INFO = {
    "commodity_documents": {
        "description": "PDF and KML documents from Google Drive",
        "purpose": "Semantic search across cashew/rubber documentation",
        "metadata_fields": ["commodity", "file_name", "file_type", "language", "geolocation"],
        "example_query": "cashew production techniques in Kampong Cham"
    },
    "perplexity_analyses": {
        "description": "Perplexity API research results with citations",
        "purpose": "Cache and retrieve market analyses",
        "metadata_fields": ["commodity", "query_type", "created_at", "citations"],
        "example_query": "Vietnam cashew processing impact on Cambodia exports"
    },
    "claude_reports": {
        "description": "Generated market reports (daily/weekly/crisis)",
        "purpose": "Historical scenario matching and trend analysis",
        "metadata_fields": ["commodity", "report_type", "created_at", "insights", "sentiment"],
        "example_query": "price spike due to supply shortage"
    },
    "commodity_prices": {
        "description": "Price data with market context",
        "purpose": "Similar price scenario detection",
        "metadata_fields": ["commodity", "date", "price_usd", "destination", "market_conditions"],
        "example_query": "high Vietnam demand with supply constraints"
    },
    "production_data": {
        "description": "Agricultural production statistics with geospatial data",
        "purpose": "High-yield regions and YoY growth analysis",
        "metadata_fields": ["commodity", "province", "year", "area_hectares", "yield_kg_per_ha"],
        "example_query": "high productivity regions above 900kg per hectare"
    }
}


async def init_collections():
    """Initialize all ChromaDB collections."""
    print("🚀 Starting ChromaDB initialization...")
    print(f"   Host: {settings.chroma_host}")
    print(f"   Port: {settings.chroma_port}")
    print(f"   Persist Path: {settings.chroma_persist_path}")

    try:
        # Create ChromaDB service
        service = ChromaDBService(
            host=settings.chroma_host,
            port=settings.chroma_port,
            persist_path=settings.chroma_persist_path
        )

        print("\n📊 Initializing collections...\n")

        # Initialize collections
        service.init_collections()

        # Display collection info
        print("\n✅ Collections created successfully!\n")
        print("=" * 80)

        for name, info in COLLECTIONS_INFO.items():
            print(f"\n🗂️  Collection: {name}")
            print(f"   Description: {info['description']}")
            print(f"   Purpose: {info['purpose']}")
            print(f"   Metadata: {', '.join(info['metadata_fields'])}")
            print(f"   Example Query: \"{info['example_query']}\"")

        # Get stats
        print("\n" + "=" * 80)
        print("\n📈 Collection Statistics:\n")

        stats = service.get_collection_stats()
        for name, stat in stats.items():
            print(f"   {name:25} → {stat['count']:>5} documents")

        print("\n✅ ChromaDB initialization complete!")
        print("\n💡 Next steps:")
        print("   1. Start importing Google Drive PDFs → commodity_documents")
        print("   2. Enable Perplexity analysis storage → perplexity_analyses")
        print("   3. Configure dual-write: Supabase + ChromaDB for prices/production")

        print("\n🔍 Test semantic search:")
        print("   from app.services.chromadb_service import ChromaDBService")
        print("   service = ChromaDBService()")
        print("   service.init_collections()")
        print("   results = await service.search_documents('cashew production')")

    except Exception as e:
        print(f"\n❌ Error initializing ChromaDB: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure ChromaDB is running:")
        print("      docker run -d -p 8000:8000 chromadb/chroma")
        print("   2. Check host/port in .env file")
        print("   3. Verify network connectivity")
        raise


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Cambodia Agri Analytics - ChromaDB Initialization         ║
║   Semantic Search Layer (5 Collections)                     ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(init_collections())
