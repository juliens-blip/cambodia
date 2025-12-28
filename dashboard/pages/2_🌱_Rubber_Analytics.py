"""Rubber market analytics page."""
import os
import streamlit as st
import httpx
import json
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

st.set_page_config(page_title="Rubber Analytics", page_icon="🌱", layout="wide")

st.title("🌱 Rubber Market Analytics")
st.markdown("Comprehensive analysis of Cambodia's rubber market")
st.markdown("---")

# API base URL
load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=300)
def get_latest_price():
    """Get latest rubber price."""
    try:
        response = httpx.get(f"{API_URL}/api/prices/latest?commodity=rubber", timeout=10.0)
        return response.json()
    except:
        return None


@st.cache_data(ttl=300)
def get_price_trends(days=30):
    """Get price trends."""
    try:
        response = httpx.get(
            f"{API_URL}/api/prices/trends?commodity=rubber&days={days}",
            timeout=10.0
        )
        return response.json()
    except:
        return None


@st.cache_data(ttl=300)
def get_production_data(year=2024):
    """Get production data."""
    try:
        response = httpx.get(
            f"{API_URL}/api/production?commodity=rubber&year={year}",
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


# Latest Price
st.header("💰 Current Market Price")

col1, col2, col3 = st.columns(3)

latest_price = get_latest_price()
latest_metadata = normalize_metadata(latest_price.get("metadata", {})) if latest_price else {}
price_label, change_label = metric_label_from_metadata(latest_metadata)

if latest_price:
    with col1:
        st.metric(
            price_label,
            f"${latest_price.get('price_usd_per_unit', 0):,.2f}"
        )

    with col2:
        st.metric(
            "Volume (tons)",
            f"{latest_price.get('volume_tons', 0):,}"
        )

    with col3:
        st.metric(
            "Quality",
            latest_price.get('quality_grade', 'Standard')
        )
else:
    st.warning("⚠️ Unable to load price data")

st.markdown("---")

# Price Trends
st.header("📈 Price Trends")

days = st.slider("Time period (days)", 7, 365, 30)

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

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_display['date'],
        y=df_display['price_usd_per_unit'],
        mode='lines+markers',
        name=chart_label,
        line=dict(color='blue', width=2)
    ))

    fig.update_layout(
        title=f"Rubber Price Trend (Last {days} Days)",
        xaxis_title="Date",
        yaxis_title=chart_label,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 No trend data available")

st.markdown("---")

# Production Stats
st.header("🌳 Production Statistics")

year = st.selectbox("Select Year", [2024, 2023, 2022, 2021])

production = get_production_data(year)

if production and production.get('data'):
    df_prod = pd.DataFrame(production['data'])

    col1, col2 = st.columns(2)

    with col1:
        total_area = df_prod['area_hectares'].sum() if 'area_hectares' in df_prod else 0
        st.metric("Total Area (hectares)", f"{total_area:,.0f}")

    with col2:
        total_prod = df_prod['production_tons'].sum() if 'production_tons' in df_prod else 0
        st.metric("Total Production (tons)", f"{total_prod:,.0f}")

    st.dataframe(df_prod, use_container_width=True)
else:
    st.info("🌳 No production data available for this year")
