"""Cambodia Agricultural Intelligence - Streamlit UI.

Main application entry point with multilingual support.
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.i18n.translations import get_all_translations

# Page config
st.set_page_config(
    page_title="Cambodia Agri Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language selector in sidebar
language = st.sidebar.selectbox(
    "Language / ភាសា / Ngôn ngữ / Langue",
    options=["en", "km", "vi", "fr"],
    format_func=lambda x: {"en": "🇬🇧 English", "km": "🇰🇭 ខ្មែរ", "vi": "🇻🇳 Tiếng Việt", "fr": "🇫🇷 Français"}[x]
)

# Get translations
t = get_all_translations(language)

# Store language in session state
st.session_state.language = language

# Title
st.title(t["app_title"])
st.markdown(f"**{t['app_subtitle']}**")

st.markdown("---")

# Main content
st.header(t["nav_search"])

st.info("""
This is the main page. Use the sidebar to navigate to:
- **Search Documents**: Semantic search across all documents
- **AI Q&A**: Ask questions and get AI-generated answers
- **History**: View your conversation history
- **Admin Dashboard**: Monitor usage and budget

### Quick Start

1. Go to **Search Documents** to find relevant information
2. Use **AI Q&A** for detailed answers with citations
3. Check **Admin Dashboard** to monitor your usage

### Features

- 🌐 Multilingual search (Khmer, English, Vietnamese)
- 🔍 Semantic search (<100ms)
- 🤖 AI-powered Q&A (Perplexity RAG)
- 📊 Usage tracking and budget management
- 💾 Conversation history

### Technical Info

- **Documents**: 34 PDFs (207K characters)
- **Chunks**: 146 embedded chunks
- **Model**: multilingual-e5-large (1024 dimensions)
- **Search**: pgvector with HNSW index
- **AI**: Perplexity sonar-pro model

### Budget

- **Monthly limit**: $5
- **Cost per RAG query**: $0.005
- **Search queries**: Free (local embeddings)

---

Use the sidebar navigation to get started!
""")

# Sidebar info
with st.sidebar:
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    Cambodia Agricultural Intelligence Platform provides semantic search and AI-powered Q&A for agricultural commodity markets.

    **Supported Commodities:**
    - 🥜 Cashew (ស្វាយចន្ទី)
    - 🌳 Rubber (កៅស៊ូ)
    """)

    st.markdown("---")
    st.markdown("### Support")
    st.markdown("""
    For help or questions:
    - Check the documentation
    - Review the history page
    - Contact the administrator
    """)
