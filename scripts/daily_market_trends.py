"""Daily market trends analysis script.

Run this script daily (via cron/scheduler) to analyze Twitter/X and stock market trends.

Schedule:
- Recommended: Once per day at 9:00 AM (after markets open)
- Cron: 0 9 * * * python scripts/daily_market_trends.py

Cost: ~$0.01 per day (2 commodities × $0.005)
"""
import asyncio
import sys
import os
import io
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.perplexity_service import PerplexityService
from app.services.market_trends_service import MarketTrendsService


async def run_daily_analysis():
    """Run daily market trends analysis."""

    print("=" * 80)
    print("Daily Market Trends Analysis")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Initialize services
    print("\n1. Initializing services...")
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=1000
    )
    trends = MarketTrendsService(supabase, perplexity)
    print("   Services initialized")

    # Commodities to analyze
    commodities = ['cashew', 'rubber']

    results = []

    # Analyze each commodity
    for i, commodity in enumerate(commodities, 1):
        print(f"\n{i}. Analyzing {commodity} market trends...")
        print(f"   - Searching Twitter/X (last 48h)...")
        print(f"   - Fetching stock market data...")
        print(f"   - Generating AI analysis...")

        try:
            result = await trends.analyze_and_store_trends(
                commodity=commodity,
                force_refresh=False  # Skip if already analyzed today
            )

            results.append(result)

            if result['status'] == 'success':
                data = result['data']
                print(f"   COMPLETED:")
                print(f"      - Sentiment: {data.get('twitter_sentiment', 'N/A')}")
                print(f"      - Overall trend: {data.get('overall_trend', 'N/A')}")
                print(f"      - Confidence: {data.get('confidence_score', 0):.2f}")
                print(f"      - Tweet volume: {data.get('twitter_volume', 0)}")
                if data.get('stock_change_pct'):
                    print(f"      - Price change: {data.get('stock_change_pct'):+.2f}%")

            elif result['status'] == 'exists':
                print(f"   SKIPPED: Already analyzed today")

            else:
                print(f"   ERROR: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"   ERROR: {e}")
            results.append({'status': 'error', 'error': str(e)})

    # Check for alerts
    print("\n3. Checking for market alerts...")
    try:
        alerts = await trends.get_unread_alerts()

        if alerts:
            print(f"   ALERTS: {len(alerts)} unread alerts")
            for alert in alerts[:5]:  # Show first 5
                severity_icon = {
                    'low': 'ℹ️',
                    'medium': '⚠️',
                    'high': '⚠️',
                    'critical': '🚨'
                }.get(alert['severity'], '•')

                print(f"   {severity_icon} [{alert['severity'].upper()}] {alert['message']}")

        else:
            print(f"   No new alerts")

    except Exception as e:
        print(f"   ERROR checking alerts: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("DAILY ANALYSIS SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'exists')
    failed = sum(1 for r in results if r['status'] == 'error')

    print(f"\nCommodities analyzed: {len(commodities)}")
    print(f"   - Success: {successful}")
    print(f"   - Skipped (already done): {skipped}")
    print(f"   - Failed: {failed}")

    # Budget info
    cost_per_analysis = 0.005
    cost_today = successful * cost_per_analysis

    print(f"\nCost:")
    print(f"   - Today: ${cost_today:.3f}")
    print(f"   - Monthly estimate: ${cost_today * 30:.2f} (if run daily)")

    # Perplexity budget
    perplexity_stats = perplexity.get_stats()
    print(f"\nPerplexity Budget:")
    print(f"   - Used this month: {perplexity_stats['requests_used']}/{perplexity_stats['rate_limit']}")
    print(f"   - Remaining: {perplexity_stats['requests_remaining']}")
    print(f"   - Utilization: {perplexity_stats['utilization_percentage']:.1f}%")

    print("\n" + "=" * 80)

    if failed > 0:
        print("⚠️ Some analyses failed - check errors above")
        return False
    else:
        print("✅ Daily analysis complete!")
        return True


async def main():
    """Main execution."""
    try:
        success = await run_daily_analysis()

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
