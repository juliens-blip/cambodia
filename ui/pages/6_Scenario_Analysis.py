"""Scenario Analysis - Multi-perspective market analysis (Pessimistic, Realistic, Optimistic)."""
import streamlit as st
import sys
import os
import httpx
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector

# Page config
st.set_page_config(page_title="Scenario Analysis", page_icon="📊", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
BASE_URL = "http://localhost:8000/api/v1"

# Title
st.title(f"📊 {t.get('scenario_title', 'Multi-Perspective Analysis')}")
st.markdown(t.get('scenario_subtitle', '3 scenarios based on market prices, historical documents, and Twitter/X news'))

# Sidebar - Settings
st.sidebar.markdown(f"### {t.get('settings', 'Settings')}")
commodity = st.sidebar.selectbox(
    t.get('filter_commodity', 'Select Commodity'),
    options=["cashew", "rubber"],
    format_func=lambda x: t.get(f'filter_{x}', x.capitalize()),
    index=0
)

history_days = st.sidebar.slider(
    t.get('history_days', 'History (days)'),
    min_value=7,
    max_value=90,
    value=30
)

# Refresh button - clears ALL cache including Twitter data
if st.sidebar.button(f"🔄 {t.get('scenario_refresh', 'Refresh Analysis')}"):
    st.cache_data.clear()
    print("[DEBUG] Cache cleared by user")
    st.rerun()

# Debug mode toggle
show_debug = st.sidebar.checkbox("🐛 Debug mode", value=False)

st.sidebar.markdown("---")


@st.cache_data(ttl=3600)
def fetch_market_data(commodity: str, days: int):
    """Fetch market price data."""
    try:
        with httpx.Client() as client:
            url = f"{BASE_URL}/trends/public/prices/{commodity}?days={days}"
            response = client.get(url, timeout=30.0)
            if response.status_code == 200:
                return response.json()
    except httpx.TimeoutException:
        st.warning(f"⚠️ Market data request timed out. Using fallback data.")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error fetching market data: {e}")
    return None


@st.cache_data(ttl=3600)
def fetch_historical_docs(commodity: str, query: str, limit: int = 5):
    """Fetch relevant historical documents."""
    try:
        with httpx.Client() as client:
            url = f"{BASE_URL}/search"
            payload = {
                "query": query,
                "top_k": limit,
                "similarity_threshold": 0.5,
                "commodity": commodity
            }
            # First search can take 60+ seconds (model loading)
            response = client.post(url, json=payload, timeout=120.0)
            if response.status_code == 200:
                return response.json()
    except httpx.TimeoutException:
        st.warning(f"⏱️ Document search timed out (model loading can take time). Try again.")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error fetching documents: {str(e)}")
    return None


@st.cache_data(ttl=300)  # 5 min cache instead of 1h
def fetch_twitter_data(commodity: str):
    """Fetch latest Twitter/X sentiment data."""
    try:
        with httpx.Client() as client:
            url = f"{BASE_URL}/trends/latest/{commodity}"
            print(f"[DEBUG] Fetching Twitter data from: {url}")
            response = client.get(url, timeout=30.0)
            print(f"[DEBUG] Response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                tweet_count = data.get('tweet_count', 0)
                top_tweets = data.get('top_tweets', [])
                print(f"[DEBUG] tweet_count={tweet_count}, top_tweets len={len(top_tweets) if top_tweets else 0}")
                if top_tweets:
                    print(f"[DEBUG] First tweet: {top_tweets[0] if top_tweets else 'None'}")
                return data
            elif response.status_code == 404:
                st.info(f"ℹ️ No Twitter data available for {commodity} yet.")
                return None
    except httpx.TimeoutException:
        st.warning(f"⏱️ Twitter data request timed out.")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error fetching Twitter data: {str(e)}")
        print(f"[DEBUG] Error: {e}")
    return None


@st.cache_data(ttl=3600)
def generate_scenario_analysis(commodity: str, scenario_type: str, market_data: dict, docs_data: dict, twitter_data: dict):
    """
    Generate scenario analysis using Perplexity API.

    scenario_type: 'pessimistic', 'realistic', or 'optimistic'
    """
    try:
        # Prepare context
        price_stats = market_data.get('statistics', {}) if market_data else {}
        current_price = price_stats.get('current', 0)
        price_change = price_stats.get('change_pct', 0)

        # Get top documents
        docs = docs_data.get('results', [])[:3] if docs_data else []
        doc_summaries = []
        for doc in docs:
            doc_summaries.append(f"- {doc.get('content', '')[:200]}...")

        # Get Twitter sentiment
        twitter_sentiment = twitter_data.get('twitter_sentiment', 'neutral') if twitter_data else 'neutral'
        overall_trend = twitter_data.get('overall_trend', 'neutral') if twitter_data else 'neutral'

        # Build prompt based on scenario type
        scenario_prompts = {
            'pessimistic': f"""As a conservative market analyst, provide a PESSIMISTIC (bearish) analysis for {commodity} market.

Current market data:
- Current price: ${current_price}/ton
- Price change ({history_days} days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Historical context from documents:
{chr(10).join(doc_summaries) if doc_summaries else "Limited historical data available"}

Focus on:
1. **Price Outlook**: Downside risks, potential price declines
2. **Risk Factors**: Supply gluts, demand weakness, market headwinds
3. **Bearish Scenarios**: What could go wrong in the next 3-6 months

Be realistic but cautious. Cite specific data points.""",

            'realistic': f"""As a balanced market analyst, provide a REALISTIC (neutral) analysis for {commodity} market.

Current market data:
- Current price: ${current_price}/ton
- Price change ({history_days} days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Historical context from documents:
{chr(10).join(doc_summaries) if doc_summaries else "Limited historical data available"}

Focus on:
1. **Price Outlook**: Most likely price trajectory based on fundamentals
2. **Balanced View**: Both upside and downside factors
3. **Probable Scenarios**: What's most likely in the next 3-6 months

Be objective and data-driven. Cite specific evidence.""",

            'optimistic': f"""As an opportunity-focused market analyst, provide an OPTIMISTIC (bullish) analysis for {commodity} market.

Current market data:
- Current price: ${current_price}/ton
- Price change ({history_days} days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Historical context from documents:
{chr(10).join(doc_summaries) if doc_summaries else "Limited historical data available"}

Focus on:
1. **Price Outlook**: Upside potential, bullish catalysts
2. **Opportunities**: Strong demand drivers, supply constraints, growth factors
3. **Bullish Scenarios**: What could drive prices higher in the next 3-6 months

Be realistic but optimistic. Cite specific opportunities."""
        }

        prompt = scenario_prompts.get(scenario_type, scenario_prompts['realistic'])

        # Call Perplexity API via RAG endpoint
        with httpx.Client() as client:
            url = f"{BASE_URL}/rag/query"
            payload = {
                "query": prompt,
                "commodity": commodity,
                "top_k": 5,
                "use_cache": True
            }
            # RAG query can take 30-60 seconds (Perplexity AI call + search)
            response = client.post(url, json=payload, timeout=120.0)

            if response.status_code == 200:
                result = response.json()
                return {
                    'analysis': result.get('answer', 'Analysis not available'),
                    'citations': result.get('citations', []),
                    'cost': 0  # Cost is tracked by the API internally
                }
            elif response.status_code == 429:
                st.warning(f"⏱️ Rate limit exceeded. Please wait a moment and try again.")
                return {
                    'analysis': f"Rate limit exceeded. Please refresh the page in a few minutes.",
                    'citations': [],
                    'cost': 0
                }
    except httpx.TimeoutException:
        st.warning(f"⏱️ Analysis generation timed out. This can happen on first use. Try refreshing.")
        return {
            'analysis': f"Request timed out. The AI analysis is taking longer than expected. Please try again.",
            'citations': [],
            'cost': 0
        }
    except Exception as e:
        st.warning(f"⚠️ Error generating analysis: {str(e)}")

    return {
        'analysis': f"Unable to generate {scenario_type} analysis. Please try again.",
        'citations': [],
        'cost': 0
    }


def display_data_sources(market_data, docs_data, twitter_data):
    """Display data sources summary."""
    st.markdown(f"### 📊 {t.get('scenario_data_sources', 'Data Sources')}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            t.get('scenario_market_data', 'Market Data'),
            f"${market_data.get('statistics', {}).get('current', 0):,.0f}/ton" if market_data else "N/A",
            delta=f"{market_data.get('statistics', {}).get('change_pct', 0):+.1f}%" if market_data else None
        )

    with col2:
        doc_count = len(docs_data.get('results', [])) if docs_data else 0
        st.metric(
            t.get('scenario_historical_docs', 'Historical Documents'),
            f"{doc_count} {t.get('scenario_doc_count', 'documents analyzed')}"
        )

    with col3:
        tweet_count = twitter_data.get('tweet_count', 0) if twitter_data else 0
        st.metric(
            t.get('scenario_twitter_news', 'Twitter/X News'),
            f"{tweet_count} {t.get('scenario_tweet_count', 'recent tweets')}"
        )


def display_key_tweet(twitter_data):
    """Display the most relevant tweet and other tweets in an expander."""
    if not twitter_data:
        st.info("ℹ️ No Twitter/X data available. Analysis will proceed without social media context.")
        return

    tweets = twitter_data.get('top_tweets', [])
    if tweets and len(tweets) > 0:
        st.markdown(f"### 🐦 {t.get('scenario_key_tweet', 'Key Tweet')}")

        # Get the most relevant tweet (first one, usually highest engagement)
        key_tweet = tweets[0]

        # Display main tweet in a nice box
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1a1a2e; padding: 15px; border-radius: 10px; border-left: 4px solid #1DA1F2;">
                <p style="margin: 0; font-size: 14px; color: #1DA1F2;"><strong>@{key_tweet.get('username', 'unknown')}</strong></p>
                <p style="margin: 10px 0; font-size: 15px; color: #e0e0e0;">{key_tweet.get('text', '')}</p>
                <p style="margin: 0; font-size: 12px; color: #657786;">
                    ❤️ {key_tweet.get('likes', 0)} • 🔄 {key_tweet.get('retweets', 0)} •
                    {key_tweet.get('created_at', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Show other tweets in an expander if there are more than 1
        if len(tweets) > 1:
            with st.expander(f"📋 {t.get('scenario_view_all_tweets', 'View all')} {len(tweets)} tweets"):
                for i, tweet in enumerate(tweets[1:], start=2):
                    st.markdown(f"""
                    <div style="background-color: #16213e; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #1DA1F2;">
                        <p style="margin: 0; font-size: 13px; color: #1DA1F2;"><strong>@{tweet.get('username', 'unknown')}</strong></p>
                        <p style="margin: 8px 0; font-size: 14px; color: #d0d0d0;">{tweet.get('text', '')}</p>
                        <p style="margin: 0; font-size: 11px; color: #657786;">
                            ❤️ {tweet.get('likes', 0)} • 🔄 {tweet.get('retweets', 0)} • {tweet.get('created_at', 'N/A')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No recent tweets found. Analysis will focus on market data and historical documents.")



def display_scenario_analysis(scenario_type: str, analysis_data: dict, color: str):
    """Display a single scenario analysis."""
    scenario_emoji = {
        'pessimistic': '📉',
        'realistic': '⚖️',
        'optimistic': '📈'
    }

    # Analysis content
    st.markdown(analysis_data.get('analysis', 'Analysis not available'))

    # Citations
    citations = analysis_data.get('citations', [])
    if citations:
        with st.expander(f"📚 {t.get('trends_sources', 'Sources & Citations')} ({len(citations)})"):
            for i, citation in enumerate(citations, 1):
                # Handle both string citations and dict citations
                if isinstance(citation, str):
                    # Citation is a simple string
                    st.markdown(f"**[{i}]** {citation[:300]}...")
                elif isinstance(citation, dict):
                    # Citation is a dictionary
                    st.markdown(f"**[{i}]** {citation.get('content', '')[:300]}...")
                    st.caption(f"Source: {citation.get('source', 'Unknown')} | Similarity: {citation.get('similarity', 0):.2%}")
                else:
                    # Fallback for unknown type
                    st.markdown(f"**[{i}]** {str(citation)[:300]}...")


# Main content
try:
    # Fetch all data
    with st.spinner(t.get('loading', 'Loading...')):
        commodity_display = t.get(f'filter_{commodity}', commodity.capitalize())

        # Fetch market data
        market_data = fetch_market_data(commodity, history_days)

        # Fetch historical documents
        search_query = f"{commodity} market trends prices analysis"
        docs_data = fetch_historical_docs(commodity, search_query, limit=5)

        # Fetch Twitter data
        twitter_data = fetch_twitter_data(commodity)

    # Debug display if enabled
    if show_debug:
        st.sidebar.markdown("### 🐛 Debug Info")
        if twitter_data:
            st.sidebar.success(f"✅ Twitter data received")
            st.sidebar.write(f"tweet_count: {twitter_data.get('tweet_count', 'N/A')}")
            top_tweets = twitter_data.get('top_tweets', [])
            st.sidebar.write(f"top_tweets: {len(top_tweets) if top_tweets else 0} items")
            if top_tweets and len(top_tweets) > 0:
                st.sidebar.write(f"First tweet: @{top_tweets[0].get('username', '?')}")
        else:
            st.sidebar.error("❌ No Twitter data")

    # Display data sources summary
    display_data_sources(market_data, docs_data, twitter_data)

    st.markdown("---")

    # Display key tweet
    display_key_tweet(twitter_data)

    st.markdown("---")

    # Three scenario tabs
    tab1, tab2, tab3 = st.tabs([
        t.get('scenario_pessimistic', '📉 Pessimistic Analysis'),
        t.get('scenario_realistic', '⚖️ Realistic Analysis'),
        t.get('scenario_optimistic', '📈 Optimistic Analysis')
    ])

    with tab1:
        st.markdown(f"## {t.get('scenario_pessimistic', '📉 Pessimistic Analysis')}")
        st.caption(t.get('scenario_based_on', 'Based on') + f": {t.get('scenario_market_data', 'Market data')}, {t.get('scenario_historical_docs', 'Historical documents')}, {t.get('scenario_twitter_news', 'Twitter/X news')}")

        with st.spinner(t.get('scenario_generating', 'Generating analysis...')):
            pessimistic = generate_scenario_analysis(commodity, 'pessimistic', market_data, docs_data, twitter_data)

        display_scenario_analysis('pessimistic', pessimistic, '#ff4b4b')

    with tab2:
        st.markdown(f"## {t.get('scenario_realistic', '⚖️ Realistic Analysis')}")
        st.caption(t.get('scenario_based_on', 'Based on') + f": {t.get('scenario_market_data', 'Market data')}, {t.get('scenario_historical_docs', 'Historical documents')}, {t.get('scenario_twitter_news', 'Twitter/X news')}")

        with st.spinner(t.get('scenario_generating', 'Generating analysis...')):
            realistic = generate_scenario_analysis(commodity, 'realistic', market_data, docs_data, twitter_data)

        display_scenario_analysis('realistic', realistic, '#ffa500')

    with tab3:
        st.markdown(f"## {t.get('scenario_optimistic', '📈 Optimistic Analysis')}")
        st.caption(t.get('scenario_based_on', 'Based on') + f": {t.get('scenario_market_data', 'Market data')}, {t.get('scenario_historical_docs', 'Historical documents')}, {t.get('scenario_twitter_news', 'Twitter/X news')}")

        with st.spinner(t.get('scenario_generating', 'Generating analysis...')):
            optimistic = generate_scenario_analysis(commodity, 'optimistic', market_data, docs_data, twitter_data)

        display_scenario_analysis('optimistic', optimistic, '#00cc66')

except Exception as e:
    st.error(f"{t.get('error', 'Error')}: {str(e)}")
    import traceback
    st.code(traceback.format_exc())


# Sidebar info
st.sidebar.markdown("---")
if language == "fr":
    st.sidebar.info("""
    ### À propos

    Cette page génère 3 analyses différentes :

    - **📉 Dépréciative**: Scénario pessimiste avec facteurs de risque
    - **⚖️ Réaliste**: Vue équilibrée basée sur les données
    - **📈 Positive**: Scénario optimiste avec opportunités

    Chaque analyse utilise :
    - Prix du marché en temps réel
    - Documents historiques pertinents
    - Sentiment Twitter/X récent
    - IA Perplexity pour génération
    """)
else:
    st.sidebar.info("""
    ### About

    This page generates 3 different analyses:

    - **📉 Pessimistic**: Bearish scenario with risk factors
    - **⚖️ Realistic**: Balanced view based on data
    - **📈 Optimistic**: Bullish scenario with opportunities

    Each analysis uses:
    - Real-time market prices
    - Relevant historical documents
    - Recent Twitter/X sentiment
    - Perplexity AI for generation
    """)
