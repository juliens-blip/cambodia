"""Comparative price trends for cashew and rubber."""
import os
import httpx
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
PERIODS = [7, 30, 90, 365]

st.set_page_config(
    page_title="Price Trends",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

st.title("Price Trends")
st.markdown("Compare cashew and rubber price movements over time.")
st.markdown("---")


@st.cache_data(ttl=300)
def get_price_trends(commodity: str, days: int):
    """Fetch price trends for a commodity."""
    try:
        response = httpx.get(
            f"{API_URL}/api/prices/trends",
            params={"commodity": commodity, "days": days},
            timeout=10.0
        )
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_geopolitical_events(limit: int = 20):
    """Fetch recent geopolitical events."""
    try:
        response = httpx.get(
            f"{API_URL}/api/reports/geopolitical-events",
            params={"limit": limit},
            timeout=10.0
        )
        return response.json()
    except Exception:
        return None


def build_price_df(trends, commodity_label: str):
    """Normalize API response into a clean dataframe."""
    if not trends or not trends.get("data"):
        return None

    df = pd.DataFrame(trends["data"])
    if df.empty or "date" not in df.columns or "price_usd_per_unit" not in df.columns:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price_usd_per_unit"] = pd.to_numeric(df["price_usd_per_unit"], errors="coerce")
    if "metadata" in df.columns:
        df["metadata"] = df["metadata"].apply(normalize_metadata)
    else:
        df["metadata"] = [{} for _ in range(len(df))]
    df["metric_type"] = df["metadata"].apply(
        lambda meta: meta.get("metric_type", "unit_price_usd_per_ton")
    )
    df["value_unit"] = df["metadata"].apply(lambda meta: meta.get("value_unit"))
    df = df.dropna(subset=["date", "price_usd_per_unit"]).sort_values("date")
    df["commodity"] = commodity_label
    return df


def normalize_metadata(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def compute_stats(df: pd.DataFrame):
    """Compute summary statistics for a price series."""
    if df is None or df.empty:
        return None

    series = df["price_usd_per_unit"].dropna()
    if series.empty:
        return None

    return {
        "avg": float(series.mean()),
        "min": float(series.min()),
        "max": float(series.max()),
        "volatility": float(series.std() or 0.0)
    }


def filter_metric(df: pd.DataFrame):
    if df is None or df.empty:
        return df, "Price (USD/ton)"

    metric_types = df["metric_type"].unique().tolist()
    if len(metric_types) > 1 and "unit_price_usd_per_ton" in metric_types:
        df_display = df[df["metric_type"] == "unit_price_usd_per_ton"]
    else:
        df_display = df

    if df_display.empty:
        df_display = df

    metric_type = df_display["metric_type"].iloc[0]
    if metric_type == "export_value_usd":
        value_unit = df_display["value_unit"].iloc[0]
        if value_unit == "thousand_usd":
            return df_display, "Export Value (USD, thousands)"
        return df_display, "Export Value (USD)"

    return df_display, "Price (USD/ton)"


def build_period_table(commodity: str, label: str):
    """Build a multi-period stats table."""
    rows = []
    for period in PERIODS:
        trends = get_price_trends(commodity, period)
        df = build_price_df(trends, label)
        df_display, metric_label = filter_metric(df)
        stats = compute_stats(df_display)
        if not stats:
            continue
        rows.append({
            "Period": f"{period}d",
            "Avg (USD)": round(stats["avg"], 2),
            "Min": round(stats["min"], 2),
            "Max": round(stats["max"], 2),
            "Volatility (Std)": round(stats["volatility"], 2),
            "Change %": trends.get("change_percent", 0)
        })
    return pd.DataFrame(rows)


days = st.slider("Time window (days)", 7, 365, 90)

cashew_trends = get_price_trends("cashew", days)
rubber_trends = get_price_trends("rubber", days)

df_cashew = build_price_df(cashew_trends, "Cashew")
df_rubber = build_price_df(rubber_trends, "Rubber")

df_cashew_display, cashew_label = filter_metric(df_cashew)
df_rubber_display, rubber_label = filter_metric(df_rubber)

st.header("Comparative Trend")

if df_cashew is None and df_rubber is None:
    st.warning("No price data available yet. Make sure the API has data loaded.")
else:
    fig = go.Figure()

    if df_cashew_display is not None:
        fig.add_trace(go.Scatter(
            x=df_cashew_display["date"],
            y=df_cashew_display["price_usd_per_unit"],
            mode="lines+markers",
            name=f"Cashew ({cashew_label})",
            line=dict(color="#2ca02c", width=2),
            marker=dict(size=5)
        ))

    if df_rubber_display is not None:
        fig.add_trace(go.Scatter(
            x=df_rubber_display["date"],
            y=df_rubber_display["price_usd_per_unit"],
            mode="lines+markers",
            name=f"Rubber ({rubber_label})",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=5)
        ))

    combined = pd.concat([df for df in [df_cashew_display, df_rubber_display] if df is not None], ignore_index=True)
    start_date = combined["date"].min()
    end_date = combined["date"].max()

    events = get_geopolitical_events()
    if events and events.get("data"):
        event_rows = []
        for event in events["data"]:
            event_date = pd.to_datetime(event.get("event_date"), errors="coerce")
            if pd.isna(event_date):
                continue
            event_rows.append({
                "date": event_date.date(),
                "title": event.get("title", "Unknown"),
                "impact_level": event.get("impact_level", "unknown")
            })

        events_df = pd.DataFrame(event_rows)
        if not events_df.empty:
            in_range = events_df[
                (events_df["date"] >= start_date.date()) &
                (events_df["date"] <= end_date.date())
            ]
            for _, row in in_range.head(8).iterrows():
                fig.add_vline(
                    x=pd.to_datetime(row["date"]),
                    line_dash="dot",
                    line_color="gray",
                    annotation_text=row["title"][:40],
                    annotation_position="top left"
                )

    if cashew_label == rubber_label:
        y_label = cashew_label
    else:
        y_label = "Value (USD)"

    fig.update_layout(
        title=f"Cashew vs Rubber Price Trends (Last {days} Days)",
        xaxis_title="Date",
        yaxis_title=y_label,
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")

st.header("Current Period Stats")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cashew")
    st.caption(cashew_label)
    cashew_stats = compute_stats(df_cashew_display)
    if cashew_stats:
        metric_cols = st.columns(4)
        metric_cols[0].metric("Avg", f"${cashew_stats['avg']:,.2f}")
        metric_cols[1].metric("Min", f"${cashew_stats['min']:,.2f}")
        metric_cols[2].metric("Max", f"${cashew_stats['max']:,.2f}")
        metric_cols[3].metric("Volatility", f"{cashew_stats['volatility']:,.2f}")
        st.metric("Change %", f"{cashew_trends.get('change_percent', 0):+.2f}%")
    else:
        st.info("No cashew data for this period.")

with col2:
    st.subheader("Rubber")
    st.caption(rubber_label)
    rubber_stats = compute_stats(df_rubber_display)
    if rubber_stats:
        metric_cols = st.columns(4)
        metric_cols[0].metric("Avg", f"${rubber_stats['avg']:,.2f}")
        metric_cols[1].metric("Min", f"${rubber_stats['min']:,.2f}")
        metric_cols[2].metric("Max", f"${rubber_stats['max']:,.2f}")
        metric_cols[3].metric("Volatility", f"{rubber_stats['volatility']:,.2f}")
        st.metric("Change %", f"{rubber_trends.get('change_percent', 0):+.2f}%")
    else:
        st.info("No rubber data for this period.")

st.markdown("---")

st.header("Multi-period Summary")

left, right = st.columns(2)

with left:
    st.subheader("Cashew (7d / 30d / 90d / 365d)")
    cashew_table = build_period_table("cashew", "Cashew")
    if not cashew_table.empty:
        st.dataframe(cashew_table, width="stretch", hide_index=True)
    else:
        st.info("No cashew data available.")

with right:
    st.subheader("Rubber (7d / 30d / 90d / 365d)")
    rubber_table = build_period_table("rubber", "Rubber")
    if not rubber_table.empty:
        st.dataframe(rubber_table, width="stretch", hide_index=True)
    else:
        st.info("No rubber data available.")

st.markdown("---")

st.header("Geopolitical Events")

events = get_geopolitical_events()
if events and events.get("data"):
    event_rows = []
    for event in events["data"]:
        event_date = pd.to_datetime(event.get("event_date"), errors="coerce")
        if pd.isna(event_date):
            continue
        event_rows.append({
            "Date": event_date.date(),
            "Title": event.get("title", "Unknown"),
            "Impact": event.get("impact_level", "unknown")
        })
    events_df = pd.DataFrame(event_rows)
    if not events_df.empty:
        st.dataframe(events_df, width="stretch", hide_index=True)
    else:
        st.info("No events available yet.")
else:
    st.info("No events available yet.")
