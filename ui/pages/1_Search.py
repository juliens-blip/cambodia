"""Search page - Semantic search interface."""
import streamlit as st
import sys
import os
import httpx
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector

# Page config
st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoint
API_URL = "http://localhost:8000/api/v1/search"

# Title
st.title(f"🔍 {t['search_title']}")

# Sidebar filters
with st.sidebar:
    st.markdown(f"### {t['settings']}")

    commodity_filter = st.selectbox(
        t["filter_commodity"],
        options=[None, "cashew", "rubber"],
        format_func=lambda x: t["filter_all"] if x is None else t[f"filter_{x}"]
    )

    top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)

    similarity_threshold = st.slider(
        "Similarity threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05
    )

# Search input
query = st.text_input(
    t["search_placeholder"],
    placeholder=t["search_placeholder"],
    key="search_query"
)

search_button = st.button(t["search_button"], type="primary", use_container_width=True)

# Search logic
if search_button and query:
    with st.spinner(t["loading"]):
        try:
            # Call API
            payload = {
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "commodity": commodity_filter
            }

            with httpx.Client() as client:
                response = client.post(API_URL, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

            # Display results
            st.success(f"{t['search_results']}: {data['count']} ({data['execution_time_ms']:.0f}ms)")

            if data['count'] == 0:
                st.info(t["search_no_results"])
            else:
                for i, result in enumerate(data['results'], 1):
                    with st.expander(
                        f"**Result {i}** - {t['search_similarity']}: {result['similarity']:.2f} | "
                        f"{t['search_source']}: {result['metadata'].get('source', 'Unknown')}"
                    ):
                        # Metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**{t['search_source']}:** {result['metadata'].get('source', 'Unknown')}")
                        with col2:
                            st.markdown(f"**{t['search_commodity']}:** {result['metadata'].get('commodity', 'N/A')}")
                        with col3:
                            st.markdown(f"**{t['search_similarity']}:** {result['similarity']:.4f}")

                        # Title
                        if result['metadata'].get('title'):
                            st.markdown(f"**Title:** {result['metadata']['title']}")

                        # Content
                        st.markdown("**Content:**")
                        st.text(result['chunk_text'])

                        # URL if available
                        if result['metadata'].get('url'):
                            st.markdown(f"**URL:** [{result['metadata']['url']}]({result['metadata']['url']})")

        except httpx.HTTPError as e:
            st.error(f"{t['error']}: {e}")
        except Exception as e:
            st.error(f"{t['error']}: {e}")

# Example queries
with st.expander("📝 Example queries"):
    st.markdown("""
    ### English
    - cashew production statistics
    - rubber export data
    - Kampong Thom agriculture

    ### Khmer (ខ្មែរ)
    - ការផលិតស្វាយចន្ទី
    - ទិន្នន័យនាំចេញកៅស៊ូ
    - កសិកម្មខេត្តកំពង់ធំ

    ### Vietnamese
    - thống kê sản xuất điều
    - dữ liệu xuất khẩu cao su
    """)

# Info
st.markdown("---")
st.info(f"""
**How it works:**
1. Enter your search query in any language
2. The system uses multilingual embeddings to find semantically similar documents
3. Results are ranked by cosine similarity
4. Free to use (no API costs)

**Performance:**
- Search latency: <100ms with HNSW index
- Supports 100+ languages including Khmer, English, Vietnamese
""")
