"""Query and display all context documents."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService


async def query_context_docs():
    """Query all context documents."""
    print("Querying context documents...\n")

    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    # Get all context documents
    all_docs = await supabase.get_context_documents(limit=100)

    print(f"Total context documents: {len(all_docs)}\n")

    # Group by source
    by_source = {}
    for doc in all_docs:
        source = doc.get('source', 'Unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(doc)

    for source, docs in by_source.items():
        print(f"\n{source}: {len(docs)} documents")
        print("-" * 80)
        for doc in docs:
            title = doc.get('title', 'Untitled')
            chars = doc.get('char_count', 0)
            commodity = doc.get('commodity', 'N/A')
            method = doc.get('extraction_method', 'N/A')
            print(f"  - {title[:60]:60} | {chars:>6} chars | {commodity:8} | {method}")

    # Calculate total characters
    total_chars = sum(doc.get('char_count', 0) for doc in all_docs)
    print(f"\n{'='*80}")
    print(f"Total characters stored: {total_chars:,}")
    print(f"Average chars per document: {total_chars // len(all_docs) if all_docs else 0:,}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(query_context_docs())
