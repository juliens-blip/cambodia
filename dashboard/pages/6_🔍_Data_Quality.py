"""
Data Quality Monitoring Page

Displays comprehensive data quality metrics, alerts, and visualizations
for the Cambodia Agri Analytics platform.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Data Quality - Cambodia Agri Analytics",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Data Quality Monitoring")
st.markdown("Monitor data integrity, coverage, and quality metrics across all sources")

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_quality_report():
    """Load the latest quality report JSON."""
    report_path = Path(__file__).parent.parent.parent / "reports" / "data_quality_report.json"

    if not report_path.exists():
        return None

    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_quality_score(score_data):
    """Render quality score gauge."""
    overall_score = score_data.get("overall", 0)

    # Determine color based on score
    if overall_score >= 80:
        color = "green"
    elif overall_score >= 60:
        color = "orange"
    else:
        color = "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Quality Score"},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "gray"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 60
            }
        }
    ))

    fig.update_layout(height=300)
    return fig


def render_component_scores(score_data):
    """Render component scores breakdown."""
    components = score_data.get("components", {})

    if not components:
        return None

    df = pd.DataFrame([
        {"Component": "Completeness (40%)", "Score": components.get("completeness", 0)},
        {"Component": "Validity (30%)", "Score": components.get("validity", 0)},
        {"Component": "Consistency (20%)", "Score": components.get("consistency", 0)},
        {"Component": "Timeliness (10%)", "Score": components.get("timeliness", 0)}
    ])

    fig = px.bar(
        df,
        x="Component",
        y="Score",
        color="Score",
        color_continuous_scale=["red", "orange", "green"],
        range_color=[0, 100],
        title="Quality Score Components"
    )

    fig.update_layout(height=300, showlegend=False)
    fig.update_yaxis(range=[0, 100])

    return fig


def render_coverage_chart(coverage_data):
    """Render coverage metrics chart."""
    prices = coverage_data.get("prices", {})
    by_commodity = prices.get("by_commodity", {})

    if not by_commodity:
        return None

    df = pd.DataFrame([
        {"Commodity": commodity.capitalize(), "Records": count}
        for commodity, count in by_commodity.items()
    ])

    fig = px.pie(
        df,
        values="Records",
        names="Commodity",
        title="Price Data Coverage by Commodity",
        hole=0.4
    )

    fig.update_layout(height=300)
    return fig


def render_completeness_heatmap(completeness_data):
    """Render completeness heatmap."""
    if "prices" not in completeness_data and "production" not in completeness_data:
        return None

    # Prepare data for heatmap
    tables = []
    fields = []
    values = []

    for table, fields_dict in completeness_data.items():
        if table == "error":
            continue
        for field, pct in fields_dict.items():
            tables.append(table.capitalize())
            fields.append(field.replace("_", " ").title())
            values.append(pct)

    if not tables:
        return None

    df = pd.DataFrame({
        "Table": tables,
        "Field": fields,
        "Completeness": values
    })

    # Pivot for heatmap
    pivot = df.pivot(index="Field", columns="Table", values="Completeness")

    fig = px.imshow(
        pivot,
        color_continuous_scale=["red", "yellow", "green"],
        aspect="auto",
        title="Data Completeness Heatmap (%)",
        labels=dict(color="Completeness %")
    )

    fig.update_layout(height=400)
    return fig


def render_temporal_gaps_chart(temporal_data):
    """Render temporal gaps visualization."""
    price_gaps = temporal_data.get("price_gaps", {})
    gap_details = price_gaps.get("gap_details", [])

    if not gap_details:
        return None

    # Extract gap information
    data = []
    for gap in gap_details:
        commodity_id = gap.get("commodity_id", "unknown")[:8]  # Short ID
        source = gap.get("source", "unknown")
        total = gap.get("total_records", 0)
        gaps = gap.get("gaps_count", 0)
        largest = gap.get("largest_gap_days", 0)

        data.append({
            "Combination": f"{source}",
            "Total Records": total,
            "Gaps Count": gaps,
            "Largest Gap (days)": largest
        })

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="Combination",
        y="Largest Gap (days)",
        color="Gaps Count",
        title="Temporal Gaps in Price Data",
        hover_data=["Total Records", "Gaps Count"]
    )

    fig.update_layout(height=300)
    return fig


def render_alerts_section(recommendations):
    """Render alerts and recommendations section."""
    if not recommendations:
        st.success("No alerts - data quality is good!")
        return

    # Group by priority
    high_priority = [r for r in recommendations if r["priority"] == "HIGH"]
    medium_priority = [r for r in recommendations if r["priority"] == "MEDIUM"]
    low_priority = [r for r in recommendations if r["priority"] == "LOW"]

    # High priority alerts
    if high_priority:
        st.error(f"🚨 {len(high_priority)} High Priority Issues")
        for rec in high_priority:
            with st.expander(f"❗ {rec['issue']}", expanded=True):
                st.markdown(f"**Category:** {rec['category']}")
                st.markdown(f"**Issue:** {rec['issue']}")
                st.markdown(f"**Recommendation:** {rec['recommendation']}")
                st.code(rec['action'], language="bash")

    # Medium priority
    if medium_priority:
        st.warning(f"⚠️ {len(medium_priority)} Medium Priority Issues")
        for rec in medium_priority:
            with st.expander(f"⚠️ {rec['issue']}"):
                st.markdown(f"**Category:** {rec['category']}")
                st.markdown(f"**Recommendation:** {rec['recommendation']}")
                st.code(rec['action'], language="bash")

    # Low priority
    if low_priority:
        st.info(f"ℹ️ {len(low_priority)} Low Priority Suggestions")
        for rec in low_priority:
            with st.expander(f"💡 {rec['issue']}"):
                st.markdown(f"**Category:** {rec['category']}")
                st.markdown(f"**Recommendation:** {rec['recommendation']}")
                st.code(rec['action'], language="bash")


def render_summary_stats(summary):
    """Render summary statistics cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Price Records", summary.get("prices_count", 0))

    with col2:
        st.metric("Production Records", summary.get("production_count", 0))

    with col3:
        sources = summary.get("price_sources", [])
        st.metric("Data Sources", len(sources))

    with col4:
        st.metric("Commodities", summary.get("commodities_count", 0))


