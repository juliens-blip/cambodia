"""
Trigger Market Analysis Immediately
Calls Railway API to force a new analysis for both commodities
"""
import httpx
import sys
import io

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "https://cambodia.up.railway.app/api/v1/trends/analyze"

def trigger_analysis(commodity: str):
    """Trigger analysis for a commodity"""
    print(f"\n🚀 Triggering analysis for {commodity}...")

    try:
        with httpx.Client(timeout=60.0, verify=False) as client:
            response = client.post(
                f"{API_URL}/{commodity}",
                params={"force_refresh": "true"}
            )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {commodity.upper()} analysis completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Tweet count: {result.get('tweet_count', 0)}")
            print(f"   Updated: {result.get('updated_at', 'N/A')}")
            return True
        else:
            print(f"❌ {commodity.upper()} analysis failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Error analyzing {commodity}: {e}")
        return False

def main():
    """Trigger analysis for both commodities"""
    print("=" * 60)
    print("MARKET ANALYSIS TRIGGER - Cambodia Agri Analytics")
    print("=" * 60)

    commodities = ["cashew", "rubber"]
    success_count = 0

    for commodity in commodities:
        if trigger_analysis(commodity):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: {success_count}/{len(commodities)} analyses completed")
    print("=" * 60)

    if success_count == len(commodities):
        print("\n✅ All analyses successful! Check Market Trends UI.")
        sys.exit(0)
    else:
        print("\n⚠️ Some analyses failed. Check Railway logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
