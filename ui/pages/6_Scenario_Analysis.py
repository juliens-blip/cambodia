"""Scenario Analysis - Multi-perspective market analysis (Pessimistic, Realistic, Optimistic)."""
import streamlit as st
import sys
import os
import httpx
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.i18n.translations import get_all_translations
from ui.components import render_language_selector
from ui.config import API_BASE_URL

# Page config
st.set_page_config(page_title="Scenario Analysis", page_icon="📊", layout="wide")

# Language selector
language = render_language_selector()
t = get_all_translations(language)

# API endpoints
BASE_URL = f"{API_BASE_URL}/api/v1"
MEF_REALTIME_BASE = "https://data.mef.gov.kh/api/v1/realtime-api"
DOCS_CANDIDATES = 15
DOCS_SELECTED = 5
DOCS_THRESHOLD = 0.3
DOCS_SOURCE = "GDrive"
DOCS_MIN_WORDS = 40
DOCS_MIN_CHARS = 200
DOCS_MIN_ALPHA_RATIO = 0.25
KEYWORDS_LIMIT = 12
KEYWORD_BONUS = 0.02

GENERIC_TITLE_TOKENS = [
    "abbreviation",
    "acronym",
    "glossary",
    "appendix",
    "annex",
    "table of contents",
    "contents",
    "index",
    "test",
    "sample",
    "dummy"
]

DOMAIN_KEYWORDS = [
    "price",
    "prices",
    "export",
    "exports",
    "market",
    "demand",
    "supply",
    "yield",
    "production",
    "processing",
    "factory",
    "quality",
    "tariff",
    "trade",
    "shipment",
    "stock",
    "inventory",
    "plantation",
    "farm",
    "acreage",
    "hectare",
    "ton",
    "tons",
    "tonne",
    "capacity",
    "policy",
    "subsidy",
    "tax",
    "ban",
    "quota",
    "logistics",
    "weather",
    "drought",
    "rain",
    "pest"
]

COMMODITY_KEYWORDS = {
    "cashew": ["cashew", "anacard", "anacardium", "anacardier", "kernel", "nut"],
    "rubber": ["rubber", "latex", "caoutchouc", "rss", "tsr", "sheet"]
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "into",
    "over", "under", "about", "after", "before", "between", "their", "there", "have",
    "has", "had", "will", "would", "could", "should", "more", "most", "less", "also",
    "les", "des", "avec", "pour", "dans", "sur", "par", "une", "un", "et", "ou", "mais",
    "est", "sont", "ete", "etre", "avait", "ont", "ainsi", "comme", "sans", "plusieurs",
    "tres", "trop", "chez", "leurs", "cette", "ces"
}

# Title
st.title(f"📊 {t.get('scenario_title', 'Multi-Perspective Analysis')}")
st.markdown(t.get('scenario_subtitle', '3 scenarios based on market prices, historical documents, and Twitter/X news'))

# Sidebar - Settings
st.sidebar.markdown(f"### {t.get('settings', 'Settings')}")

# Clear cache button
if st.sidebar.button("🔄 Clear Cache", help="Clear cached data to fetch fresh results"):
    st.cache_data.clear()
    st.success("Cache cleared! Refreshing...")
    st.rerun()

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


def fetch_historical_docs(commodity: str, query: str, limit: int = DOCS_CANDIDATES, threshold: float = DOCS_THRESHOLD):
    """Fetch relevant historical documents (no caching to avoid stale errors)."""
    try:
        with httpx.Client() as client:
            url = f"{BASE_URL}/search"
            payload = {
                "query": query,
                "top_k": limit,
                "similarity_threshold": threshold,  # Lower threshold to get more results
                "commodity": commodity,
                "source": DOCS_SOURCE
            }
            print(f"[DEBUG] Searching documents: {url}", flush=True)
            # First search can take 60+ seconds (model loading)
            response = client.post(url, json=payload, timeout=120.0)
            print(f"[DEBUG] Search response: {response.status_code}", flush=True)
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] Found {data.get('count', 0)} documents", flush=True)
                return data
            else:
                print(f"[DEBUG] Search error: {response.text}", flush=True)
    except httpx.TimeoutException:
        st.warning(f"⏱️ Document search timed out (model loading can take time). Try again.")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error fetching documents: {str(e)}")
        print(f"[DEBUG] Search exception: {e}", flush=True)
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