def render_consistency_section(consistency_data):
    """Render inter-source consistency section."""
    source_comp = consistency_data.get("source_comparison", {})

    if not source_comp or source_comp.get("total_overlapping_records", 0) == 0:
        st.info("No overlapping records between sources for comparison")
        return

    st.subheader("Inter-Source Consistency")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Overlapping Records",
            source_comp.get("total_overlapping_records", 0),
            help="Records with same commodity, date from different sources"
        )

    with col2:
        st.metric(
            "High Discrepancy (>20%)",
            source_comp.get("high_discrepancy_count", 0),
            delta=f"-{source_comp.get('high_discrepancy_count', 0)} ideal",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Avg Difference",
            f"{source_comp.get('avg_difference_percentage', 0):.2f}%",
            delta=f"-{source_comp.get('avg_difference_percentage', 0):.2f}% ideal",
            delta_color="inverse"
        )

    # Show sample comparisons
    comparisons = source_comp.get("sample_comparisons", [])
    if comparisons:
        st.markdown("**Sample Discrepancies:**")

        df = pd.DataFrame(comparisons)
        df["MEF Value"] = df["mef_value"].apply(lambda x: f"${x:,.2f}")
        df["WITS Value"] = df["wits_value"].apply(lambda x: f"${x:,.2f}")
        df["Difference"] = df["difference_percentage"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            df[["date", "MEF Value", "WITS Value", "Difference"]],
            hide_index=True,
            width="stretch"
        )

        st.warning(
            "⚠️ Large discrepancies detected between MEF and WITS. "
            "This may be due to different measurement units (thousand_usd vs usd) or data collection methodologies."
        )


