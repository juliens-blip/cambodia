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
from ui.config import TRENDS_URL

# Page config
st.set_page_config(page_title="Market Trends", page_icon="📈", layout="wide")

# Language selector (must be called before using translations)
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
BASE_URL = TRENDS_URL
MEF_REALTIME_BASE = "https://data.mef.gov.kh/api/v1/realtime-api"
CSX_INDEX_LAST_VALID_KEY = "macro_csx_index_last_valid"

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

def parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def format_number(value, decimals: int = 0) -> str:
    if value is None:
        return "N/A"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


@st.cache_resource
def get_csx_index_cache():
    return {"value": None, "change_percent": None, "updated_at": None}


def get_last_valid_csx_index():
    last_valid = st.session_state.get(CSX_INDEX_LAST_VALID_KEY)
    if last_valid:
        return last_valid
    cache = get_csx_index_cache()
    if cache.get("value") is not None:
        return dict(cache)
    return None


def fetch_mef_json(path: str, timeout: float = 15.0):
    url = f"{MEF_REALTIME_BASE}/{path}"
    last_error = None
    for verify in (True, False):
        try:
            with httpx.Client(verify=verify) as client:
                response = client.get(url, timeout=timeout)
            if response.status_code == 200:
                if not verify:
                    print(f"[WARN] MEF SSL verification disabled for {path}")
                return response.json()
            print(f"[DEBUG] MEF {path} status {response.status_code}")
            return None
        except httpx.TransportError as e:
            last_error = e
            if verify and "CERTIFICATE_VERIFY_FAILED" in str(e):
                print(f"[WARN] MEF SSL verification failed for {path}, retrying without verification.")
                continue
            print(f"[DEBUG] MEF {path} error: {e}")
            return None
        except Exception as e:
            print(f"[DEBUG] MEF {path} error: {e}")
            return None

    if last_error:
        print(f"[DEBUG] MEF {path} error: {last_error}")
    return None


@st.cache_data(ttl=900)
def fetch_exchange_rate(currency_id: str = "USD"):
    """Fetch exchange rate from MEF realtime API."""
    data = fetch_mef_json(f"exchange-rate?currency_id={currency_id}")
    return data.get("data") if data else None


@st.cache_data(ttl=900)
def fetch_csx_summary():
    """Fetch CSX summary from MEF realtime API."""
    data = fetch_mef_json("csx-summary")
    return data.get("data", []) if data else []


@st.cache_data(ttl=900)
def fetch_csx_index():
    """Fetch CSX index from MEF realtime API."""
    data = fetch_mef_json("csx-index")
    return data.get("data") if data else None


def remember_csx_index(csx_index):
    if not csx_index:
        return
    index_value = parse_number(csx_index.get("value"))
    if index_value is None:
        return
    payload = {
        "value": index_value,
        "change_percent": parse_number(csx_index.get("change_percent")),
        "updated_at": csx_index.get("created_at") or csx_index.get("index_time"),
    }
    st.session_state[CSX_INDEX_LAST_VALID_KEY] = payload
    cache = get_csx_index_cache()
    cache.update(payload)


def summarize_csx_summary(summary_rows):
    stats = {
        "count": 0,
        "up": 0,
        "down": 0,
        "flat": 0,
        "total_value": 0.0,
        "total_volume": 0.0
    }

    if not summary_rows:
        return stats

    for row in summary_rows:
        status = (row or {}).get("change_up_down")
        if status == "up":
            stats["up"] += 1
        elif status == "down":
            stats["down"] += 1
        else:
            stats["flat"] += 1

        value = parse_number((row or {}).get("value"))
        if value is not None:
            stats["total_value"] += value

        volume = parse_number((row or {}).get("volume"))
        if volume is not None:
            stats["total_volume"] += volume

        stats["count"] += 1

    return stats


