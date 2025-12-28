"""Streamlit main dashboard for Cambodia Agri Analytics."""
import os
from datetime import datetime

import httpx
import streamlit as st
from dotenv import load_dotenv

# Page config
st.set_page_config(
    page_title="Cambodia Agri Analytics",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=300)
def get_stats():
    """Fetch API stats for the dashboard."""
    try:
        response = httpx.get(f"{API_URL}/stats", timeout=10.0)
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_production_provinces(year: int):
    """Fetch unique provinces across commodities for a year."""
    provinces = set()
    for commodity in ["cashew", "rubber"]:
        try:
            response = httpx.get(
                f"{API_URL}/api/production/provinces",
                params={"commodity": commodity, "year": year},
                timeout=10.0
            )
            data = response.json()
        except Exception:
            continue

        for row in data.get("provinces", []):
            province = row.get("province")
            if province:
                provinces.add(province)

    return provinces

# Main page
st.title("🌾 Cambodia Agri Analytics Platform")
st.markdown("---")

st.markdown("""
## Welcome to Cambodia Agri Analytics

Multi-commodity analytics platform for **Cashew** and **Rubber** markets in Cambodia.

### Features

- 📊 **Cashew Analytics** - Comprehensive cashew market analysis
- 🌱 **Rubber Analytics** - Rubber market insights and trends
- 📈 **Price Trends** - Interactive price charts and forecasts
- 🗺️ **Production Maps** - Geospatial production data visualization
- 🔍 **Semantic Search** - AI-powered search across all data sources

### Data Sources

- **MEF Cambodia** - Ministry of Economy export data
- **WITS World Bank** - International trade flows
- **Open Development Cambodia** - Production statistics
- **Google Drive** - PDF/KML documents with OCR

### AI-Powered Insights

- 🧠 **Perplexity API** - Daily market research
- 📝 **Claude Reports** - Automated market analysis
- 🔍 **ChromaDB** - Semantic search across 5 collections

---

### Quick Stats
""")

stats = get_stats()
current_year = datetime.now().year
provinces = get_production_provinces(current_year)

price_count = "Loading..."
province_count = "Loading..."
report_count = "Loading..."
document_count = "Loading..."

if stats:
    supabase_stats = stats.get("supabase", {})
    chroma_stats = stats.get("chromadb", {})
    price_count = f"{supabase_stats.get('prices', 0):,}"
    report_count = f"{supabase_stats.get('claude_reports', 0):,}"
    chroma_total = sum(item.get("count", 0) for item in chroma_stats.values())
    document_count = f"{chroma_total:,}"

if provinces:
    province_count = f"{len(provinces):,}"
elif stats:
    province_count = "0"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Price Records", price_count)

with col2:
    st.metric("Production Provinces", province_count)

with col3:
    st.metric("Generated Reports", report_count)

with col4:
    st.metric("Indexed Documents", document_count)

st.markdown("---")

st.markdown("""
### Getting Started

1. **Explore Markets** - Select a commodity from the sidebar
2. **View Trends** - Analyze price movements and patterns
3. **Search Data** - Use semantic search to find relevant information
4. **Download Reports** - Export data and insights

---

**Status**: 🟢 All systems operational

**Last Updated**: Auto-refreshes every 5 minutes
""")

# Sidebar
with st.sidebar:
    st.title("Navigation")
    st.markdown("Use the pages above to navigate")

    st.markdown("---")

    st.markdown("### Quick Links")
    st.markdown("- [API Documentation](http://localhost:8000/docs)")
    st.markdown("- [Health Check](http://localhost:8000/health)")
    st.markdown("- [Database Stats](http://localhost:8000/stats)")

    st.markdown("---")

    st.markdown("### About")
    st.markdown("Cambodia Agri Analytics v0.1.0")
    st.markdown("Powered by AI & Semantic Search")
