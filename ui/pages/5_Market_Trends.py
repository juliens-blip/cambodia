"""Market Trends - Twitter/X sentiment and stock market analysis."""
import streamlit as st
import json
import re
import sys
import os
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector
from ui.config import TRENDS_URL, RUBBER_FARMGATE_FACTOR
from ui.lib.csx_helper import save_csx_index, get_latest_csx_index
from ui.lib.text_postprocess import postprocess_text, compact_sentences, unique_lines

# Page config
st.set_page_config(page_title="Market Trends", page_icon="📈", layout="wide")

# Language selector (must be called before using translations)
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
BASE_URL = TRENDS_URL
MEF_REALTIME_BASE = "https://data.mef.gov.kh/api/v1/realtime-api"
CSX_INDEX_LAST_VALID_KEY = "macro_csx_index_last_valid"
CSX_INDEX_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "csx_index_cache.json"

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

# Manual refresh button
if st.sidebar.button("🔄 Refresh Page"):
    st.rerun()

# Info message
st.sidebar.markdown("""
**Note**: Market Trends updates daily at 9:00 AM.
Use **Trigger New Analysis** button to force refresh.
""")

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


def normalize_display_text(text: str) -> str:
    """Collapse obvious character-split artifacts while preserving paragraphs."""
    if not isinstance(text, str) or "\n" not in text:
        return text

    lines = text.splitlines()
    if not lines:
        return text

    rebuilt = []
    buffer = []

    def flush_buffer():
        if not buffer:
            return
        if len(buffer) >= 6 and all(len(item) <= 4 and " " not in item for item in buffer):
            rebuilt.append("".join(buffer))
        else:
            rebuilt.extend(buffer)
        buffer.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            flush_buffer()
            rebuilt.append("")
            continue
        if len(stripped) <= 4 and " " not in stripped:
            buffer.append(stripped)
            continue
        flush_buffer()
        rebuilt.append(line)

    flush_buffer()
    return "\n".join(rebuilt)


def clean_display_text(text: str) -> str:
    """Apply display normalization + AI postprocessing."""
    return postprocess_text(normalize_display_text(text))


def strip_limitations_block(text: str) -> str:
    """Remove 'What I cannot provide' blocks from AI text."""
    if not text:
        return text

    lines = text.splitlines()
    cleaned_lines = []
    skip = False
    for line in lines:
        if skip:
            if line.strip() == "":
                skip = False
            continue
        if "what i cannot provide" in line.lower():
            skip = True
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def get_fx_rate_khr(exchange_rate, fallback: float = 4014) -> float:
    if not exchange_rate:
        return fallback
    avg = parse_number(exchange_rate.get("average"))
    bid = parse_number(exchange_rate.get("bid"))
    ask = parse_number(exchange_rate.get("ask"))
    return avg or bid or ask or fallback


def validate_trend_label(ai_analysis: str, current_label: str, price_change_pct: float = None) -> str:
    """
    Validate that trend label matches AI analysis content and price change.

    Phase 1.4: Ensures coherence between displayed label and analysis content.

    Args:
        ai_analysis: Full AI analysis text
        current_label: Current trend label from API
        price_change_pct: Optional price change percentage for cross-validation

    Returns:
        Validated trend label (may differ from current_label if incoherence detected)
    """
    if not ai_analysis:
        return current_label

    analysis_lower = ai_analysis.lower()

    # Check for explicit neutral/stable mentions in analysis
    neutral_indicators = [
        'neutral', 'stable', 'sideways', 'range-bound',
        '+/-3%', 'flat', 'unchanged', 'little change'
    ]

    bullish_indicators = [
        'bullish', 'upward', 'rising', 'increasing',
        'positive outlook', 'price increase', 'gains expected'
    ]

    bearish_indicators = [
        'bearish', 'downward', 'falling', 'decreasing',
        'negative outlook', 'price decline', 'losses expected'
    ]

    strong_indicators = ['strong', 'very', 'significant', 'major', 'substantial']

    # Count indicator matches
    neutral_count = sum(1 for ind in neutral_indicators if ind in analysis_lower)
    bullish_count = sum(1 for ind in bullish_indicators if ind in analysis_lower)
    bearish_count = sum(1 for ind in bearish_indicators if ind in analysis_lower)
    has_strong = any(ind in analysis_lower for ind in strong_indicators)

    # Cross-validate with price change if available
    if price_change_pct is not None:
        if -3 <= price_change_pct <= 3:
            neutral_count += 2  # Boost neutral if price is flat
        elif price_change_pct > 7:
            bullish_count += 2  # Boost bullish if price up significantly
        elif price_change_pct < -7:
            bearish_count += 2  # Boost bearish if price down significantly

    # Determine validated label
    if neutral_count > max(bullish_count, bearish_count):
        return 'neutral'
    elif bullish_count > bearish_count:
        return 'strong_bullish' if has_strong else 'bullish'
    elif bearish_count > bullish_count:
        return 'strong_bearish' if has_strong else 'bearish'

    # Default to current label if no clear signal
    return current_label