def main():
    """Main function."""

    # Sidebar controls
    st.sidebar.header("Controls")

    if st.sidebar.button("🔄 Refresh Report", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("📊 Generate New Audit", width="stretch"):
        with st.spinner("Running data quality audit..."):
            import subprocess
            try:
                # Run audit script
                result = subprocess.run(
                    ["python", "scripts/audit_data_quality.py"],
                    cwd=Path(__file__).parent.parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    st.sidebar.success("✅ Audit completed!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Audit failed: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This page monitors data quality across all sources. "
        "Metrics are calculated based on integrity, completeness, consistency, and timeliness."
    )

    # Load report
    report = load_quality_report()

    if not report:
        st.warning(
            "📝 No quality report found. Click 'Generate New Audit' to create one."
        )

        if st.button("🔧 Generate Initial Report"):
            st.info("Running audit script...")
            st.code("python scripts/audit_data_quality.py", language="bash")

        return

    # Display metadata
    metadata = report.get("metadata", {})
    generated_at = metadata.get("generated_at", "Unknown")

    st.caption(f"Report generated: {generated_at}")

    # Summary section
    st.header("📊 Summary")
    summary = report.get("summary", {})
    render_summary_stats(summary)

    st.markdown("---")

    # Quality Score section
    st.header("🎯 Quality Score")

    # For now, calculate a simple score since the report doesn't include it
    # In production, this would come from the data_quality_service
    integrity = report.get("integrity_checks", {})
    prices_int = integrity.get("prices", {})
    null_pct = prices_int.get("null_values", {}).get("null_percentage", 0)

    # Simple scoring
    completeness_score = 100 - null_pct
    validity_score = 100  # Placeholder
    consistency_score = 85  # Placeholder
    timeliness_score = 80  # Placeholder

    overall_score = (
        completeness_score * 0.4 +
        validity_score * 0.3 +
        consistency_score * 0.2 +
        timeliness_score * 0.1
    )

    score_data = {
        "overall": round(overall_score, 2),
        "components": {
            "completeness": round(completeness_score, 2),
            "validity": round(validity_score, 2),
            "consistency": round(consistency_score, 2),
            "timeliness": round(timeliness_score, 2)
        }
    }

    col1, col2 = st.columns([1, 2])

    with col1:
        fig = render_quality_score(score_data)
        if fig:
            st.plotly_chart(fig, width="stretch")

    with col2:
        fig = render_component_scores(score_data)
        if fig:
            st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Alerts and Recommendations
    st.header("🚨 Alerts & Recommendations")
    recommendations = report.get("recommendations", [])
    render_alerts_section(recommendations)

    st.markdown("---")

    # Coverage Metrics
    st.header("📈 Coverage Metrics")

    col1, col2 = st.columns(2)

    coverage = report.get("coverage_metrics", {})

    with col1:
        fig = render_coverage_chart(coverage)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No coverage data available")

    with col2:
        # Source breakdown
        prices = coverage.get("prices", {})
        by_source = prices.get("by_source", {})

        if by_source:
            df = pd.DataFrame([
                {"Source": source, "Records": count}
                for source, count in by_source.items()
            ])

            fig = px.bar(
                df,
                x="Source",
                y="Records",
                title="Price Data Coverage by Source",
                color="Source"
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, width="stretch")

    # Temporal coverage
    temporal_cov = coverage.get("price_temporal_coverage", {})
    if temporal_cov:
        st.markdown("**Temporal Coverage (Prices):**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Earliest Date", temporal_cov.get("earliest_date", "N/A"))
        with col2:
            st.metric("Latest Date", temporal_cov.get("latest_date", "N/A"))
        with col3:
            st.metric("Total Records", temporal_cov.get("total_records", 0))

    st.markdown("---")

    # Consistency Checks
    st.header("🔄 Consistency Checks")
    consistency = report.get("consistency_checks", {})
    render_consistency_section(consistency)

    st.markdown("---")

    # Temporal Continuity
    st.header("📅 Temporal Continuity")
    temporal = report.get("temporal_checks", {})

    col1, col2 = st.columns(2)

    with col1:
        price_gaps = temporal.get("price_gaps", {})
        st.metric(
            "Price Data Gaps",
            price_gaps.get("combinations_with_gaps", 0),
            help="Number of commodity-source combinations with date gaps > 60 days"
        )

    with col2:
        prod_gaps = temporal.get("production_gaps", {})
        st.metric(
            "Production Data Gaps",
            prod_gaps.get("combinations_with_gaps", 0),
            help="Number of commodity-province combinations with missing years"
        )

    # Temporal gaps chart
    fig = render_temporal_gaps_chart(temporal)
    if fig:
        st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Data Integrity Details
    st.header("🔍 Data Integrity Details")

    tab1, tab2 = st.tabs(["Prices", "Production"])

    with tab1:
        prices_int = integrity.get("prices", {})

        # Null values
        st.subheader("Null Values")
        null_vals = prices_int.get("null_values", {})
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Null commodity_id", null_vals.get("null_commodity_id", 0))
        with col2:
            st.metric("Null date", null_vals.get("null_date", 0))
        with col3:
            st.metric("Null price", null_vals.get("null_price_usd_per_unit", 0))
        with col4:
            st.metric("Null source", null_vals.get("null_source", 0))

        # Value validation
        st.subheader("Value Validation")
        val_check = prices_int.get("value_validation", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Negative Prices", val_check.get("negative_prices", 0))
        with col2:
            st.metric("Zero Prices", val_check.get("zero_prices", 0))
        with col3:
            st.metric("Outliers (>3σ)", val_check.get("outliers_count", 0))

        # Price statistics
        st.markdown("**Price Statistics:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Mean", f"${val_check.get('mean_price', 0):,.2f}")
        with col2:
            st.metric("Std Dev", f"${val_check.get('stdev_price', 0):,.2f}")
        with col3:
            st.metric("Min", f"${val_check.get('min_price', 0):,.2f}")
        with col4:
            st.metric("Max", f"${val_check.get('max_price', 0):,.2f}")

        # Unit consistency
        st.subheader("Unit Consistency")
        units = prices_int.get("unit_consistency", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("thousand_usd", units.get("thousand_usd_records", 0))
        with col2:
            st.metric("usd", units.get("usd_records", 0))
        with col3:
            st.metric("No unit specified", units.get("no_unit_specified", 0))

        if units.get("warning"):
            st.warning(f"⚠️ {units['warning']}")

        # Duplicates
        st.subheader("Duplicates")
        dups = prices_int.get("duplicates", {})
        dup_count = dups.get("potential_duplicates", 0)

        if dup_count > 0:
            st.error(f"🚨 Found {dup_count} potential duplicate records")
            st.markdown(
                "This indicates that unique constraints may not be properly applied. "
                "Run the migration to fix this issue."
            )
        else:
            st.success("✅ No duplicates detected")

    with tab2:
        prod_int = integrity.get("production", {})

        total_prod = prod_int.get("null_values", {}).get("total_records", 0)

        if total_prod == 0:
            st.warning(
                "⚠️ No production data found. "
                "Run seed with --include-odc flag to collect production data."
            )
        else:
            # Completeness
            st.subheader("Data Completeness")
            completeness = prod_int.get("data_completeness", {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Area Coverage", f"{completeness.get('area_hectares_coverage', 0)}%")
            with col2:
                st.metric("Production Coverage", f"{completeness.get('production_tons_coverage', 0)}%")
            with col3:
                st.metric("Yield Coverage", f"{completeness.get('yield_kg_per_ha_coverage', 0)}%")
            with col4:
                st.metric("Geolocation Coverage", f"{completeness.get('geolocation_coverage', 0)}%")


if __name__ == "__main__":
    main()
