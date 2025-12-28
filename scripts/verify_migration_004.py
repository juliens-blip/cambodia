"""Verify migration 004 was applied correctly."""
import sys
import os
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService


def verify_migration():
    """Verify migration 004."""

    print("=" * 80)
    print("Verifying Migration 004: Conversation History & Usage Tracking")
    print("=" * 80)

    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    checks = {
        "conversation_history table": False,
        "usage_logs table": False,
        "query_cache table": False,
        "budget_tracking view": False,
        "get_current_month_budget function": False
    }

    # Check 1: conversation_history table
    print("\n1. Checking conversation_history table...")
    try:
        result = supabase.client.table("conversation_history").select("id").limit(1).execute()
        checks["conversation_history table"] = True
        print("   ✅ conversation_history table exists")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check 2: usage_logs table
    print("\n2. Checking usage_logs table...")
    try:
        result = supabase.client.table("usage_logs").select("id").limit(1).execute()
        checks["usage_logs table"] = True
        print("   ✅ usage_logs table exists")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check 3: query_cache table
    print("\n3. Checking query_cache table...")
    try:
        result = supabase.client.table("query_cache").select("id").limit(1).execute()
        checks["query_cache table"] = True
        print("   ✅ query_cache table exists")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check 4: budget_tracking view
    print("\n4. Checking budget_tracking view...")
    try:
        result = supabase.client.table("budget_tracking").select("*").limit(1).execute()
        checks["budget_tracking view"] = True
        print("   ✅ budget_tracking view exists")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check 5: get_current_month_budget function
    print("\n5. Checking get_current_month_budget function...")
    try:
        result = supabase.client.rpc("get_current_month_budget").execute()
        checks["get_current_month_budget function"] = True
        print("   ✅ get_current_month_budget function exists")

        # Show budget stats
        if result.data:
            stats = result.data[0]
            print(f"\n   Current Month Budget:")
            print(f"      - Total queries: {stats['total_queries']}")
            print(f"      - RAG queries: {stats['rag_queries']}")
            print(f"      - Total cost: ${stats['total_cost_usd']:.2f}")
            print(f"      - Budget limit: ${stats['budget_limit_usd']:.2f}")
            print(f"      - Remaining: ${stats['budget_remaining_usd']:.2f}")
            print(f"      - Utilization: {stats['budget_utilization_pct']:.1f}%")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    passed = sum(checks.values())
    total = len(checks)

    print(f"\nChecks passed: {passed}/{total}")

    for check, status in checks.items():
        status_icon = "✅ PASS" if status else "❌ FAIL"
        print(f"   {status_icon} - {check}")

    print("\n" + "=" * 80)

    if passed == total:
        print("✅ ALL CHECKS PASSED - Migration 004 Complete!")
        print("=" * 80)
        print("\nNext: Start API server and test endpoints")
        print("   python -m uvicorn app.main:app --reload")
        return True
    else:
        print("❌ SOME CHECKS FAILED - Please review errors above")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
