"""Semantic search page using ChromaDB."""
import os
import streamlit as st
import httpx
import json
from dotenv import load_dotenv

st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")

st.title("🔍 Semantic Search")
st.markdown("AI-powered search across all data sources using ChromaDB")
st.markdown("---")

# API base URL
load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=60)
def get_collections_info():
    """Get ChromaDB collections info."""
    try:
        response = httpx.get(f"{API_URL}/api/search/collections", timeout=10.0)
        return response.json()
    except:
        return None


def perform_search(query, collection=None, commodity=None, n_results=5):
    """Perform semantic search."""
    try:
        payload = {
            "query": query,
            "collection": collection,
            "commodity": commodity,
            "n_results": n_results
        }

        response = httpx.post(
            f"{API_URL}/api/search/",
            json=payload,
            timeout=30.0
        )

        return response.json()
    except Exception as e:
        st.error(f"Search failed: {e}")
        return None


# Collections Info
st.header("📚 Available Collections")

collections = get_collections_info()

if collections:
    cols = st.columns(len(collections['collections']))

    for i, coll in enumerate(collections['collections']):
        with cols[i]:
            st.metric(
                coll['name'].replace('_', ' ').title(),
                coll['count']
            )
            st.caption(coll['description'])
else:
    st.warning("Unable to load collections")

st.markdown("---")

# Search Interface
st.header("🔎 Search")

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    query = st.text_input(
        "Enter your search query",
        placeholder="e.g., 'cashew production in Kampong Cham' or 'price spike due to high demand'"
    )

with col2:
    collection = st.selectbox(
        "Collection",
        ["All Collections", "commodity_documents", "perplexity_analyses",
         "claude_reports", "commodity_prices", "production_data"]
    )

with col3:
    commodity = st.selectbox(
        "Commodity",
        ["All", "cashew", "rubber"]
    )

n_results = st.slider("Number of results", 1, 20, 5)

if st.button("🔍 Search", type="primary"):
    if not query:
        st.warning("Please enter a search query")
    else:
        with st.spinner("Searching..."):
            results = perform_search(
                query,
                collection=None if collection == "All Collections" else collection,
                commodity=None if commodity == "All" else commodity,
                n_results=n_results
            )

            if results:
                st.success(f"✅ Search complete!")

                if collection == "All Collections" and "collections" in results:
                    # Show results by collection
                    for coll_name, coll_results in results['collections'].items():
                        if coll_results:
                            st.subheader(f"📁 {coll_name.replace('_', ' ').title()}")

                            for i, result in enumerate(coll_results, 1):
                                with st.expander(f"Result {i} (Distance: {result.get('distance', 'N/A'):.4f})"):
                                    st.markdown(f"**Document:**\n{result['document'][:500]}...")
                                    st.json(result['metadata'])

                            st.markdown("---")
                else:
                    # Show single collection results
                    for i, result in enumerate(results.get('results', []), 1):
                        with st.expander(f"Result {i}"):
                            st.markdown(result['document'])
                            st.json(result['metadata'])

# Example Queries
st.markdown("---")
st.header("💡 Example Queries")

examples = [
    "High cashew prices in Vietnam",
    "Rubber production trends 2023",
    "Impact of US-China trade war",
    "Best yielding provinces for cashew",
    "Supply shortage affecting prices"
]

cols = st.columns(len(examples))
for i, example in enumerate(examples):
    with cols[i]:
        if st.button(example, key=f"example_{i}"):
            st.session_state['search_query'] = example
            st.rerun()
