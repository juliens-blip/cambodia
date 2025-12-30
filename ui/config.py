"""Configuration for Streamlit UI."""
import os

# API Base URL - use environment variable or default to localhost for dev
# In production, set API_BASE_URL to the Railway API service URL
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Ensure no trailing slash
if API_BASE_URL.endswith("/"):
    API_BASE_URL = API_BASE_URL[:-1]

# Common API endpoints
SEARCH_URL = f"{API_BASE_URL}/api/v1/search"
RAG_URL = f"{API_BASE_URL}/api/v1/rag/query"
HISTORY_URL = f"{API_BASE_URL}/api/v1/history"
STATS_URL = f"{API_BASE_URL}/api/v1/stats"
TRENDS_URL = f"{API_BASE_URL}/api/v1/trends"
TRENDS_SUMMARY_URL = f"{API_BASE_URL}/api/v1/trends/summary"
ALERTS_URL = f"{API_BASE_URL}/api/v1/trends/alerts"

# Admin endpoints for document indexation
ADMIN_INDEX_URL = f"{API_BASE_URL}/api/v1/admin/index-documents"
ADMIN_STATUS_URL = f"{API_BASE_URL}/api/v1/admin/indexation-status"
ADMIN_CLEAR_URL = f"{API_BASE_URL}/api/v1/admin/clear-embeddings"

def get_api_url(endpoint: str) -> str:
    """Get full API URL for an endpoint."""
    if endpoint.startswith("/"):
        return f"{API_BASE_URL}{endpoint}"
    return f"{API_BASE_URL}/{endpoint}"
