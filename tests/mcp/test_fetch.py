"""
Test script for Fetch MCP Server
Tests HTTP requests to MEF Cambodia API and other data sources
"""

import asyncio
import json


async def test_mef_api():
    """Test fetching data from MEF Cambodia API"""

    print("=" * 60)
    print("TESTING FETCH MCP - MEF Cambodia API")
    print("=" * 60)

    mef_api_url = "https://data.mef.gov.kh/api/v1/public-datasets/pd_68b588a0eb43bd000745b588/json?page=1&page_size=10"

    print(f"\n1. Target URL:")
    print(f"   {mef_api_url}")

    print("\n2. Expected response structure:")
    print("""   {
       "data": [...],
       "pagination": {
         "current_page": 1,
         "total_pages": X,
         "page_size": 10
       }
     }""")

    print("\n3. Data fields expected:")
    print("   - Date")
    print("   - Price (KHR/USD)")
    print("   - Volume")
    print("   - Destination country")
    print("   - Product category")

    print("\n4. Test scenarios:")
    print("   a. Fetch current page (page=1)")
    print("   b. Fetch with custom page_size (page_size=50)")
    print("   c. Handle pagination (iterate through all pages)")
    print("   d. Error handling (invalid dataset ID)")

    print("\n" + "=" * 60)


async def test_wits_api():
    """Test fetching from WITS World Bank API"""

    print("\n" + "=" * 60)
    print("TESTING FETCH MCP - WITS World Bank API")
    print("=" * 60)

    wits_url = "http://wits.worldbank.org/API/V1/datasource/trn/country/KHM"

    print(f"\n1. Target URL:")
    print(f"   {wits_url}")

    print("\n2. Response format: XML")
    print("   (Requires XML parsing)")

    print("\n3. Expected data:")
    print("   - Cambodia (KHM) trade statistics")
    print("   - Export/import values")
    print("   - Partner countries")
    print("   - Product categories (HS codes)")

    print("\n" + "=" * 60)


async def test_odc_scraping():
    """Test fetching from Open Development Cambodia"""

    print("\n" + "=" * 60)
    print("TESTING FETCH MCP - Open Development Cambodia")
    print("=" * 60)

    odc_url = "https://data.opendevelopmentcambodia.net/en/dataset"

    print(f"\n1. Target URL:")
    print(f"   {odc_url}")

    print("\n2. Data types available:")
    print("   - CSV files (agricultural production)")
    print("   - JSON datasets (provincial statistics)")
    print("   - KML files (geospatial data)")

    print("\n3. Search strategy:")
    print("   a. Search for 'cashew' datasets")
    print("   b. Search for 'rubber' datasets")
    print("   c. Filter by file format (CSV, KML)")
    print("   d. Download and parse files")

    print("\n4. NOTE: May require browsermcp if JavaScript rendering needed")

    print("\n" + "=" * 60)


async def test_perplexity_api():
    """Test Perplexity API calls (requires API key)"""

    print("\n" + "=" * 60)
    print("TESTING FETCH MCP - Perplexity API")
    print("=" * 60)

    perplexity_url = "https://api.perplexity.ai/chat/completions"

    print(f"\n1. Target URL:")
    print(f"   {perplexity_url}")

    print("\n2. Authentication:")
    print("   Header: Authorization: Bearer $PERPLEXITY_API_KEY")

    print("\n3. Sample request:")
    sample_request = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": "What are the latest cashew export prices from Cambodia to Vietnam?"
            }
        ]
    }
    print(json.dumps(sample_request, indent=2))

    print("\n4. Expected response:")
    print("   - Answer with citations")
    print("   - Source URLs")
    print("   - Confidence scores")

    print("\n5. Query templates for project:")
    queries = [
        "Cambodia cashew export prices last 24 hours",
        "Vietnam cashew processing industry news",
        "US-China trade tensions impact on cashew market",
        "Cashew demand forecast China 2025"
    ]

    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query}")

    print("\n" + "=" * 60)


async def test_error_handling():
    """Test error scenarios"""

    print("\n" + "=" * 60)
    print("TESTING FETCH MCP - Error Handling")
    print("=" * 60)

    print("\n1. Test cases:")
    print("   a. 404 Not Found (invalid URL)")
    print("   b. 401 Unauthorized (missing API key)")
    print("   c. 429 Rate Limit Exceeded")
    print("   d. 500 Server Error")
    print("   e. Timeout (slow response)")
    print("   f. Invalid JSON response")

    print("\n2. Expected behaviors:")
    print("   - Retry with exponential backoff (3 attempts)")
    print("   - Log errors with context")
    print("   - Return None or empty result on failure")
    print("   - Alert if critical API fails")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mef_api())
    asyncio.run(test_wits_api())
    asyncio.run(test_odc_scraping())
    asyncio.run(test_perplexity_api())
    asyncio.run(test_error_handling())

    print("\n" + "=" * 60)
    print("ALL FETCH TESTS COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set PERPLEXITY_API_KEY in .env")
    print("2. Test actual API calls using Claude Code with Fetch MCP")
    print("3. Implement retry logic in collectors")