def get_last_valid_csx_index():
    """
    Get last valid CSX index with fallback chain:
    1. Session state (current session)
    2. Supabase database (persistent)
    3. Environment override (manual fallback)
    """
    # Check session state first
    last_valid = st.session_state.get(CSX_INDEX_LAST_VALID_KEY)
    if last_valid:
        return last_valid

    # Try Supabase/file helper
    cached_data = get_latest_csx_index()
    if cached_data:
        return cached_data

    # Environment override (last resort)
    env_value = parse_number(os.getenv("CSX_INDEX_FALLBACK_VALUE"))
    if env_value is not None:
        return {
            "value": env_value,
            "change_percent": parse_number(os.getenv("CSX_INDEX_FALLBACK_CHANGE_PCT")),
            "updated_at": os.getenv("CSX_INDEX_FALLBACK_UPDATED_AT"),
        }

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
    """Save CSX index to session state and Supabase/file"""
    if not csx_index:
        return
    index_value = parse_number(csx_index.get("value"))
    if index_value is None:
        return

    change_percent = parse_number(csx_index.get("change_percent"))
    updated_at = csx_index.get("created_at") or csx_index.get("index_time")

    payload = {
        "value": index_value,
        "change_percent": change_percent,
        "updated_at": updated_at,
    }

    # Save to session state (current session)
    st.session_state[CSX_INDEX_LAST_VALID_KEY] = payload

    # Save to Supabase/file (persistent)
    save_csx_index(index_value, change_percent, updated_at)


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
    # Display macro indicators from MEF realtime API.
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
            if csx_index and updated_at:
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

# Tracking last data update for sidebar display.
latest_trend_date = None

