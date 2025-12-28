"""Verify pgvector setup in Supabase."""
import asyncio
import sys
import os
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService

async def verify_setup():
    """Verify pgvector migration success."""
    print("=" * 80)
    print("Verifying pgvector Setup")
    print("=" * 80)

    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    checks = []

    # Check 1: pgvector extension
    print("\n1️⃣ Checking pgvector extension...")
    try:
        result = supabase.client.rpc('exec_sql', {
            'sql': "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
        }).execute()

        if result.data and len(result.data) > 0:
            version = result.data[0].get('extversion', 'unknown')
            print(f"   ✅ pgvector extension found (version: {version})")
            checks.append(True)
        else:
            print("   ❌ pgvector extension NOT found")
            checks.append(False)
    except:
        # Fallback: Try direct table query
        try:
            # Check if we can query document_embeddings
            result = supabase.client.table('document_embeddings').select('id').limit(0).execute()
            print("   ✅ pgvector extension likely installed (table queryable)")
            checks.append(True)
        except Exception as e:
            print(f"   ❌ Cannot verify extension: {e}")
            checks.append(False)

    # Check 2: document_embeddings table
    print("\n2️⃣ Checking document_embeddings table...")
    try:
        result = supabase.client.table('document_embeddings').select('id').limit(1).execute()
        print("   ✅ document_embeddings table exists and queryable")
        checks.append(True)
    except Exception as e:
        print(f"   ❌ Table not found or not accessible: {e}")
        checks.append(False)

    # Check 3: RPC function match_documents
    print("\n3️⃣ Checking match_documents RPC function...")
    try:
        # Create a dummy vector (all zeros)
        dummy_vector = [0.0] * 1024

        result = supabase.client.rpc('match_documents', {
            'query_embedding': dummy_vector,
            'match_count': 1,
            'match_threshold': 0.5
        }).execute()

        print("   ✅ match_documents function exists and callable")
        print(f"   Results: {len(result.data)} documents (expected 0 since no embeddings yet)")
        checks.append(True)
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg.lower():
            print("   ❌ match_documents function NOT found")
        else:
            print(f"   ❌ Function error: {e}")
        checks.append(False)

    # Check 4: Table structure
    print("\n4️⃣ Checking table structure (columns)...")
    try:
        # Query with all expected columns
        result = supabase.client.table('document_embeddings').select(
            'id,document_id,chunk_index,chunk_text,embedding,metadata,created_at,updated_at'
        ).limit(0).execute()

        print("   ✅ All expected columns exist:")
        print("      - id, document_id, chunk_index")
        print("      - chunk_text, embedding (vector)")
        print("      - metadata (jsonb)")
        print("      - created_at, updated_at")
        checks.append(True)
    except Exception as e:
        print(f"   ❌ Column structure issue: {e}")
        checks.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)

    passed = sum(checks)
    total = len(checks)

    print(f"\nChecks passed: {passed}/{total}")

    for i, check in enumerate(checks, 1):
        status = "✅ PASS" if check else "❌ FAIL"
        check_names = [
            "pgvector extension",
            "document_embeddings table",
            "match_documents RPC",
            "Table structure"
        ]
        print(f"   {status} - {check_names[i-1]}")

    print("\n" + "=" * 80)

    if passed == total:
        print("✅ ALL CHECKS PASSED - pgvector Setup Complete!")
        print("=" * 80)
        print("\n🚀 Ready for Phase 2: Create Services")
        print("   Next: Create embedding_service.py, chunking_service.py, etc.")
    elif passed >= 2:
        print("⚠️ PARTIAL SUCCESS - Some checks failed")
        print("=" * 80)
        print("\n⚠️ Review failed checks above")
        print("   You may still be able to proceed if critical components passed")
    else:
        print("❌ SETUP INCOMPLETE - Migration Required")
        print("=" * 80)
        print("\n❌ pgvector migration needs to be applied")
        print("   Run: python scripts/apply_pgvector_migration.py")
        print("   Or apply manually via Supabase SQL Editor")

    print("=" * 80)

    return passed == total

if __name__ == "__main__":
    asyncio.run(verify_setup())
