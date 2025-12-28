"""Language selector component - Reusable across all pages."""
import streamlit as st


def render_language_selector():
    """Render language selector in sidebar and sync with session state."""
    # Get current language from session state (default to English)
    current_language = st.session_state.get("language", "en")

    # Language selector in sidebar
    language = st.sidebar.selectbox(
        "Language / ភាសា / Ngôn ngữ / Langue",
        options=["en", "km", "vi", "fr"],
        format_func=lambda x: {
            "en": "🇬🇧 English",
            "km": "🇰🇭 ខ្មែរ",
            "vi": "🇻🇳 Tiếng Việt",
            "fr": "🇫🇷 Français"
        }[x],
        index=["en", "km", "vi", "fr"].index(current_language),
        key="language_selector"
    )

    # Update session state
    st.session_state.language = language

    # Add separator
    st.sidebar.markdown("---")

    return language
