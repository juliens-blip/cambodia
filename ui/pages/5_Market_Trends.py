"""Market Trends - Twitter/X sentiment and stock market analysis."""
import streamlit as st
import sys
import os
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector

# Page config
st.set_page_config(page_title="Market Trends", page_icon="📈", layout="wide")

# Language selector (must be called before using translations)
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
BASE_URL = "http://localhost:8000/api/v1/trends"

# Title
st.title(f"📈 {t.get('trends_title', 'Market Trends Analysis')}")
st.markdown(t.get('trends_subtitle', 'Twitter/X sentiment + Stock market data • Updated daily'))

# Sidebar - Commodity selection
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

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()

# Main content
try:
    with httpx.Client() as client:
        # Get latest trend
        latest_url = f"{BASE_URL}/latest/{commodity}"
        latest_response = client.get(latest_url, timeout=10.0)

        if latest_response.status_code == 200:
            latest = latest_response.json()

            # Display latest trend
            commodity_display = t.get(f'filter_{commodity}', commodity.capitalize())
            st.markdown(f"## {t.get('trends_latest_analysis', 'Latest Analysis')} - {commodity_display}")
            st.markdown(f"*{t.get('trends_updated', 'Updated')}: {latest.get('trend_date', 'N/A')}*")

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                trend = latest.get('overall_trend', 'neutral')
                trend_emoji = {
                    'strong_bullish': '📈🔥',
                    'bullish': '📈',
                    'neutral': '➡️',
                    'bearish': '📉',
                    'strong_bearish': '📉💥'
                }.get(trend, '➡️')

                trend_label = t.get(f'trend_{trend}', trend.replace('_', ' ').title())

                st.metric(
                    t.get('trends_overall_trend', 'Overall Trend'),
                    f"{trend_emoji} {trend_label}",
                    delta=None
                )

            with col2:
                sentiment = latest.get('twitter_sentiment', 'neutral')
                sentiment_emoji = {
                    'bullish': '😊',
                    'bearish': '😟',
                    'neutral': '😐'
                }.get(sentiment, '😐')

                st.metric(
                    t.get('trends_twitter_sentiment', 'Twitter Sentiment'),
                    f"{sentiment_emoji} {sentiment.capitalize()}",
                    delta=None
                )

            with col3:
                price_change = latest.get('stock_change_pct')
                if price_change is not None:
                    st.metric(
                        t.get('trends_price_change', 'Price Change'),
                        f"{price_change:+.2f}%",
                        delta=price_change,
                        delta_color="normal"
                    )
                else:
                    st.metric(t.get('trends_price_change', 'Price Change'), "N/A")

            with col4:
                confidence = latest.get('confidence_score', 0)
                st.metric(
                    t.get('trends_confidence', 'Confidence'),
                    f"{confidence:.0%}",
                    delta=None
                )

            st.markdown("---")

            # Twitter Analysis
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"### 🐦 {t.get('trends_twitter_analysis', 'Twitter/X Analysis')}")

                twitter_volume = latest.get('twitter_volume', 0)
                st.markdown(f"**{t.get('trends_tweet_volume', 'Tweet Volume (48h)')}:** {twitter_volume} {t.get('tweets', 'tweets')}")

                twitter_summary = latest.get('twitter_summary', '')
                if twitter_summary:
                    st.markdown(f"**{t.get('trends_summary', 'Summary')}:** {twitter_summary}")

                # Top tweets
                top_tweets = latest.get('top_tweets', [])
                if top_tweets:
                    st.markdown(f"**{t.get('trends_top_tweets', 'Top Tweets')}:**")
                    for idx, tweet in enumerate(top_tweets[:5], 1):
                        st.markdown(f"{idx}. *\"{tweet}\"*")

            with col2:
                st.markdown(f"### 📊 {t.get('trends_stock_market', 'Stock Market')}")

                stock_price = latest.get('stock_price_usd')
                if stock_price:
                    st.markdown(f"**{t.get('trends_price', 'Price')}:** ${stock_price:,.2f}/ton")

                stock_change = latest.get('stock_change_pct')
                if stock_change is not None:
                    color = "green" if stock_change > 0 else "red" if stock_change < 0 else "gray"
                    st.markdown(f"**{t.get('trends_24h_change', '24h Change')}:** :{color}[{stock_change:+.2f}%]")

                stock_volume = latest.get('stock_volume')
                if stock_volume:
                    st.markdown(f"**{t.get('trends_volume', 'Volume')}:** {stock_volume:,}")

            st.markdown("---")

            # Key Factors
            st.markdown(f"### 🔑 {t.get('trends_key_factors', 'Key Factors')}")
            key_factors = latest.get('key_factors', [])

            if key_factors:
                for idx, factor in enumerate(key_factors, 1):
                    st.markdown(f"{idx}. {factor}")
            else:
                st.info(t.get('trends_no_data', 'No key factors extracted'))

            st.markdown("---")

            # AI Analysis
            with st.expander(f"🤖 {t.get('trends_ai_analysis', 'Full AI Analysis')}", expanded=False):
                ai_analysis = latest.get('ai_analysis', '')
                if ai_analysis:
                    st.markdown(ai_analysis)
                else:
                    st.info(t.get('trends_no_data', 'No AI analysis available'))

            # Citations
            citations = latest.get('perplexity_citations', [])
            if citations:
                with st.expander(f"📚 {t.get('trends_sources', 'Sources & Citations')}", expanded=False):
                    for idx, citation in enumerate(citations, 1):
                        st.markdown(f"{idx}. {citation}")

        else:
            st.warning(f"{t.get('trends_no_data', 'No trend data found for')} {commodity}")

        st.markdown("---")

        # PUBLIC PRICE DATA (NEW SECTION)
        st.markdown(f"## 💰 {t.get('trends_public_data', 'Public Price Data')}")

        try:
            public_url = f"{BASE_URL}/public/prices/{commodity}?days={history_days}"
            public_response = client.get(public_url, timeout=10.0)

            if public_response.status_code == 200:
                public_data = public_response.json()
                stats = public_data['statistics']

                st.markdown(f"*{t.get('trends_source', 'Source')}: {public_data['source']}*")

                # Statistics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        t.get('trends_current_price', 'Current Price'),
                        f"${stats['current']:,.0f}/ton",
                        delta=f"{stats['change_pct']:+.1f}%"
                    )

                with col2:
                    st.metric(
                        t.get('trends_avg_price', 'Average Price'),
                        f"${stats['average']:,.0f}/ton"
                    )

                with col3:
                    st.metric(
                        t.get('trends_highest', 'Highest'),
                        f"${stats['highest']:,.0f}/ton"
                    )

                with col4:
                    st.metric(
                        t.get('trends_lowest', 'Lowest'),
                        f"${stats['lowest']:,.0f}/ton"
                    )

                # Chart
                if public_data['data']:
                    df_public = pd.DataFrame(public_data['data'])
                    df_public['date'] = pd.to_datetime(df_public['date'])

                    fig_public = go.Figure()

                    fig_public.add_trace(go.Scatter(
                        x=df_public['date'],
                        y=df_public['price_usd'],
                        mode='lines+markers',
                        name=t.get('trends_price', 'Price'),
                        line=dict(color='#00CC96', width=3),
                        marker=dict(size=10),
                        fill='tozeroy',
                        fillcolor='rgba(0, 204, 150, 0.1)',
                        hovertemplate='<b>' + t.get('date', 'Date') + ':</b> %{x|%Y-%m-%d}<br>' +
                                      '<b>' + t.get('trends_price', 'Price') + ':</b> $%{y:,.0f}/ton<br>' +
                                      '<extra></extra>'
                    ))

                    fig_public.update_layout(
                        xaxis_title=t.get('date', 'Date'),
                        yaxis_title=f"{t.get('trends_price', 'Price')} (USD/ton)",
                        hovermode='x unified',
                        height=450,
                        yaxis=dict(
                            tickformat='$,.0f',
                            gridcolor='rgba(128, 128, 128, 0.2)'
                        ),
                        xaxis=dict(
                            gridcolor='rgba(128, 128, 128, 0.2)'
                        )
                    )

                    st.plotly_chart(fig_public, use_container_width=True)
                else:
                    st.info(t.get('trends_no_price_data', 'No price data available'))

            else:
                st.warning(t.get('trends_no_price_data', 'No public price data available'))

        except Exception as e:
            st.error(f"{t.get('error', 'Error')}: {e}")

        st.markdown("---")

        # Historical Trends (AI Analysis)
        st.markdown(f"## {t.get('trends_historical', 'Historical Trends')} ({history_days} {t.get('history_days', 'days').lower()})")

        history_url = f"{BASE_URL}/history/{commodity}?days={history_days}"
        history_response = client.get(history_url, timeout=10.0)
        history_response.raise_for_status()
        history_data = history_response.json()

        history_list = history_data.get('data', [])

        if history_list:
            # Convert to DataFrame
            df = pd.DataFrame(history_list)
            df['trend_date'] = pd.to_datetime(df['trend_date'])
            df = df.sort_values('trend_date')

            # Sentiment over time
            st.markdown(f"### {t.get('trends_sentiment_chart', 'Twitter Sentiment Trend')}")

            sentiment_map = {'bullish': 1, 'neutral': 0, 'bearish': -1}
            df['sentiment_score'] = df['twitter_sentiment'].map(sentiment_map)

            fig_sentiment = go.Figure()

            fig_sentiment.add_trace(go.Scatter(
                x=df['trend_date'],
                y=df['sentiment_score'],
                mode='lines+markers',
                name='Sentiment',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))

            # Translate y-axis labels
            bearish_label = t.get('trend_bearish', 'Bearish')
            neutral_label = t.get('trend_neutral', 'Neutral')
            bullish_label = t.get('trend_bullish', 'Bullish')

            fig_sentiment.update_layout(
                xaxis_title=t.get('date', 'Date'),
                yaxis_title="Sentiment Score",
                yaxis=dict(
                    tickmode='array',
                    tickvals=[-1, 0, 1],
                    ticktext=[bearish_label, neutral_label, bullish_label]
                ),
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig_sentiment, use_container_width=True)

            # Price change over time
            if 'stock_change_pct' in df.columns:
                st.markdown(f"### {t.get('trends_price_chart', 'Price Change Trend')}")

                fig_price = go.Figure()

                colors = ['green' if x > 0 else 'red' if x < 0 else 'gray'
                         for x in df['stock_change_pct']]

                fig_price.add_trace(go.Bar(
                    x=df['trend_date'],
                    y=df['stock_change_pct'],
                    marker_color=colors,
                    name=t.get('trends_price_change', 'Price Change %')
                ))

                fig_price.update_layout(
                    xaxis_title=t.get('date', 'Date'),
                    yaxis_title=f"{t.get('trends_price_change', 'Price Change')} (%)",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig_price, use_container_width=True)

            # Confidence over time
            if 'confidence_score' in df.columns:
                st.markdown(f"### {t.get('trends_confidence_chart', 'Confidence Score Trend')}")

                fig_confidence = go.Figure()

                fig_confidence.add_trace(go.Scatter(
                    x=df['trend_date'],
                    y=df['confidence_score'],
                    mode='lines+markers',
                    name=t.get('trends_confidence', 'Confidence'),
                    line=dict(color='purple', width=2),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(128, 0, 128, 0.1)'
                ))

                fig_confidence.update_layout(
                    xaxis_title=t.get('date', 'Date'),
                    yaxis_title=t.get('trends_confidence', 'Confidence Score'),
                    yaxis=dict(range=[0, 1]),
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig_confidence, use_container_width=True)

            # Data table
            with st.expander(f"📋 {t.get('trends_raw_data', 'Raw Data')}", expanded=False):
                display_df = df[[
                    'trend_date', 'overall_trend', 'twitter_sentiment',
                    'stock_change_pct', 'confidence_score', 'twitter_volume'
                ]].copy()

                display_df['trend_date'] = display_df['trend_date'].dt.strftime('%Y-%m-%d')

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info(t.get('trends_no_data', 'No historical data available'))

        st.markdown("---")

        # Active Alerts
        st.markdown(f"## 🚨 {t.get('trends_alerts', 'Active Alerts')}")

        alerts_url = f"{BASE_URL}/alerts"
        alerts_response = client.get(alerts_url, timeout=10.0)
        alerts_response.raise_for_status()
        alerts_data = alerts_response.json()

        alerts = alerts_data.get('alerts', [])

        if alerts:
            for alert in alerts:
                severity = alert.get('severity', 'low')

                severity_colors = {
                    'low': 'info',
                    'medium': 'warning',
                    'high': 'warning',
                    'critical': 'error'
                }

                severity_icons = {
                    'low': 'ℹ️',
                    'medium': '⚠️',
                    'high': '⚠️',
                    'critical': '🚨'
                }

                message = f"{severity_icons.get(severity, '•')} **[{severity.upper()}]** {alert.get('message', '')}"
                created_at = alert.get('created_at', '')

                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        message += f" *({dt.strftime('%Y-%m-%d %H:%M')})*"
                    except:
                        pass

                if severity == 'critical':
                    st.error(message)
                elif severity in ['high', 'medium']:
                    st.warning(message)
                else:
                    st.info(message)
        else:
            st.success(f"✅ {t.get('trends_no_alerts', 'No active alerts')}")

        st.markdown("---")

        # Manual Analysis Trigger
        st.markdown(f"## 🔄 {t.get('trends_manual_analysis', 'Manual Analysis')}")

        if language == "fr":
            st.markdown("""
            Déclencher une nouvelle analyse de marché pour cette matière première.

            **Coût:** $0.005 par analyse

            **Note:** L'analyse automatique s'exécute quotidiennement. Utilisez ceci uniquement si vous avez besoin de données mises à jour immédiatement.
            """)
        else:
            st.markdown("""
            Trigger a new market analysis for this commodity.

            **Cost:** $0.005 per analysis

            **Note:** Automatic analysis runs daily. Use this only if you need immediate updated data.
            """)

        col1, col2 = st.columns([1, 3])

        with col1:
            force_refresh = st.checkbox(
                t.get('force_refresh', 'Force refresh (skip today\'s check)') if language == "fr" else "Force refresh (skip today's check)",
                value=False
            )

        with col2:
            if st.button(f"🚀 {t.get('trigger_analysis', 'Trigger New Analysis')}" if language == "fr" else "🚀 Trigger New Analysis", type="primary"):
                with st.spinner(t.get('analyzing', 'Analyzing market trends...') if language == "fr" else "Analyzing market trends... This may take 5-10 seconds"):
                    try:
                        analyze_url = f"{BASE_URL}/analyze/{commodity}"
                        analyze_response = client.post(
                            analyze_url,
                            params={"force_refresh": force_refresh},
                            timeout=30.0
                        )
                        analyze_response.raise_for_status()
                        result = analyze_response.json()

                        status = result.get('status')

                        if status == 'success':
                            st.success(f"✅ {t.get('success', 'Analysis completed successfully!')}")
                            st.balloons()
                            st.rerun()
                        elif status == 'exists':
                            st.info(t.get('analysis_exists', 'Analysis already exists for today. Enable Force refresh to override.') if language == "fr" else "ℹ️ Analysis already exists for today. Enable 'Force refresh' to override.")
                        else:
                            st.error(f"❌ {t.get('error', 'Analysis failed')}: {result.get('message', 'Unknown error')}")

                    except Exception as e:
                        st.error(f"❌ {t.get('error', 'Error')}: {e}")

