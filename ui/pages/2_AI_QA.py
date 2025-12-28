"""AI Q&A page - RAG-powered question answering."""
import streamlit as st
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector

# Page config
st.set_page_config(page_title="AI Q&A", page_icon="💬", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoint
API_URL = "http://localhost:8000/api/v1/rag/query"

# Title
st.title(f"💬 {t['chat_title']}")

# Sidebar
with st.sidebar:
    st.markdown(f"### {t['settings']}")

    commodity = st.selectbox(
        t["filter_commodity"],
        options=[None, "cashew", "rubber"],
        format_func=lambda x: t["filter_all"] if x is None else t[f"filter_{x}"]
    )

    top_k = st.slider("Context chunks", min_value=1, max_value=10, value=5)

    st.markdown("---")
    st.markdown("### 💰 Cost Info")
    st.markdown("""
    - **Per RAG query**: $0.005
    - **Monthly budget**: $5
    - **Free searches**: Unlimited
    """)

# Query input
query = st.text_area(
    t["chat_placeholder"],
    placeholder=t["chat_placeholder"],
    height=100,
    key="rag_query"
)

# Progressive disclosure
col1, col2 = st.columns([3, 1])

with col1:
    rag_button = st.button(
        f"🤖 {t['chat_button']}",
        type="primary",
        use_container_width=True,
        help=f"{t['chat_cost']}: $0.005"
    )

# RAG logic
if rag_button and query:
    with st.spinner(f"{t['loading']} ({t['chat_cost']}: $0.005)..."):
        try:
            # Call API
            payload = {
                "query": query,
                "commodity": commodity,
                "top_k": top_k,
                "use_cache": True
            }

            with httpx.Client() as client:
                response = client.post(API_URL, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()

            # Display answer
            st.success(f"✅ {t['success']} ({data['execution_time_ms']:.0f}ms)")

            # Answer
            st.markdown(f"### {t['chat_answer']}")
            st.markdown(data['answer'])

            # Citations
            if data.get('citations'):
                st.markdown(f"### {t['chat_citations']} ({len(data['citations'])})")
                for i, citation in enumerate(data['citations'], 1):
                    st.markdown(f"{i}. [{citation}]({citation})")

            # Context info
            with st.expander(f"ℹ️ {t['chat_context']}"):
                st.markdown(f"**Chunks used:** {top_k}")
                st.markdown(f"**Context size:** {data['context_used']} characters")
                st.markdown(f"**Model:** {data['model']}")
                st.markdown(f"**Tokens:** {data.get('tokens_used', 'N/A')}")
                st.markdown(f"**Cached:** {'Yes' if data.get('cached') else 'No'}")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                st.error(f"⚠️ Rate limit exceeded. Please try again later.")
                st.json(e.response.json())
            else:
                st.error(f"{t['error']}: {e.response.text}")
        except Exception as e:
            st.error(f"{t['error']}: {e}")

# Example questions
with st.expander("📝 Example questions"):
    st.markdown("""
    ### English
    - What are the main challenges for cashew production in Cambodia?
    - How do rubber prices vary across different provinces?
    - What are the key export markets for Cambodian cashew?

    ### Khmer (ខ្មែរ)
    - តើអ្វីជាបញ្ហាប្រឈមសំខាន់ៗសម្រាប់ការផលិតស្វាយចន្ទីនៅកម្ពុជា?
    - តើតម្លៃកៅស៊ូប្រែប្រួលដូចម្តេចនៅតាមខេត្តផ្សេងៗ?

    ### Vietnamese
    - Những thách thức chính trong sản xuất điều ở Campuchia là gì?
    - Giá cao su thay đổi như thế nào ở các tỉnh khác nhau?
    """)

# Progressive disclosure info
st.markdown("---")
st.info(f"""
**💡 How RAG works:**
1. Your question triggers semantic search to find relevant context
2. Context is sent to Perplexity AI along with your question
3. AI generates an answer based on local documents + online knowledge
4. Answer includes citations from both sources

**✨ Benefits:**
- Answers grounded in your documents
- Supplemented with latest online information
- Citations for verification
- Multilingual support

**💰 Budget-friendly:**
- Search is free (local embeddings)
- RAG costs $0.005 per query
- Cache reduces costs by 40-60%
""")

# Budget warning
if st.session_state.get("budget_warning"):
    st.warning("⚠️ Approaching monthly budget limit. Use semantic search (free) when possible.")
