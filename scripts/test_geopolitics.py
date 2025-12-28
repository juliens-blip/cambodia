"""Test geopolitical analysis with Perplexity API."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.perplexity_service import PerplexityService


async def test_geopolitics():
    """Test geopolitical analysis for cashew and rubber."""
    print("=" * 80)
    print("🌍 Testing Perplexity Geopolitical Analysis")
    print("=" * 80)

    # Initialize Perplexity service
    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=settings.perplexity_max_requests_per_month
    )

    print(f"\n📊 Initial stats: {perplexity.get_stats()}\n")

    # Test 1: Cashew geopolitics
    print("=" * 80)
    print("🥜 CASHEW - Geopolitical Analysis")
    print("=" * 80)

    try:
        cashew_geo = await perplexity.research_geopolitics("cashew")

        print(f"\n✅ Query successful!")
        print(f"   Commodity: {cashew_geo['commodity']}")
        print(f"   Query Type: {cashew_geo['query_type']}")
        print(f"   Created: {cashew_geo['created_at']}")
        print(f"   Model: {cashew_geo['metadata']['model']}")
        print(f"   Tokens: {cashew_geo['metadata'].get('tokens_used', 'N/A')}")

        print(f"\n📝 RESPONSE (first 500 chars):")
        print("-" * 80)
        print(cashew_geo['response_text'][:500])
        print("...")
        print("-" * 80)

        print(f"\n🔗 CITATIONS ({len(cashew_geo['citations'])} sources):")
        for i, citation in enumerate(cashew_geo['citations'][:5], 1):
            print(f"   [{i}] {citation}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Rubber geopolitics
    print("\n" + "=" * 80)
    print("🛞 RUBBER - Geopolitical Analysis")
    print("=" * 80)

    try:
        rubber_geo = await perplexity.research_geopolitics("rubber")

        print(f"\n✅ Query successful!")
        print(f"   Commodity: {rubber_geo['commodity']}")
        print(f"   Query Type: {rubber_geo['query_type']}")
        print(f"   Created: {rubber_geo['created_at']}")
        print(f"   Model: {rubber_geo['metadata']['model']}")
        print(f"   Tokens: {rubber_geo['metadata'].get('tokens_used', 'N/A')}")

        print(f"\n📝 RESPONSE (first 500 chars):")
        print("-" * 80)
        print(rubber_geo['response_text'][:500])
        print("...")
        print("-" * 80)

        print(f"\n🔗 CITATIONS ({len(rubber_geo['citations'])} sources):")
        for i, citation in enumerate(rubber_geo['citations'][:5], 1):
            print(f"   [{i}] {citation}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Final stats
    print("\n" + "=" * 80)
    print("📊 Final Statistics")
    print("=" * 80)
    stats = perplexity.get_stats()
    print(f"   Requests used: {stats['requests_used']}/{stats['rate_limit']}")
    print(f"   Remaining: {stats['requests_remaining']}")
    print(f"   Utilization: {stats['utilization_percentage']:.2f}%")
    print("=" * 80)

    print("\n✅ Test complete! Geopolitical analysis is working.")
    print("\n💡 Key insights to expect:")
    print("   - China demand trends (major buyer)")
    print("   - Vietnam/Thailand competition (regional producers)")
    print("   - Trade policy changes (tariffs, restrictions)")
    print("   - Global harvest forecasts (supply impact)")
    print("   - Manufacturing output trends (processed products)")


if __name__ == "__main__":
    asyncio.run(test_geopolitics())
