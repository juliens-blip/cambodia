"""History page - Conversation history viewer."""
import streamlit as st
import sys
import os
import httpx
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector
from ui.config import HISTORY_URL

# Page config
st.set_page_config(page_title="History", page_icon="📚", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoint
API_URL = HISTORY_URL

# Title
st.title(f"📚 {t['history_title']}")

# Sidebar
with st.sidebar:
    st.markdown(f"### {t['settings']}")

    session_id = st.text_input(
        t["history_session"],
        value="",
        placeholder="Optional session ID"
    )

    limit = st.slider("Results to show", min_value=5, max_value=100, value=20)

    refresh_button = st.button("🔄 Refresh", width="stretch")

# Fetch history
try:
    params = {"limit": limit}
    if session_id:
        params["session_id"] = session_id

    with httpx.Client() as client:
        response = client.get(API_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    # Display history
    if data['count'] == 0:
        st.info(t["history_no_data"])
    else:
        st.success(f"Found {data['count']} conversations")

        # Convert to DataFrame for display
        if data.get('messages'):
            df = pd.DataFrame([
                {
                    "Time": msg.get("timestamp", "N/A"),
                    "Session": session_id or "default",
                    "Role": msg.get("role", "unknown"),
                    "Content": msg.get("content", "")[:100] + "..."
                }
                for msg in data['messages']
            ])

            st.dataframe(df, width="stretch")

            # Export option
            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="conversation_history.csv",
                    mime="text/csv"
                )

except httpx.HTTPError as e:
    st.error(f"{t['error']}: {e}")
except Exception as e:
    st.error(f"{t['error']}: {e}")

# Info
st.markdown("---")
st.info("""
**📚 Conversation History:**

- All your searches and Q&A sessions are saved
- Filter by session ID for specific conversations
- Export to CSV for offline analysis
- History is kept for 90 days

**Privacy:**
- No personal data is collected
- Session IDs are anonymous
- You can request deletion anytime
""")
