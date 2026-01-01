"""
Trigger Market Analysis Immediately
Calls Railway admin API to force a new analysis for both commodities
"""
import httpx
import sys
import io

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "https://cambodia.up.railway.app/api/v1/admin/trigger-analysis"

def trigger_analysis(commodity: str = None):
    """Trigger analysis for commodities

    Args:
        commodity: 'cashew', 'rubber', or None for both
    """
    comm_name = commodity.upper() if commodity else "BOTH"
    print(f"\n🚀 Triggering analysis for {comm_name}...")

    try:
        with httpx.Client(timeout=120.0, verify=False) as client:
            response = client.post(
                API_URL,
                params={
                    "commodity": commodity,
                    "force_refresh": "true"
                }
            )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis trigger successful!")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")

            for r in result.get('results', []):
                comm = r.get('commodity', 'unknown').upper()
                status = r.get('status')
                if status == 'success':
                    print(f"   ✅ {comm}: {r.get('tweet_count', 0)} tweets, updated {r.get('updated_at', 'N/A')}")
                else:
                    print(f"   ❌ {comm}: {r.get('error', 'Unknown error')}")

            return result.get('status') == 'success'
        else:
            print(f"❌ Analysis failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Error triggering analysis: {e}")
        return False

def main():
    """Trigger analysis for both commodities"""
    print("=" * 60)
    print("MARKET ANALYSIS TRIGGER - Cambodia Agri Analytics")
    print("Admin Endpoint (No Rate Limit)")
    print("=" * 60)

    # Trigger both commodities at once
    success = trigger_analysis(commodity=None)

    print("\n" + "=" * 60)
    if success:
        print("✅ Analysis complete! Check Market Trends UI.")
        print("   https://cambodia.up.railway.app/Market_Trends")
        print("=" * 60)
        sys.exit(0)
    else:
        print("⚠️ Analysis failed. Check Railway logs.")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
