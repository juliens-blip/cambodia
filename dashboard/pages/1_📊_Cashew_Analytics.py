"""Cashew market analytics page."""
import os
import streamlit as st
import httpx
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

st.set_page_config(page_title="Cashew Analytics", page_icon="📊", layout="wide")

st.title("📊 Cashew Market Analytics")
st.markdown("Comprehensive analysis of Cambodia's cashew market")
st.markdown("---")

# API base URL
load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_price():
    """Get latest cashew price."""
    try:
        response = httpx.get(f"{API_URL}/api/prices/latest?commodity=cashew", timeout=10.0)
        return response.json()
    except:
        return None


@st.cache_data(ttl=300)
def get_price_trends(days=30):
    """Get price trends."""
    try:
        response = httpx.get(
            f"{API_URL}/api/prices/trends?commodity=cashew&days={days}",
            timeout=10.0
        )
        return response.json()
    except:
        return None


@st.cache_data(ttl=300)
def get_latest_report():
    """Get latest report."""
    try:
        response = httpx.get(
            f"{API_URL}/api/reports/latest?commodity=cashew&report_type=daily",
            timeout=10.0
        )
        return response.json()
    except:
        return None


def normalize_metadata(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def metric_label_from_metadata(metadata):
    metric_type = metadata.get("metric_type")
    if metric_type == "export_value_usd":
        if metadata.get("value_unit") == "thousand_usd":
            return "Export Value (USD, thousands)", "Value Change"
        return "Export Value (USD)", "Value Change"
    return "Price (USD/ton)", "Price Change"


# Latest Price Section
st.header("💰 Current Market Price")

col1, col2, col3 = st.columns(3)

latest_price = get_latest_price()
latest_metadata = normalize_metadata(latest_price.get("metadata", {})) if latest_price else {}
price_label, change_label = metric_label_from_metadata(latest_metadata)

if latest_price:
    with col1:
        st.metric(
            price_label,
            f"${latest_price.get('price_usd_per_unit', 0):,.2f}",
            delta=None
        )

    with col2:
        st.metric(
            "Volume (tons)",
            f"{latest_price.get('volume_tons', 0):,}",
            delta=None
        )

    with col3:
        st.metric(
            "Destination",
            latest_price.get('destination_country', 'Unknown'),
            delta=None
        )
else:
    st.warning("⚠️ Unable to load latest price data. Make sure API is running.")

st.markdown("---")

# Price Trends
st.header("📈 Price Trends")

days = st.slider("Select time period (days)", 7, 365, 30)

trends = get_price_trends(days)

if trends and trends.get('data'):
    df = pd.DataFrame(trends['data'])
    if "metadata" in df.columns:
        df["metadata"] = df["metadata"].apply(normalize_metadata)
    else:
        df["metadata"] = [{} for _ in range(len(df))]
    df["metric_type"] = df["metadata"].apply(
        lambda meta: meta.get("metric_type", "unit_price_usd_per_ton")
    )
    metric_types = df["metric_type"].unique().tolist()
    if len(metric_types) > 1 and "unit_price_usd_per_ton" in metric_types:
        df_display = df[df["metric_type"] == "unit_price_usd_per_ton"]
    else:
        df_display = df

    if df_display.empty:
        df_display = df

    display_metric_type = df_display["metric_type"].iloc[0]
    if display_metric_type == "export_value_usd":
        value_unit = df_display["metadata"].iloc[0].get("value_unit")
        if value_unit == "thousand_usd":
            chart_label = "Export Value (USD, thousands)"
        else:
            chart_label = "Export Value (USD)"
        change_label = "Value Change"
    else:
        chart_label = "Price (USD/ton)"
        change_label = "Price Change"

    # Create Plotly chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_display['date'],
        y=df_display['price_usd_per_unit'],
        mode='lines+markers',
        name=chart_label,
        line=dict(color='green', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f"Cashew Price Trend (Last {days} Days)",
        xaxis_title="Date",
        yaxis_title=chart_label,
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, width="stretch")

    # Show change
    st.metric(
        change_label,
        f"{trends.get('change_percent', 0):+.2f}%",
        delta=f"{trends.get('change_percent', 0):+.2f}%"
    )
else:
    st.info("📊 No trend data available yet")

st.markdown("---")

# Latest Report
st.header("📝 Latest Market Report")

report = get_latest_report()

if report:
    st.markdown(report.get('content', 'No content available'))
else:
    st.info("📄 No reports available yet")

st.markdown("---")

# Quick Actions
st.header("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button("📥 Download CSV"):
        if trends and trends.get('data'):
            df = pd.DataFrame(trends['data'])
            csv = df.to_csv(index=False)
            st.download_button(
                "Download",
                csv,
                "cashew_prices.csv",
                "text/csv"
            )

with col3:
    if st.button("📊 View All Reports"):
        st.switch_page("pages/Reports.py")