except httpx.HTTPError as e:
    st.error(f"{t.get('error', 'API Error')}: {e}")
except Exception as e:
    st.error(f"{t.get('error', 'Error')}: {e}")

# Sidebar info
with st.sidebar:
    st.markdown("---")
    st.markdown(f"### {t.get('about_trends', 'About Market Trends')}" if language == "fr" else "### About Market Trends")

    if language == "fr":
        st.markdown("""
        **Sources de Données:**
        - Twitter/X (derniers 48h)
        - Données boursières
        - Analyse IA Perplexity
        - Prix publics historiques

        **Fréquence de Mise à Jour:**
        - Automatique: Quotidien à 9h00
        - Manuel: Sur demande ($0.005/requête)

        **Classifications de Tendance:**
        - 📈🔥 Très Haussier (>+7%)
        - 📈 Haussier (+3% à +7%)
        - ➡️ Neutre (-3% à +3%)
        - 📉 Baissier (-3% à -7%)
        - 📉💥 Très Baissier (<-7%)

        **Déclencheurs d'Alerte:**
        - Variation prix >5%
        - Changement sentiment vers baissier
        - Événements haute volatilité
        """)
    else:
        st.markdown("""
        **Data Sources:**
        - Twitter/X (last 48h tweets)
        - Stock market data
        - Perplexity AI analysis
        - Public historical prices

        **Update Frequency:**
        - Automatic: Daily at 9:00 AM
        - Manual: On-demand ($0.005/query)

        **Trend Classifications:**
        - 📈🔥 Strong Bullish (>+7%)
        - 📈 Bullish (+3% to +7%)
        - ➡️ Neutral (-3% to +3%)
        - 📉 Bearish (-3% to -7%)
        - 📉💥 Strong Bearish (<-7%)

        **Alert Triggers:**
        - Price change >5%
        - Sentiment shift to bearish
        - High volatility events
        """)

    st.markdown(f"""
    ---
    **{t.get('last_updated', 'Last updated') if language == "fr" else 'Last updated'}:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