def display_macro_indicators(exchange_rate, csx_summary_stats, csx_index):
    """Display macro indicators from MEF realtime API."""
    st.markdown(f"### {t.get('macro_indicators', 'Macro Indicators')}")
    st.caption(f"{t.get('trends_source', 'Source')}: MEF/NBC/CSX")
    if not exchange_rate and not csx_summary_stats.get("count", 0) and not csx_index:
        st.info("Macro indicators currently unavailable. Try Refresh Macro.")

    col1, col2, col3 = st.columns(3)

    with col1:
        rate_value = "N/A"
        bid = None
        ask = None
        valid_date = None
        if exchange_rate:
            avg = parse_number(exchange_rate.get("average"))
            bid = parse_number(exchange_rate.get("bid"))
            ask = parse_number(exchange_rate.get("ask"))
            valid_date = exchange_rate.get("valid_date")
            if avg is not None:
                rate_value = f"{format_number(avg)} KHR"
            elif bid is not None:
                rate_value = f"{format_number(bid)} KHR"

        st.metric(
            t.get('macro_exchange_rate', 'USD/KHR Exchange Rate'),
            rate_value
        )
        if bid is not None or ask is not None or valid_date:
            bid_text = format_number(bid)
            ask_text = format_number(ask)
            date_text = valid_date or "N/A"
            st.caption(f"Bid {bid_text} | Ask {ask_text} | {date_text}")

    with col2:
        summary_value = "N/A"
        total_value = None
        total_volume = None
        if csx_summary_stats and csx_summary_stats.get("count", 0) > 0:
            up = csx_summary_stats.get("up", 0)
            down = csx_summary_stats.get("down", 0)
            flat = csx_summary_stats.get("flat", 0)
            summary_value = (
                f"{up} {t.get('macro_up', 'Up')} / "
                f"{down} {t.get('macro_down', 'Down')} / "
                f"{flat} {t.get('macro_flat', 'Flat')}"
            )
            total_value = csx_summary_stats.get("total_value")
            total_volume = csx_summary_stats.get("total_volume")

        st.metric(
            t.get('macro_csx_summary', 'CSX Summary'),
            summary_value
        )
        if total_value is not None or total_volume is not None:
            value_text = format_number(total_value)
            volume_text = format_number(total_volume)
            st.caption(
                f"{t.get('macro_value', 'Value')}: {value_text} KHR | "
                f"{t.get('macro_volume', 'Volume')}: {volume_text}"
            )

    with col3:
        index_value = None
        change_pct = None
        updated_at = None
        fallback_used = False
        last_valid = None
        if csx_index:
            index_value = parse_number(csx_index.get("value"))
            change_pct = parse_number(csx_index.get("change_percent"))
            updated_at = csx_index.get("created_at") or csx_index.get("index_time")
            if index_value is not None:
                remember_csx_index(csx_index)

        if index_value is None:
            last_valid = get_last_valid_csx_index()
            if last_valid:
                index_value = last_valid.get("value")
                change_pct = last_valid.get("change_percent")
                fallback_used = True

        if index_value is not None:
            delta = f"{change_pct:+.2f}%" if change_pct is not None else None
            st.metric(
                t.get('macro_csx_index', 'CSX Index'),
                format_number(index_value, decimals=2),
                delta=delta
            )
            if fallback_used:
                last_updated = last_valid.get("updated_at") if last_valid else None
                if language == "fr":
                    note = (
                        f"Indice MEF indisponible (valeurs nulles). "
                        f"Dernier indice valide ({last_updated or 'N/A'})."
                    )
                    if updated_at:
                        note += f" Maj MEF: {updated_at}."
                else:
                    note = (
                        f"MEF index unavailable (null values). "
                        f"Last valid index ({last_updated or 'N/A'})."
                    )
                    if updated_at:
                        note += f" MEF updated: {updated_at}."
                st.caption(note)
        else:
            st.metric(
                t.get('macro_csx_index', 'CSX Index'),
                "N/A"
            )
            if csx_index:
                if updated_at:
                    if language == "fr":
                        st.caption(f"Indice indisponible (valeurs null). Maj: {updated_at}")
                    else:
                        st.caption(f"Index unavailable (null values). Updated: {updated_at}")

# Sidebar refresh for macro indicators (after function definitions)
if st.sidebar.button("Refresh Macro"):
    fetch_exchange_rate.clear()
    fetch_csx_summary.clear()
    fetch_csx_index.clear()
    st.sidebar.success("Macro cache cleared.")

def render_market_trends():
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
    
                # Macro Indicators (MEF/NBC/CSX)
                exchange_rate = fetch_exchange_rate()
                csx_summary = fetch_csx_summary()
                csx_index = fetch_csx_index()
                csx_summary_stats = summarize_csx_summary(csx_summary)
    
                display_macro_indicators(exchange_rate, csx_summary_stats, csx_index)
    
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
    
                        st.plotly_chart(fig_public, width="stretch")
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
    
                st.plotly_chart(fig_sentiment, width="stretch")
    
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
    
                    st.plotly_chart(fig_price, width="stretch")
    
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
    
                    st.plotly_chart(fig_confidence, width="stretch")
    
                # Data table
                with st.expander(f"📋 {t.get('trends_raw_data', 'Raw Data')}", expanded=False):
                    display_df = df[[
                        'trend_date', 'overall_trend', 'twitter_sentiment',
                        'stock_change_pct', 'confidence_score', 'twitter_volume'
                    ]].copy()
    
                    display_df['trend_date'] = display_df['trend_date'].dt.strftime('%Y-%m-%d')
    
                    st.dataframe(
                        display_df,
                        width="stretch",
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
    

if auto_refresh:
    render_market_trends = st.fragment(run_every=60)(render_market_trends)
render_market_trends()

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
