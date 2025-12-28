"""Apply pgvector migration (003) to Supabase."""
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

async def apply_migration():
    """Apply pgvector migration SQL."""
    print("=" * 80)
    print("Applying pgvector Migration (003) to Supabase")
    print("=" * 80)

    # Read migration file
    migration_file = "supabase/migrations/003_pgvector_setup.sql"

    print(f"\n1️⃣ Reading migration file: {migration_file}")
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        print(f"   ✅ Migration loaded ({len(sql)} chars)")
    except Exception as e:
        print(f"   ❌ Error reading migration: {e}")
        return False

    # Initialize Supabase
    print("\n2️⃣ Connecting to Supabase...")
    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        print(f"   ✅ Connected to {settings.supabase_url}")
    except Exception as e:
        print(f"   ❌ Error connecting: {e}")
        return False

    # Execute migration
    print("\n3️⃣ Executing migration SQL...")
    print("   NOTE: This may take 30-60 seconds (creating HNSW index)...")

    try:
        # Execute raw SQL via RPC
        result = supabase.client.rpc('exec_sql', {'sql': sql}).execute()
        print("   ✅ Migration executed successfully!")

        if result.data:
            print(f"\n   Result: {result.data}")

    except Exception as e:
        error_msg = str(e)

        # Check if it's because exec_sql RPC doesn't exist
        if 'function public.exec_sql' in error_msg.lower() or 'does not exist' in error_msg.lower():
            print("\n   ⚠️ RPC exec_sql not available - Using manual execution instead")
            print("\n" + "=" * 80)
            print("📋 MANUAL MIGRATION INSTRUCTIONS")
            print("=" * 80)
            print("\n1. Go to Supabase Dashboard: https://supabase.com/dashboard")
            print(f"2. Select your project: {settings.supabase_url}")
            print("3. Navigate to: SQL Editor (left sidebar)")
            print("4. Click: New Query")
            print("5. Copy the SQL from: supabase/migrations/003_pgvector_setup.sql")
            print("6. Paste into SQL Editor")
            print("7. Click: Run (or press Ctrl+Enter)")
            print("8. Verify success messages appear")
            print("\n" + "=" * 80)
            print("\n✅ After completing manual migration, run verification:")
            print("   python scripts/verify_pgvector_setup.py")
            print("=" * 80)
            return False
        else:
            print(f"   ❌ Error executing migration: {error_msg}")
            print("\n   Try manual execution (see above)")
            return False

    return True

async def main():
    """Main execution."""
    success = await apply_migration()

    if success:
        print("\n" + "=" * 80)
        print("✅ Migration 003 Applied Successfully!")
        print("=" * 80)
        print("\nNext step: Verify setup")
        print("   python scripts/verify_pgvector_setup.py")
    else:
        print("\n" + "=" * 80)
        print("⚠️ Automatic Migration Failed - Manual Step Required")
        print("=" * 80)
        print("\nPlease follow the manual instructions above.")

if __name__ == "__main__":
    asyncio.run(main())
