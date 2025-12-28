"""Apply migration 004 - Conversation History & Usage Tracking."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService


def apply_migration():
    """Apply migration 004."""

    print("=" * 80)
    print("Applying Migration 004: Conversation History & Usage Tracking")
    print("=" * 80)

    # Read migration file
    migration_path = "supabase/migrations/004_conversation_history.sql"

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        print(f"\nMigration file: {migration_path}")
        print(f"SQL size: {len(sql)} characters")

    except FileNotFoundError:
        print(f"ERROR: Migration file not found: {migration_path}")
        return False

    # Instructions for manual application
    print("\n" + "=" * 80)
    print("MANUAL APPLICATION REQUIRED")
    print("=" * 80)

    print("\nPlease apply this migration manually via Supabase SQL Editor:")
    print("\n1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Navigate to: SQL Editor")
    print("4. Create a new query")
    print("5. Copy/paste the SQL below")
    print("6. Click 'Run'")

    print("\n" + "=" * 80)
    print("SQL TO EXECUTE:")
    print("=" * 80)
    print("\n" + sql[:500] + "\n...\n")

    print("\n" + "=" * 80)
    print("After applying the migration, verify with:")
    print("python scripts/verify_migration_004.py")
    print("=" * 80)

    return True


if __name__ == "__main__":
    apply_migration()
