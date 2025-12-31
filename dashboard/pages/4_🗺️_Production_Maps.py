"""Production maps with geospatial data."""
import os
import httpx
import pandas as pd
import folium
from dotenv import load_dotenv
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import streamlit as st

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Production Maps",
    page_icon=":world_map:",
    layout="wide"
)

st.title("Production Maps")
st.markdown("Geospatial view of production data by province.")
st.markdown("---")


@st.cache_data(ttl=300)
def get_production(commodity: str, year: int):
    """Fetch production data for a commodity and year."""
    try:
        response = httpx.get(
            f"{API_URL}/api/production",
            params={"commodity": commodity, "year": year},
            timeout=10.0
        )
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_geospatial(commodity: str, year: int):
    """Fetch geospatial production data for mapping."""
    try:
        response = httpx.get(
            f"{API_URL}/api/production/geospatial",
            params={"commodity": commodity, "year": year},
            timeout=10.0
        )
        return response.json()
    except Exception:
        return None


def build_map(points, mode: str, color: str):
    """Build a folium map for geospatial points."""
    coords = []
    weights = []
    for point in points:
        geo = point.get("geolocation") or {}
        lat = geo.get("lat")
        lon = geo.get("lon")
        if lat is None or lon is None:
            continue
        coords.append([lat, lon])
        weights.append(float(point.get("production_tons") or 0))

    if not coords:
        return None

    center = [
        sum(lat for lat, _ in coords) / len(coords),
        sum(lon for _, lon in coords) / len(coords)
    ]

    fmap = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

    if mode == "Heatmap":
        heat_data = [[lat, lon, weight] for (lat, lon), weight in zip(coords, weights)]
        HeatMap(heat_data, radius=16, blur=12, max_zoom=7).add_to(fmap)
        return fmap

    max_weight = max(weights) if weights else 1
    for point in points:
        geo = point.get("geolocation") or {}
        lat = geo.get("lat")
        lon = geo.get("lon")
        if lat is None or lon is None:
            continue
        weight = float(point.get("production_tons") or 0)
        radius = 4 + (weight / max_weight) * 16 if max_weight else 6
        province = point.get("province", "Unknown")
        tooltip = f"{province} - {weight:,.0f} tons"
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=tooltip
        ).add_to(fmap)

    return fmap


col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    commodity = st.selectbox("Commodity", ["cashew", "rubber"])

with col2:
    year = st.selectbox("Year", [2024, 2023, 2022, 2021])

with col3:
    map_mode = st.selectbox("Map Mode", ["Markers", "Heatmap"])

production = get_production(commodity, year)
geospatial = get_geospatial(commodity, year)

st.header("Production Summary")

if production and production.get("data"):
    df_prod = pd.DataFrame(production["data"])
    area_series = pd.to_numeric(
        df_prod.get("area_hectares", pd.Series(dtype=float)),
        errors="coerce"
    ).fillna(0)
    prod_series = pd.to_numeric(
        df_prod.get("production_tons", pd.Series(dtype=float)),
        errors="coerce"
    ).fillna(0)
    total_area = area_series.sum()
    total_prod = prod_series.sum()
    provinces_count = df_prod.get("province", pd.Series(dtype=str)).nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Provinces", f"{provinces_count:,}")
    col2.metric("Total Area (hectares)", f"{total_area:,.0f}")
    col3.metric("Total Production (tons)", f"{total_prod:,.0f}")
else:
    st.info("No production data available for this selection.")

st.markdown("---")

st.header("Map View")

if geospatial and geospatial.get("data"):
    color = "#2ca02c" if commodity == "cashew" else "#1f77b4"
    fmap = build_map(geospatial["data"], map_mode, color)
    if fmap:
        st_folium(fmap, width=900, height=520)
    else:
        st.info("Geolocation data is missing for this selection.")
else:
    st.info("Geolocation data is missing for this selection.")

st.markdown("---")

st.header("Production Table")

if production and production.get("data"):
    st.dataframe(df_prod, width="stretch")
else:
    st.info("No production records to display.")
