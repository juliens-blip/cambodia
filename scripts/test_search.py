"""Test script for semantic search API."""
import httpx
import json

API_URL = "https://cambodia.up.railway.app"

# Note: This tests via the Streamlit proxy, may not work directly
# We need to test internally

print("Testing search endpoint...")
print("This script should be run on the Railway container")
print()
print("To test manually, use curl:")
print('curl -X POST "http://127.0.0.1:8000/api/v1/search" \')
print('  -H "Content-Type: application/json" \')
print('  -d \'{"query": "cashew market", "top_k": 5, "similarity_threshold": 0.3}\'')