@st.cache_data(ttl=3600)
def fetch_exchange_rate(currency_id: str = "USD"):
    """Fetch exchange rate from MEF realtime API."""
    try:
        with httpx.Client() as client:
            url = f"{MEF_REALTIME_BASE}/exchange-rate?currency_id={currency_id}"
            response = client.get(url, timeout=15.0)
            if response.status_code == 200:
                return response.json().get("data")
    except Exception as e:
        print(f"[DEBUG] MEF exchange rate error: {e}")
    return None


@st.cache_data(ttl=3600)
def fetch_csx_summary():
    """Fetch CSX summary from MEF realtime API."""
    try:
        with httpx.Client() as client:
            url = f"{MEF_REALTIME_BASE}/csx-summary"
            response = client.get(url, timeout=15.0)
            if response.status_code == 200:
                return response.json().get("data", [])
    except Exception as e:
        print(f"[DEBUG] MEF CSX summary error: {e}")
    return []


@st.cache_data(ttl=3600)
def fetch_csx_index():
    """Fetch CSX index from MEF realtime API."""
    try:
        with httpx.Client() as client:
            url = f"{MEF_REALTIME_BASE}/csx-index"
            response = client.get(url, timeout=15.0)
            if response.status_code == 200:
                return response.json().get("data")
    except Exception as e:
        print(f"[DEBUG] MEF CSX index error: {e}")
    return None


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


def build_macro_context(exchange_rate, csx_summary_stats, csx_index):
    parts = []

    if exchange_rate:
        avg_value = parse_number(exchange_rate.get("average"))
        bid_value = parse_number(exchange_rate.get("bid"))
        ask_value = parse_number(exchange_rate.get("ask"))
        if avg_value is not None or bid_value is not None or ask_value is not None:
            avg = format_number(avg_value)
            bid = format_number(bid_value)
            ask = format_number(ask_value)
            valid_date = exchange_rate.get("valid_date") or "N/A"
            parts.append(
                f"USD/KHR exchange rate (avg {avg}, bid {bid}, ask {ask}) on {valid_date}."
            )

    if csx_summary_stats and csx_summary_stats.get("count", 0) > 0:
        up = csx_summary_stats.get("up", 0)
        down = csx_summary_stats.get("down", 0)
        flat = csx_summary_stats.get("flat", 0)
        total_value = format_number(csx_summary_stats.get("total_value"))
        total_volume = format_number(csx_summary_stats.get("total_volume"))
        parts.append(
            "CSX summary: "
            f"{up} up, {down} down, {flat} flat; "
            f"total value {total_value} KHR; total volume {total_volume}."
        )

    if csx_index:
        index_value = parse_number(csx_index.get("value"))
        change_pct = parse_number(csx_index.get("change_percent"))
        if index_value is not None or change_pct is not None:
            value_text = format_number(index_value, decimals=2)
            change_text = f"{change_pct:+.2f}%" if change_pct is not None else "N/A"
            parts.append(f"CSX index: {value_text} (change {change_text}).")

    return "\n".join(parts).strip()


def extract_keywords(twitter_data: dict, commodity: str, limit: int = KEYWORDS_LIMIT) -> list[str]:
    """Extract keywords from twitter/news/market context."""
    texts = []

    if twitter_data:
        for field in ["twitter_summary", "news_summary", "market_summary"]:
            value = twitter_data.get(field)
            if value:
                texts.append(value)

        key_factors = twitter_data.get("key_factors", [])
        for factor in key_factors:
            if isinstance(factor, str):
                texts.append(factor)

        top_tweets = twitter_data.get("top_tweets", [])
        for tweet in top_tweets:
            if isinstance(tweet, dict):
                text = tweet.get("text", "")
                if text:
                    texts.append(text)
            elif isinstance(tweet, str):
                texts.append(tweet)

        news_articles = twitter_data.get("news_articles", [])
        for article in news_articles:
            if isinstance(article, dict):
                headline = article.get("headline")
                if headline:
                    texts.append(headline)

    text_blob = " ".join(texts).lower()
    tokens = re.findall(r"[\\w\\-]{3,}", text_blob, flags=re.UNICODE)

    counts = {}
    for token in tokens:
        if token.isdigit() or token in STOPWORDS:
            continue
        counts[token] = counts.get(token, 0) + 1

    for keyword in DOMAIN_KEYWORDS:
        counts[keyword] = counts.get(keyword, 0) + 1

    for keyword in COMMODITY_KEYWORDS.get(commodity, []):
        counts[keyword] = counts.get(keyword, 0) + 2

    keywords = sorted(counts.keys(), key=lambda k: (-counts[k], k))
    return keywords[:limit]


