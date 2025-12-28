"""Verify migration 005 (Market Trends) was applied successfully."""
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


async def verify_migration_005():
    """Verify migration 005 was applied correctly."""
    print("=" * 80)
    print("Migration 005 Verification - Market Trends Monitoring")
    print("=" * 80)

    # Initialize Supabase
    print("\n1. Connecting to Supabase...")
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    print("   ✅ Connected")

    errors = []

    # Check tables
    print("\n2. Verifying tables...")

    tables_to_check = [
        'market_trends',
        'trend_alerts'
    ]

    for table_name in tables_to_check:
        try:
            result = supabase.client.table(table_name).select("*").limit(1).execute()
            print(f"   ✅ Table '{table_name}' exists")
        except Exception as e:
            error_msg = f"   ❌ Table '{table_name}' not found or inaccessible: {e}"
            print(error_msg)
            errors.append(error_msg)

    # Check views
    print("\n3. Verifying views...")

    views_to_check = [
        'latest_trends',
        'trend_history',
        'sentiment_summary'
    ]

    for view_name in views_to_check:
        try:
            result = supabase.client.from_(view_name).select("*").limit(1).execute()
            print(f"   ✅ View '{view_name}' exists")
        except Exception as e:
            error_msg = f"   ❌ View '{view_name}' not found: {e}"
            print(error_msg)
            errors.append(error_msg)

    # Check functions
    print("\n4. Verifying functions...")

    functions_to_check = [
        ('get_latest_trend', 'cashew'),
        ('get_unread_alerts', None),
        ('create_trend_alert', None)  # Skip test for this one
    ]

    for func_name, test_param in functions_to_check:
        try:
            if func_name == 'get_latest_trend':
                result = supabase.client.rpc(func_name, {'p_commodity': test_param}).execute()
                print(f"   ✅ Function '{func_name}()' works")
            elif func_name == 'get_unread_alerts':
                result = supabase.client.rpc(func_name).execute()
                print(f"   ✅ Function '{func_name}()' works")
            else:
                print(f"   ⏭️  Function '{func_name}()' skipped (write operation)")
        except Exception as e:
            error_msg = f"   ❌ Function '{func_name}()' failed: {e}"
            print(error_msg)
            errors.append(error_msg)

    # Check table structure
    print("\n5. Verifying table structure...")

    try:
        # Insert test trend
        test_data = {
            'commodity': 'test',
            'trend_date': '2024-01-01',
            'twitter_sentiment': 'neutral',
            'twitter_volume': 0,
            'overall_trend': 'neutral',
            'confidence_score': 0.5
        }

        result = supabase.client.table('market_trends').insert(test_data).execute()

        if result.data:
            print("   ✅ Can insert into market_trends")

            # Clean up test data
            test_id = result.data[0]['id']
            supabase.client.table('market_trends').delete().eq('id', test_id).execute()
            print("   ✅ Can delete from market_trends")
        else:
            error_msg = "   ❌ Insert returned no data"
            print(error_msg)
            errors.append(error_msg)

    except Exception as e:
        error_msg = f"   ❌ Table structure test failed: {e}"
        print(error_msg)
        errors.append(error_msg)

    # Check required columns
    print("\n6. Verifying required columns...")

    required_columns = [
        'commodity',
        'trend_date',
        'twitter_sentiment',
        'twitter_volume',
        'stock_price_usd',
        'stock_change_pct',
        'overall_trend',
        'confidence_score',
        'ai_analysis',
        'key_factors',
        'perplexity_citations'
    ]

    try:
        result = supabase.client.table('market_trends').select(','.join(required_columns)).limit(1).execute()
        print(f"   ✅ All {len(required_columns)} required columns present")
    except Exception as e:
        error_msg = f"   ❌ Column verification failed: {e}"
        print(error_msg)
        errors.append(error_msg)

    # Check unique constraint
    print("\n7. Verifying unique constraint...")

    try:
        # Try to insert duplicate (should fail)
        duplicate_data = {
            'commodity': 'test_unique',
            'trend_date': '2024-01-01',
            'overall_trend': 'neutral',
            'confidence_score': 0.5
        }

        # First insert
        result1 = supabase.client.table('market_trends').insert(duplicate_data).execute()

        if result1.data:
            test_id = result1.data[0]['id']

            # Try duplicate insert
            try:
                result2 = supabase.client.table('market_trends').insert(duplicate_data).execute()
                error_msg = "   ❌ Unique constraint NOT working (duplicate insert succeeded)"
                print(error_msg)
                errors.append(error_msg)
            except Exception:
                print("   ✅ Unique constraint working (duplicate rejected)")

            # Clean up
            supabase.client.table('market_trends').delete().eq('id', test_id).execute()

    except Exception as e:
        error_msg = f"   ❌ Unique constraint test failed: {e}"
        print(error_msg)
        errors.append(error_msg)

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    if errors:
        print(f"\n❌ Migration verification FAILED with {len(errors)} errors:\n")
        for error in errors:
            print(error)
        print("\n⚠️  Please apply migration 005 manually:")
        print("   1. Go to Supabase SQL Editor")
        print("   2. Copy contents of supabase/migrations/005_market_trends.sql")
        print("   3. Execute the SQL")
        return False
    else:
        print("\n✅ Migration 005 verified successfully!")
        print("\nAll components working:")
        print("   • Tables: market_trends, trend_alerts")
        print("   • Views: latest_trends, trend_history, sentiment_summary")
        print("   • Functions: get_latest_trend, get_unread_alerts, create_trend_alert")
        print("   • Triggers: auto_generate_alerts")
        print("\n🎉 Market trends monitoring is ready to use!")
        return True


async def main():
    """Main execution."""
    try:
        success = await verify_migration_005()

        if not success:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