# Main content
try:
    with httpx.Client() as client:
        # Get latest trend
        latest_url = f"{BASE_URL}/latest/{commodity}"
        latest_response = client.get(latest_url, timeout=10.0)

        if latest_response.status_code == 200:
            latest = latest_response.json()
            latest_trend_date = latest.get("trend_date")

            # Display latest trend
            commodity_display = t.get(f'filter_{commodity}', commodity.capitalize())
            st.markdown(f"## {t.get('trends_latest_analysis', 'Latest Analysis')} - {commodity_display}")
            st.markdown(f"*{t.get('trends_updated', 'Updated')}: {latest.get('trend_date', 'N/A')}*")
            if language == "fr":
                st.caption("L'auto-refresh rafraichit l'interface mais ne declenche pas une nouvelle analyse.")
            else:
                st.caption("Auto-refresh updates the UI but does not trigger a new analysis.")

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                raw_trend = latest.get('overall_trend', 'neutral')
                ai_analysis = clean_display_text(latest.get('ai_analysis', ''))
                price_change = latest.get('stock_change_pct')

                known_trends = {
                    'strong_bullish',
                    'bullish',
                    'slightly_bullish',
                    'neutral',
                    'slightly_bearish',
                    'bearish',
                    'strong_bearish'
                }

                trend = raw_trend if raw_trend in known_trends else validate_trend_label(
                    ai_analysis, raw_trend, price_change
                )

                trend_label = t.get(f'trend_{trend}', trend.replace('_', ' ').title())

                trend_emoji = {
                    'strong_bullish': '📈🔥',
                    'bullish': '📈',
                    'slightly_bullish': '📈',
                    'neutral': '',
                    'slightly_bearish': '📉',
                    'bearish': '📉',
                    'strong_bearish': '📉🔥'
                }.get(trend, '')


                trend_display = f"{trend_emoji} {trend_label}".strip()

                st.metric(
                    t.get('trends_overall_trend', 'Overall Trend'),
                    trend_display,
                    delta=None
                )

            with col2:
                tweet_count = latest.get('tweet_count', 0) or 0
                twitter_volume = latest.get('twitter_volume', 0) or 0
                tweet_count_30d = latest.get('tweet_count_30d') or twitter_volume or tweet_count
                sentiment_label = latest.get('twitter_sentiment', 'neutral')
                sentiment_score = latest.get('twitter_sentiment_score')

                if sentiment_score is None:
                    sentiment_score = {
                        'bullish': 0.3,
                        'neutral': 0.0,
                        'bearish': -0.3
                    }.get(sentiment_label, 0.0)

                if sentiment_label == 'unknown' or tweet_count_30d < 10:
                    not_enough = t.get('trends_sentiment_not_enough', 'Not enough data')
                    st.metric(
                        t.get('trends_twitter_sentiment', 'Twitter Sentiment'),
                        f"{not_enough} ({tweet_count_30d} {t.get('tweets', 'tweets')} / 30d)",
                        delta=None
                    )
                else:
                    sentiment_emoji = {
                        'bullish': '😊',
                        'bearish': '😟',
                        'neutral': '😐'
                    }.get(sentiment_label, '')

                    st.metric(
                        t.get('trends_twitter_sentiment', 'Twitter Sentiment'),
                        f"{sentiment_emoji} {sentiment_label.capitalize()}".strip(),
                        delta=None
                    )
                    st.caption(
                        f"{t.get('trends_sentiment_score', 'Score')}: {sentiment_score:.2f} | "
                        f"{t.get('tweets', 'Tweets')}: {tweet_count_30d}"
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
            fx_rate = get_fx_rate_khr(exchange_rate)
            st.caption(f"FX reference: 1 USD ~ {fx_rate:,.0f} KHR (MEF/NBC)")

            st.markdown("---")

            # Twitter Analysis
            tweet_lines = []
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"### 🐦 {t.get('trends_twitter_analysis', 'Twitter/X Analysis')}")

                twitter_volume = latest.get('tweet_count_30d') or latest.get('twitter_volume', 0) or latest.get('tweet_count', 0)
                st.markdown(f"**{t.get('trends_tweet_volume', 'Tweet Volume (30d)')}:** {twitter_volume} {t.get('tweets', 'tweets')}")

                twitter_summary = clean_display_text(latest.get('twitter_summary', ''))
                if twitter_summary:
                    st.markdown(
                        f"**{t.get('trends_summary', 'Summary')}:** "
                        f"{compact_sentences(twitter_summary, 3)}"
                    )

                # Top tweets
                top_tweets = latest.get('top_tweets', [])
                tweet_lines = []
                if top_tweets:
                    for tweet in top_tweets:
                        if isinstance(tweet, dict):
                            line = tweet.get('text', '')
                            username = tweet.get('username')
                            created_at = tweet.get('created_at')
                            if username:
                                suffix = f"@{username}"
                                if created_at:
                                    suffix = f"{suffix} ({created_at})"
                                line = f"{line} - {suffix}"
                        else:
                            line = str(tweet)
                        if line:
                            tweet_lines.append(clean_display_text(line))
                    tweet_lines = unique_lines(tweet_lines)

                if tweet_lines:
                    st.markdown(f"**{t.get('trends_top_tweets', 'Top Tweets')}:**")
                    for idx, tweet in enumerate(tweet_lines[:5], 1):
                        st.markdown(f"{idx}. *\"{tweet}\"*")

            with col2:
                st.markdown(f"### 📊 {t.get('trends_stock_market', 'Stock Market')}")

                stock_price = latest.get('stock_price_usd')
                if stock_price:
                    # Display price with source
                    price_type = latest.get('price_type')
                    price_context = latest.get('price_context', '')

                    if not price_type and stock_price:
                        if 1800 <= stock_price <= 2200:
                            price_type = 'RCN'
                            price_context = 'RCN FOB Cambodia'
                        elif 6200 <= stock_price <= 6800:
                            price_type = 'Kernels'
                            price_context = 'Kernels W320 FOB Vietnam'

                    st.markdown(f"**{t.get('trends_price', 'Price')}:** ${stock_price:,.2f}/ton")

                    if commodity == 'rubber':
                        # Show conversion for rubber: USD/ton → cents/kg
                        price_cents_kg = stock_price / 10
                        st.markdown(f"*(≈ {price_cents_kg:.1f} cents/kg)*")
                        st.caption("Source: TradingEconomics / Market data")
                    else:
                        # Cashew: Show product type (RCN vs Kernels) with clear distinction
                        if price_type:
                            if price_type == 'RCN':
                                st.info(f"**{price_type}** - Raw Cashew Nuts (FOB Cambodia)")
                                st.caption("Fourchette typique: $1,800-2,200/ton")
                            elif price_type == 'Kernels':
                                st.info(f"**{price_type}** - Processed (FOB Vietnam)")
                                st.caption("Fourchette typique: $6,200-6,800/ton (W320)")
                            else:
                                st.caption(f"Type: {price_type}")
                                if price_context:
                                    st.caption(price_context)

                        fx_rate = get_fx_rate_khr(exchange_rate)
                        usd_per_kg = stock_price / 1000
                        khr_per_kg = usd_per_kg * fx_rate
                        st.caption(f"≈ ${usd_per_kg:.2f}/kg | {khr_per_kg:,.0f} KHR/kg")

                stock_change = latest.get('stock_change_pct')
                if stock_change is not None:
                    color = "green" if stock_change > 0 else "red" if stock_change < 0 else "gray"
                    st.markdown(f"**{t.get('trends_24h_change', '24h Change')}:** :{color}[{stock_change:+.2f}%]")

                stock_volume = latest.get('stock_volume')
                if stock_volume:
                    st.markdown(f"**{t.get('trends_volume', 'Volume')}:** {stock_volume:,}")

                # Rubber-specific: Show farmgate estimate
                if commodity == 'rubber':
                    farmgate_khr = latest.get('farmgate_estimate_khr_kg')
                    farmgate_usd = latest.get('farmgate_estimate_usd_kg')

                    if farmgate_khr or farmgate_usd:
                        st.markdown("---")
                        st.markdown("**Farmgate Estimate (Cambodia):**")

                        if farmgate_khr:
                            st.markdown(f"{farmgate_khr:,.0f} KHR/kg")
                        if farmgate_usd:
                            farmgate_usd_ton = farmgate_usd * 1000
                            st.markdown(f"~${farmgate_usd_ton:,.0f} USD/ton")

                        st.caption("Estimated from global prices")
                        st.caption(f"(~{RUBBER_FARMGATE_FACTOR:.0%} of FOB, based on Thailand -12%)")

                    st.markdown("---")
                    st.markdown("### Cambodia Rubber Snapshot")

                    snap_col1, snap_col2, snap_col3 = st.columns(3)
                    with snap_col1:
                        st.metric("Exports/yr", "115,000 t", help="Mainly China and Vietnam")
                    with snap_col2:
                        st.metric("Families", "80,000", help="Dependent on rubber")
                    with snap_col3:
                        st.metric("Farmgate", "3,500-4,000 KHR/kg")
                        st.caption("~$1,000-1,150 USD/ton")

                    st.caption("Destinations: China 60% | Vietnam 20% | Singapore 10% | Other 10%")
                    st.caption("Provinces: Kampong Cham, Kratie, Mondulkiri, Ratanakiri")

                elif commodity == 'cashew':
                    st.markdown("---")
                    st.markdown("### Cambodia Cashew Snapshot")

                    snap_col1, snap_col2, snap_col3 = st.columns(3)
                    with snap_col1:
                        st.metric("Production", "850,000 t")
                    with snap_col2:
                        st.metric("Exports", "815,000 t")
                    with snap_col3:
                        st.metric("Export revenue", "$1.1-1.5B")

                    snap_col4, snap_col5, snap_col6 = st.columns(3)
                    with snap_col4:
                        st.metric("Families", "500,000")
                    with snap_col5:
                        st.metric("Farmgate", "3,000-5,000 KHR/kg")
                    with snap_col6:
                        st.metric("Vietnam share", "90%")

                    fx_rate = get_fx_rate_khr(exchange_rate)
                    rcn_low, rcn_high = 1800, 2200
                    kernel_low, kernel_high = 6200, 6800
                    rcn_usd_kg = (rcn_low / 1000, rcn_high / 1000)
                    kernel_usd_kg = (kernel_low / 1000, kernel_high / 1000)
                    rcn_khr = (rcn_usd_kg[0] * fx_rate, rcn_usd_kg[1] * fx_rate)
                    kernel_khr = (kernel_usd_kg[0] * fx_rate, kernel_usd_kg[1] * fx_rate)

                    st.caption(
                        f"RCN FOB Cambodia: ${rcn_low:,.0f}-${rcn_high:,.0f}/ton "
                        f"(~${rcn_usd_kg[0]:.2f}-${rcn_usd_kg[1]:.2f}/kg | "
                        f"{rcn_khr[0]:,.0f}-{rcn_khr[1]:,.0f} KHR/kg)"
                    )
                    st.caption(
                        f"Kernels W320 FOB Vietnam: ${kernel_low:,.0f}-${kernel_high:,.0f}/ton "
                        f"(~${kernel_usd_kg[0]:.2f}-${kernel_usd_kg[1]:.2f}/kg | "
                        f"{kernel_khr[0]:,.0f}-{kernel_khr[1]:.0f} KHR/kg)"
                    )

            st.markdown("---")

            st.markdown(f"### {t.get('trends_key_factors', 'Key Factors')}")
            key_factors = latest.get('key_factors', [])

            tweet_keys = set()
            for line in tweet_lines:
                key = re.sub(r"[^a-z0-9]+", "", line.lower())
                if key:
                    tweet_keys.add(key)

            filtered_factors = []
            for factor in key_factors:
                cleaned_factor = clean_display_text(factor)
                if not cleaned_factor:
                    continue
                lowered = cleaned_factor.lower()
                if "tweet" in lowered or "retweet" in lowered:
                    continue
                factor_key = re.sub(r"[^a-z0-9]+", "", lowered)
                if factor_key:
                    if factor_key in tweet_keys or any(factor_key in tk or tk in factor_key for tk in tweet_keys):
                        continue
                filtered_factors.append(compact_sentences(cleaned_factor, 1))

            fallback_factors = {
                'cashew': [
                    "Price stability into 2026.",
                    "Vietnam processing dominance anchors RCN demand.",
                    "OEM and retail demand growth supports kernels.",
                    "Africa supply growth around 5% caps upside."
                ],
                'rubber': [
                    "APAC accounts for ~37.5% of demand.",
                    "EV and tire demand remain key drivers.",
                    "Spot prices hover near 180 cents/kg.",
                    "Supply remains balanced with regional shocks."
                ]
            }

            if len(filtered_factors) < 3:
                existing = {re.sub(r"[^a-z0-9]+", "", item.lower()) for item in filtered_factors}
                for item in fallback_factors.get(commodity, []):
                    key = re.sub(r"[^a-z0-9]+", "", item.lower())
                    if key and key in existing:
                        continue
                    filtered_factors.append(item)
                    existing.add(key)
                    if len(filtered_factors) >= 5:
                        break

            if filtered_factors:
                for idx, factor in enumerate(filtered_factors[:5], 1):
                    st.markdown(f"{idx}. {factor}")
            else:
                st.info(t.get('trends_no_data', 'No key factors extracted'))

            st.markdown("---")

            news_summary = clean_display_text(latest.get('news_summary', ''))
            market_summary = clean_display_text(latest.get('market_summary', ''))
            twitter_summary = clean_display_text(latest.get('twitter_summary', ''))
            ai_analysis = clean_display_text(latest.get('ai_analysis', ''))

            if commodity == 'rubber':
                ai_analysis = strip_limitations_block(ai_analysis)

            synthesis_summary = ai_analysis

            if commodity == 'rubber':
                tweet_count_30d = latest.get('tweet_count_30d') or latest.get('twitter_volume', 0) or latest.get('tweet_count', 0)
                news_articles = latest.get('news_articles', []) or []
                stock_price = latest.get('stock_price_usd')
                spot_cents = (stock_price / 10) if stock_price else 179.9

                limitations = [
                    f"{tweet_count_30d} tweets in 30 days.",
                    "No articles in the last 7 days." if not news_articles else "Limited recent news coverage.",
                    f"Single spot price point (~{spot_cents:.1f} cents/kg)."
                ]

                st.info("**Data limitations**\n- " + "\n- ".join(limitations))
                st.markdown("---")

                sections = []
                if market_summary:
                    sections.append(("Market overview", market_summary))
                if news_summary:
                    sections.append(("Demand signals", news_summary))
                if twitter_summary:
                    sections.append(("Sentiment snapshot", twitter_summary))
                if synthesis_summary:
                    sections.append(("Pricing and supply", synthesis_summary))

                if not sections and ai_analysis:
                    sections.append(("Market overview", ai_analysis))

                for title, content in sections[:4]:
                    st.markdown(f"### {title}")
                    st.markdown(compact_sentences(content, 3))

                if ai_analysis:
                    st.markdown("---")
                    with st.expander("Full report", expanded=False):
                        st.markdown(ai_analysis)
            else:
                if news_summary:
                    st.markdown("### News Summary")
                    st.markdown(compact_sentences(news_summary, 3))
                    st.markdown("---")

                if market_summary:
                    st.markdown("### Market Data Summary")
                    st.markdown(compact_sentences(market_summary, 3))
                    st.markdown("---")

                if synthesis_summary:
                    st.markdown("### Integrated Synthesis")
                    st.markdown(compact_sentences(synthesis_summary, 3))
                    st.markdown("---")

                show_full = not (news_summary or market_summary or synthesis_summary)
                if show_full:
                    with st.expander(f"{t.get('trends_ai_analysis', 'Full AI Analysis')}", expanded=False):
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
                price_basis = stats.get("price_basis")
                price_type = stats.get("price_type")
                current_price = stats.get("current", 0)
                basis_label = None

                # Detect basis from API or infer from price
                if price_basis == "kernel_fob_vietnam_w320":
                    basis_label = "Kernels W320 FOB Vietnam"
                elif price_basis == "rcn_fob_cambodia":
                    basis_label = "RCN FOB Cambodia"
                elif price_basis == "tsr20_spot":
                    basis_label = "TSR20 spot benchmark"
                elif commodity == 'cashew' and current_price:
                    # Fallback: auto-detect from price range
                    if current_price > 5000:
                        basis_label = "Kernels W320 FOB Vietnam (inferred)"
                    elif current_price < 3000:
                        basis_label = "RCN FOB Cambodia (inferred)"
                elif commodity == 'rubber':
                    basis_label = "Natural rubber spot"

                if basis_label or price_type:
                    details = basis_label or price_type or "Benchmark"
                    st.info(f"**Segment:** {details}")
                if price_basis:
                    st.caption(f"price_basis: {price_basis}")
                if price_type:
                    st.caption(f"price_type: {price_type}")

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

                if current_price:
                    if commodity == 'cashew':
                        fx_rate = get_fx_rate_khr(exchange_rate)
                        usd_per_kg = current_price / 1000
                        khr_per_kg = usd_per_kg * fx_rate
                        st.caption(f"Current: ~${usd_per_kg:.2f}/kg | {khr_per_kg:,.0f} KHR/kg")
                    elif commodity == 'rubber':
                        price_cents = current_price / 10
                        st.caption(f"Current: ~{price_cents:.1f} cents/kg")

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
                t.get('force_refresh', 'Force refresh (always get fresh data)') if language == "fr" else "Force refresh (always get fresh data)",
                value=True,  # Default to True - user clicking manual trigger wants fresh data
                help="Recommended: always enabled for manual triggers"
            )

        with col2:
            if st.button(f"🚀 {t.get('trigger_analysis', 'Trigger New Analysis')}" if language == "fr" else "🚀 Trigger New Analysis", type="primary"):
                with st.spinner(t.get('analyzing', 'Analyzing market trends...') if language == "fr" else "Analyzing market trends... This may take 30-60 seconds"):
                    try:
                        analyze_url = f"{BASE_URL}/analyze/{commodity}"
                        # Increased timeout to 90s - Perplexity can take 30-60s
                        analyze_response = client.post(
                            analyze_url,
                            params={"force_refresh": force_refresh},
                            timeout=90.0
                        )
                        analyze_response.raise_for_status()
                        result = analyze_response.json()

                        status = result.get('status')

                        if status == 'success':
                            st.success(f"✅ {t.get('success', 'Analysis completed successfully!')}")
                            # Show the new date
                            new_date = result.get('data', {}).get('trend_date', 'N/A')
                            st.info(f"New analysis date: {new_date}")
                            st.balloons()
                            st.rerun()
                        elif status == 'exists':
                            st.info(t.get('analysis_exists', 'Analysis already exists for today. Enable Force refresh to override.') if language == "fr" else "ℹ️ Analysis already exists for today. Enable 'Force refresh' to override.")
                        else:
                            st.error(f"❌ {t.get('error', 'Analysis failed')}: {result.get('message', 'Unknown error')}")

                    except httpx.TimeoutException:
                        st.error("⏱️ Request timed out. The analysis may still be running in the background. Please refresh in 30 seconds.")
                    except httpx.HTTPStatusError as e:
                        st.error(f"❌ API Error ({e.response.status_code}): {e.response.text[:200]}")
                    except Exception as e:
                        st.error(f"❌ {t.get('error', 'Error')}: {type(e).__name__}: {e}")

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
        - Twitter/X (derniers 30j)
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
        - Twitter/X (last 30d tweets)
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

    last_updated_label = t.get('last_updated', 'Last updated') if language == "fr" else "Last updated"
    last_updated_value = latest_trend_date or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"""
    ---
    **{last_updated_label}:** {last_updated_value}
    """)