def build_search_query(commodity: str, keywords: list[str]) -> str:
    base_query = f"{commodity} market trends prices analysis"
    if not keywords:
        return base_query
    return f"{base_query} {' '.join(keywords)}"


def is_generic_title(title: str) -> bool:
    if not title:
        return False
    title_lower = title.lower()
    return any(token in title_lower for token in GENERIC_TITLE_TOKENS)


def is_text_quality(text: str) -> bool:
    if not text:
        return False
    word_count = len(text.split())
    char_count = len(text)
    if word_count < DOCS_MIN_WORDS and char_count < DOCS_MIN_CHARS:
        return False
    alpha_count = sum(1 for ch in text if ch.isalpha())
    alpha_ratio = alpha_count / max(1, char_count)
    return alpha_ratio >= DOCS_MIN_ALPHA_RATIO


def score_document(result: dict, keywords: list[str]) -> tuple[float, int]:
    similarity = result.get("similarity", 0.0)
    metadata = result.get("metadata", {})
    title = metadata.get("title", "")
    text = result.get("chunk_text", "")
    combined = f"{title} {text}".lower()

    keyword_hits = sum(1 for kw in keywords if kw in combined)
    bonus = min(0.2, keyword_hits * KEYWORD_BONUS)
    return similarity + bonus, keyword_hits


def select_documents(docs_data: dict, keywords: list[str]) -> tuple[list[dict], dict]:
    results = docs_data.get("results", []) if docs_data else []
    stats = {
        "candidate_count": len(results),
        "deduped_count": 0,
        "duplicates_removed": 0,
        "filtered_quality": 0,
        "filtered_title": 0,
        "filtered_similarity": 0,
        "selected_count": 0
    }

    if not results:
        return [], stats

    grouped = {}
    for result in results:
        doc_id = result.get("document_id")
        if not doc_id:
            continue
        grouped.setdefault(doc_id, []).append(result)

    stats["deduped_count"] = len(grouped)
    stats["duplicates_removed"] = max(0, stats["candidate_count"] - stats["deduped_count"])

    candidates = []
    for _, chunks in grouped.items():
        metadata = chunks[0].get("metadata", {})
        title = metadata.get("title", "")

        if is_generic_title(title):
            stats["filtered_title"] += 1
            continue

        chosen = None
        for chunk in sorted(chunks, key=lambda r: r.get("similarity", 0.0), reverse=True):
            if is_text_quality(chunk.get("chunk_text", "")):
                chosen = chunk
                break

        if not chosen:
            stats["filtered_quality"] += 1
            continue

        similarity = chosen.get("similarity", 0.0)
        if similarity < DOCS_THRESHOLD:
            stats["filtered_similarity"] += 1
            continue

        score, keyword_hits = score_document(chosen, keywords)
        chosen["_score"] = score
        chosen["_keyword_hits"] = keyword_hits
        candidates.append(chosen)

    selected = sorted(candidates, key=lambda r: r.get("_score", 0.0), reverse=True)[:DOCS_SELECTED]
    stats["selected_count"] = len(selected)
    return selected, stats


def build_docs_context(results: list[dict], max_chars: int = 1200) -> str:
    """Build a compact docs context string from semantic search results."""
    if not results:
        return ""

    context_parts = []
    for i, result in enumerate(results[:DOCS_SELECTED], 1):
        metadata = result.get("metadata", {})
        source = metadata.get("source", "Unknown")
        title = metadata.get("title", "Untitled")
        similarity = result.get("similarity", 0.0)
        text = result.get("chunk_text", "")

        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        header = f"[Source {i}: {source} - {title[:50]}] (Similarity: {similarity:.2f})"
        context_parts.append(f"{header}\n{text}")

    return "\n\n---\n\n".join(context_parts)


