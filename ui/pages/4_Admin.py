"""Admin dashboard - Usage statistics and budget monitoring."""
import streamlit as st
import sys
import os
import httpx
import pandas as pd
import plotly.express as px
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector
from ui.config import STATS_URL, TRENDS_SUMMARY_URL, ALERTS_URL

# Page config
st.set_page_config(page_title="Admin", page_icon="📊", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
API_URL = STATS_URL

# Title
st.title(f"📊 {t['admin_title']}")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()

# Fetch stats
try:
    with httpx.Client() as client:
        response = client.get(API_URL, timeout=10.0)
        response.raise_for_status()
        stats = response.json()

    # Display metrics
    st.markdown(f"### {t['admin_stats']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t["admin_total_queries"],
            stats['total_queries'],
            delta=None
        )

    with col2:
        st.metric(
            t["admin_rag_queries"],
            stats['rag_queries'],
            delta=None
        )

    with col3:
        st.metric(
            t["admin_search_queries"],
            stats['search_queries'],
            delta=None
        )

    with col4:
        cache_hit_rate = stats['cache_hit_rate']
        st.metric(
            "Cache Hit Rate",
            f"{cache_hit_rate:.1f}%",
            delta=None
        )

    st.markdown("---")

    # Budget metrics
    st.markdown(f"### {t['admin_budget']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t["admin_cost"],
            f"${stats['total_cost_usd']:.2f}",
            delta=None
        )

    with col2:
        st.metric(
            t["admin_remaining"],
            f"${stats['budget_remaining_usd']:.2f}",
            delta=None
        )

    with col3:
        utilization = stats['budget_utilization_pct']
        st.metric(
            t["admin_utilization"],
            f"{utilization:.1f}%",
            delta=None,
            delta_color="inverse" if utilization > 80 else "normal"
        )

    with col4:
        queries_remaining = int((5.0 - stats['total_cost_usd']) / 0.005)
        st.metric(
            "RAG Queries Remaining",
            queries_remaining,
            delta=None
        )

    # Budget progress bar
    st.progress(min(utilization / 100, 1.0))

    if utilization > 90:
        st.error("⚠️ Warning: Over 90% budget utilization!")
    elif utilization > 80:
        st.warning("⚠️ Notice: Over 80% budget utilization")
    else:
        st.success("✅ Budget within limits")

    st.markdown("---")

    # Query distribution
    st.markdown("### Query Distribution")

    query_data = pd.DataFrame({
        "Type": ["Search", "RAG"],
        "Count": [stats['search_queries'], stats['rag_queries']]
    })

    fig = px.pie(
        query_data,
        values="Count",
        names="Type",
        title="Query Type Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Cost breakdown
    st.markdown("### Cost Breakdown")

    cost_data = pd.DataFrame({
        "Category": ["RAG Queries", "Search (Free)", "Remaining Budget"],
        "Amount ($)": [
            stats['total_cost_usd'],
            0.0,
            stats['budget_remaining_usd']
        ]
    })

    fig = px.bar(
        cost_data,
        x="Category",
        y="Amount ($)",
        title="Monthly Budget Breakdown",
        color="Category"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Market Trends Section
    st.markdown("### 📈 Market Trends Summary")

    try:
        trends_response = client.get(TRENDS_SUMMARY_URL, timeout=10.0)
        trends_response.raise_for_status()
        trends_summary = trends_response.json()

        # Display latest trends for each commodity
        col1, col2 = st.columns(2)

        for idx, (commodity, data) in enumerate(trends_summary.get('commodities', {}).items()):
            col = col1 if idx == 0 else col2

            with col:
                st.markdown(f"**{commodity.capitalize()}**")

                # Trend indicator
                trend = data.get('overall_trend', 'neutral')
                trend_emoji = {
                    'strong_bullish': '📈🔥',
                    'bullish': '📈',
                    'neutral': '➡️',
                    'bearish': '📉',
                    'strong_bearish': '📉💥'
                }.get(trend, '➡️')

                st.markdown(f"Trend: {trend_emoji} **{trend.replace('_', ' ').title()}**")

                # Twitter sentiment
                sentiment = data.get('twitter_sentiment', 'neutral')
                sentiment_emoji = {
                    'bullish': '😊',
                    'bearish': '😟',
                    'neutral': '😐'
                }.get(sentiment, '😐')

                st.markdown(f"Sentiment: {sentiment_emoji} {sentiment.capitalize()}")

                # Price change
                price_change = data.get('stock_change_pct')
                if price_change is not None:
                    color = "green" if price_change > 0 else "red" if price_change < 0 else "gray"
                    st.markdown(f"Price Change: :{color}[{price_change:+.2f}%]")

                # Confidence
                confidence = data.get('confidence_score', 0)
                st.markdown(f"Confidence: {confidence:.0%}")

                # Date
                trend_date = data.get('trend_date', 'N/A')
                st.markdown(f"*Updated: {trend_date}*")

        # Alerts section
        alerts_response = client.get(ALERTS_URL, timeout=10.0)
        alerts_response.raise_for_status()
        alerts_data = alerts_response.json()

        alerts_count = alerts_data.get('count', 0)

        if alerts_count > 0:
            st.markdown(f"#### 🚨 Active Alerts ({alerts_count})")

            for alert in alerts_data.get('alerts', [])[:5]:  # Show first 5
                severity = alert.get('severity', 'low')
                severity_icon = {
                    'low': 'ℹ️',
                    'medium': '⚠️',
                    'high': '⚠️',
                    'critical': '🚨'
                }.get(severity, '•')

                st.markdown(f"{severity_icon} **[{severity.upper()}]** {alert.get('message', '')}")
        else:
            st.success("✅ No active market alerts")

    except Exception as e:
        st.warning(f"Could not load market trends: {e}")

    st.markdown("---")

    # Recommendations
    st.markdown("### 💡 Recommendations")

    if stats['cache_hit_rate'] < 50:
        st.info("""
        **Low cache hit rate detected!**
        - Enable caching for repeated queries
        - Current savings: minimal
        - Potential savings: 40-60% with caching
        """)

    if utilization > 70:
        st.warning("""
        **High budget utilization!**
        - Consider using semantic search (free) when possible
        - Enable aggressive caching
        - Review query patterns for duplicates
        """)

    if stats['rag_queries'] > 0 and stats['search_queries'] == 0:
        st.info("""
        **Tip: Use semantic search first!**
        - Semantic search is free and fast
        - Use RAG only when you need AI-generated answers
        - This can save up to 70% on costs
        """)

except httpx.HTTPError as e:
    st.error(f"{t['error']}: {e}")
except Exception as e:
    st.error(f"{t['error']}: {e}")

# System info
with st.sidebar:
    st.markdown("---")
    st.markdown("### System Info")
    st.markdown(f"""
    **Last updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    **Limits:**
    - Monthly: 1000 queries
    - Daily: 50 queries
    - Hourly: 5 queries/session

    **Costs:**
    - Search: $0
    - RAG: $0.005/query
    - Budget: $5/month
    """)
