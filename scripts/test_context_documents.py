"""Test context_documents functionality.

Verifies that:
1. context_documents table exists
2. Can insert/update context documents
3. Can query context documents
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService


async def test_context_documents():
    """Test context documents functionality."""
    print("[TEST] Testing context_documents functionality...")
    print(f"   URL: {settings.supabase_url}\n")

    # Initialize service
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    # Test 1: Check if table exists
    print("[Test 1] Checking if context_documents table exists...")
    try:
        result = supabase.client.table("context_documents").select("id").limit(1).execute()
        print("   [OK] Table exists!")
    except Exception as e:
        print(f"   [ERROR] Table does not exist or error: {e}")
        print("\n[WARNING] Please apply the migration first:")
        print("   python scripts/apply_context_migration.py")
        return

    # Test 2: Insert a test context document
    print("\n[Test 2] Inserting test context document...")
    test_doc = {
        "document_type": "context",
        "source": "TEST",
        "commodity": "cashew",
        "title": "Test Document - Economic Land Concession Report",
        "text_content": "This is a test document containing contextual information about cashew production. " * 10,
        "url": "https://example.com/test.pdf",
        "scraped_at": datetime.utcnow().isoformat(),
        "char_count": 500,
        "extraction_method": "text"
    }

    try:
        result = await supabase.upsert_context_document(test_doc)
        if result:
            print(f"   [OK] Inserted document: {result['title']}")
            print(f"      ID: {result['id']}")
            print(f"      Characters: {result['char_count']}")
            doc_id = result['id']
        else:
            print("   [ERROR] Failed to insert document")
            return
    except Exception as e:
        print(f"   [ERROR] Error inserting: {e}")
        return

    # Test 3: Update the same document (upsert)
    print("\n[Test 3] Updating document (upsert test)...")
    test_doc["text_content"] = "UPDATED: " + test_doc["text_content"]
    test_doc["char_count"] = len(test_doc["text_content"])

    try:
        result = await supabase.upsert_context_document(test_doc)
        if result:
            print(f"   [OK] Updated document: {result['title']}")
            print(f"      New character count: {result['char_count']}")
        else:
            print("   [ERROR] Failed to update document")
    except Exception as e:
        print(f"   [ERROR] Error updating: {e}")

    # Test 4: Query context documents
    print("\n[Test 4] Querying context documents...")
    try:
        docs = await supabase.get_context_documents(source="TEST", limit=10)
        print(f"   [OK] Found {len(docs)} test documents")
        for doc in docs:
            print(f"      - {doc['title'][:50]}... ({doc['char_count']} chars)")
    except Exception as e:
        print(f"   [ERROR] Error querying: {e}")

    # Test 5: Get database stats
    print("\n[Test 5] Checking database stats...")
    try:
        stats = await supabase.get_database_stats()
        print("   [OK] Database statistics:")
        for table, count in stats.items():
            print(f"      {table:20} {count:>6} records")
    except Exception as e:
        print(f"   [ERROR] Error getting stats: {e}")

    # Test 6: Cleanup test data
    print("\n[Test 6] Cleaning up test data...")
    try:
        # Delete test document
        supabase.client.table("context_documents").delete().eq("source", "TEST").execute()
        print("   [OK] Test data cleaned up")
    except Exception as e:
        print(f"   [ERROR] Error cleaning up: {e}")

    print("\n" + "="*80)
    print("[SUCCESS] All tests completed!")
    print("="*80)


if __name__ == "__main__":
    print("""
================================================================
   Cambodia Agri Analytics - Context Documents Test
   Verify context_documents table functionality
================================================================
    """)

    asyncio.run(test_context_documents())