@st.cache_data(ttl=3600)
def generate_scenario_analysis(
    commodity: str,
    scenario_type: str,
    market_data: dict,
    docs_context: str,
    twitter_data: dict,
    macro_context: str
):
    """
    Generate scenario analysis using the trends API endpoint.

    scenario_type: 'pessimistic', 'realistic', or 'optimistic'
    """
    try:
        # Call the new scenario endpoint in trends API
        with httpx.Client() as client:
            url = f"{BASE_URL}/trends/scenario/{commodity}"
            params = {"scenario_type": scenario_type}
            
            # Prepare optional data
            json_data = {}
            if market_data:
                json_data["price_data"] = market_data
            if twitter_data:
                json_data["twitter_data"] = twitter_data
            if docs_context:
                json_data["docs_context"] = docs_context
            if macro_context:
                json_data["macro_context"] = macro_context
            
            # Call the API (can take 30-60 seconds for Perplexity)
            response = client.post(url, params=params, json=json_data if json_data else None, timeout=120.0)

            if response.status_code == 200:
                result = response.json()
                return {
                    'analysis': result.get('analysis', 'Analysis not available'),
                    'citations': result.get('citations', []),
                    'cost': 0  # Cost is tracked by the API internally
                }
            elif response.status_code == 429:
                return {
                    'analysis': "Rate limit exceeded. Please refresh the page in a few minutes.",
                    'citations': [],
                    'cost': 0
                }
            else:
                return {
                    'analysis': f"API error: {response.status_code}. Please try again.",
                    'citations': [],
                    'cost': 0
                }
                
    except httpx.TimeoutException:
        return {
            'analysis': "Request timed out. The AI analysis is taking longer than expected. Please try again.",
            'citations': [],
            'cost': 0
        }
    except Exception as e:
        return {
            'analysis': f"Unable to generate {scenario_type} analysis: {str(e)}",
            'citations': [],
            'cost': 0
        }


def display_data_sources(market_data, docs_selected_count: int, twitter_data):
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
        doc_count = docs_selected_count if isinstance(docs_selected_count, int) else 0
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


def display_macro_indicators(exchange_rate, csx_summary_stats, csx_index):
    """Display macro indicators from MEF realtime API."""
    st.markdown(f"### {t.get('macro_indicators', 'Macro Indicators')}")
    st.caption(f"{t.get('trends_source', 'Source')}: MEF/NBC/CSX")

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
        if csx_index:
            index_value = parse_number(csx_index.get("value"))
            change_pct = parse_number(csx_index.get("change_percent"))

        if index_value is not None:
            delta = f"{change_pct:+.2f}%" if change_pct is not None else None
            st.metric(
                t.get('macro_csx_index', 'CSX Index'),
                format_number(index_value, decimals=2),
                delta=delta
            )
        else:
            st.metric(
                t.get('macro_csx_index', 'CSX Index'),
                "N/A"
            )


def display_documents_used(results: list[dict], selection_stats: dict, commodity: str, keywords: list[str], top_k: int, threshold: float):
    """Display documents used and general exclusion reasons."""
    if language == "fr":
        title = "Documents utilises"
        no_docs = "Aucun document utilise pour cette analyse."
        reasons_title = "Pourquoi les autres documents ne sont pas retenus"
        reasons = []
        list_label = "Voir la liste des documents utilises"
    else:
        title = "Documents used"
        no_docs = "No documents were used for this analysis."
        reasons_title = "Why other documents were not selected"
        reasons = []
        list_label = "View documents used"

    keywords_preview = ", ".join(keywords[:6]) if keywords else ""

    st.markdown(f"### 📄 {title}")

    if not results:
        st.info(no_docs)
    else:
        with st.expander(f"{list_label} ({len(results)})", expanded=True):
            for r in results:
                meta = r.get("metadata", {})
                title_text = meta.get("title", "Untitled")
                source = meta.get("source", "Unknown")
                url = meta.get("url")
                similarity = r.get("similarity", 0.0)
                keyword_hits = r.get("_keyword_hits", 0)
                if language == "fr":
                    details = f"source: {source}, similarite {similarity:.2f}, mots cles: {keyword_hits}"
                else:
                    details = f"source: {source}, similarity {similarity:.2f}, keyword hits: {keyword_hits}"
                if url:
                    st.markdown(f"- [{title_text}]({url}) - {details}")
                else:
                    st.markdown(f"- {title_text} - {details}")

    stats = selection_stats or {}
    candidate_count = stats.get("candidate_count", 0)
    deduped_count = stats.get("deduped_count", 0)
    duplicates_removed = stats.get("duplicates_removed", 0)
    filtered_quality = stats.get("filtered_quality", 0)
    filtered_title = stats.get("filtered_title", 0)
    filtered_similarity = stats.get("filtered_similarity", 0)

    if language == "fr":
        reasons.extend([
            f"{candidate_count} chunks candidats recuperes, {deduped_count} documents uniques.",
            f"{duplicates_removed} doublons elimines par document_id.",
            f"{filtered_similarity} exclus pour similarite sous le seuil ({threshold:.2f}).",
            f"{filtered_quality} exclus pour qualite insuffisante (OCR bruit/texte court).",
            f"{filtered_title} exclus pour titres generiques.",
            f"Selection finale: top {top_k} documents.",
            f"Filtre actif: source={DOCS_SOURCE} et commodity={commodity}."
        ])
        if keywords_preview:
            reasons.append(
                "Classement base sur similarite + recouvrement mots cles (tweets/news/market): "
                f"{keywords_preview}."
            )
    else:
        reasons.extend([
            f"{candidate_count} candidate chunks, {deduped_count} unique documents.",
            f"{duplicates_removed} duplicates removed by document_id.",
            f"{filtered_similarity} excluded below similarity threshold ({threshold:.2f}).",
            f"{filtered_quality} excluded for low quality (OCR noise/short text).",
            f"{filtered_title} excluded for generic titles.",
            f"Final selection: top {top_k} documents.",
            f"Active filter: source={DOCS_SOURCE} and commodity={commodity}."
        ])
        if keywords_preview:
            reasons.append(
                "Ranking uses similarity + keyword overlap (tweets/news/market): "
                f"{keywords_preview}."
            )

    st.markdown(f"**{reasons_title}:**")
    for reason in reasons:
        st.markdown(f"- {reason}")


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

        # Fetch Twitter data
        twitter_data = fetch_twitter_data(commodity)
        keywords = extract_keywords(twitter_data, commodity, limit=KEYWORDS_LIMIT)
        search_query = build_search_query(commodity, keywords)

        # Fetch macro indicators (MEF/NBC/CSX)
        exchange_rate = fetch_exchange_rate()
        csx_summary = fetch_csx_summary()
        csx_index = fetch_csx_index()
        csx_summary_stats = summarize_csx_summary(csx_summary)
        macro_context = build_macro_context(exchange_rate, csx_summary_stats, csx_index)

        # Fetch historical documents
        docs_data = fetch_historical_docs(commodity, search_query, limit=DOCS_CANDIDATES, threshold=DOCS_THRESHOLD)
        docs_selected, selection_stats = select_documents(docs_data, keywords)
        docs_context = build_docs_context(docs_selected)

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
        st.sidebar.write(f"search_query: {search_query}")
        if keywords:
            st.sidebar.write("keywords: " + ", ".join(keywords[:8]))
        st.sidebar.write(f"docs_selected: {len(docs_selected)} / {selection_stats.get('candidate_count', 0)} candidates")
        if macro_context:
            st.sidebar.write(f"macro_context: {macro_context[:160]}...")

    # Display data sources summary
    display_data_sources(market_data, len(docs_selected), twitter_data)

    st.markdown("---")

    # Display macro indicators
    display_macro_indicators(exchange_rate, csx_summary_stats, csx_index)

    st.markdown("---")

    # Display documents used
    display_documents_used(docs_selected, selection_stats, commodity, keywords, DOCS_SELECTED, DOCS_THRESHOLD)

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
            pessimistic = generate_scenario_analysis(
                commodity,
                'pessimistic',
                market_data,
                docs_context,
                twitter_data,
                macro_context
            )

        display_scenario_analysis('pessimistic', pessimistic, '#ff4b4b')

    with tab2:
        st.markdown(f"## {t.get('scenario_realistic', '⚖️ Realistic Analysis')}")
        st.caption(t.get('scenario_based_on', 'Based on') + f": {t.get('scenario_market_data', 'Market data')}, {t.get('scenario_historical_docs', 'Historical documents')}, {t.get('scenario_twitter_news', 'Twitter/X news')}")

        with st.spinner(t.get('scenario_generating', 'Generating analysis...')):
            realistic = generate_scenario_analysis(
                commodity,
                'realistic',
                market_data,
                docs_context,
                twitter_data,
                macro_context
            )

        display_scenario_analysis('realistic', realistic, '#ffa500')

    with tab3:
        st.markdown(f"## {t.get('scenario_optimistic', '📈 Optimistic Analysis')}")
        st.caption(t.get('scenario_based_on', 'Based on') + f": {t.get('scenario_market_data', 'Market data')}, {t.get('scenario_historical_docs', 'Historical documents')}, {t.get('scenario_twitter_news', 'Twitter/X news')}")

        with st.spinner(t.get('scenario_generating', 'Generating analysis...')):
            optimistic = generate_scenario_analysis(
                commodity,
                'optimistic',
                market_data,
                docs_context,
                twitter_data,
                macro_context
            )

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
