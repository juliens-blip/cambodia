"""
Data Quality System - Usage Examples

This file demonstrates how to use the data quality system in different contexts.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

from app.services.data_quality_service import DataQualityService

load_dotenv()


# Example 1: Get Quality Summary
async def example_quality_summary():
    """Get high-level quality summary."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Quality Summary")
    print("=" * 80)

    # Initialize service
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)
    service = DataQualityService(client)

    # Get summary
    summary = await service.get_quality_summary()

    print(f"\nTimestamp: {summary['timestamp']}")
    print(f"\nRecord Counts:")
    for table, count in summary['record_counts'].items():
        print(f"  {table}: {count}")

    print(f"\nQuality Score: {summary['quality_score']['overall']}/100")
    print(f"  Completeness: {summary['quality_score']['components']['completeness']}%")
    print(f"  Validity: {summary['quality_score']['components']['validity']}%")
    print(f"  Consistency: {summary['quality_score']['components']['consistency']}%")
    print(f"  Timeliness: {summary['quality_score']['components']['timeliness']}%")

    print(f"\nActive Alerts: {len(summary['alerts'])}")
    for alert in summary['alerts'][:3]:  # Show first 3
        print(f"  [{alert['severity'].upper()}] {alert['message']}")


# Example 2: Get Coverage Metrics
async def example_coverage_metrics():
    """Get data coverage metrics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Coverage Metrics")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)
    service = DataQualityService(client)

    coverage = await service.get_coverage_metrics()

    print("\nPrice Coverage by Commodity:")
    for commodity, count in coverage['prices']['by_commodity'].items():
        print(f"  {commodity.capitalize()}: {count} records")

    print("\nPrice Coverage by Source:")
    for source, count in coverage['prices']['by_source'].items():
        print(f"  {source}: {count} records")

    if 'temporal' in coverage and 'prices' in coverage['temporal']:
        temporal = coverage['temporal']['prices']
        print(f"\nTemporal Coverage:")
        print(f"  Date Range: {temporal['earliest']} to {temporal['latest']}")
        print(f"  Span: {temporal['span_days']} days")


# Example 3: Detect Outliers
async def example_detect_outliers():
    """Detect statistical outliers in price data."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Outlier Detection")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)
    service = DataQualityService(client)

    # Detect outliers with 3 standard deviations
    outliers = await service.detect_outliers(std_dev_threshold=3.0)

    print("\nPrice Statistics:")
    stats = outliers['statistics']
    print(f"  Mean: ${stats['mean']:,.2f}")
    print(f"  Std Dev: ${stats['stdev']:,.2f}")
    print(f"  Min: ${stats['min']:,.2f}")
    print(f"  Max: ${stats['max']:,.2f}")
    print(f"  Median: ${stats['median']:,.2f}")

    print(f"\nOutliers Found: {len(outliers['prices'])}")
    for outlier in outliers['prices'][:5]:  # Show first 5
        print(f"  Date: {outlier['date']}, Price: ${outlier['price']:,.2f}, "
              f"Deviation: {outlier['std_dev_count']:.2f}σ, Source: {outlier['source']}")


# Example 4: Find Temporal Gaps
async def example_temporal_gaps():
    """Find gaps in temporal data."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Temporal Gaps")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)
    service = DataQualityService(client)

    # Find gaps larger than 60 days
    gaps = await service.get_temporal_gaps(gap_threshold_days=60)

    print(f"\nPrice Data Gaps (>60 days): {len(gaps['prices'])}")
    for gap in gaps['prices'][:5]:  # Show first 5
        print(f"  Source: {gap['source']}, "
              f"Gap: {gap['from_date']} → {gap['to_date']} ({gap['gap_days']} days)")

    print(f"\nProduction Data Gaps (>1 year): {len(gaps['production'])}")
    for gap in gaps['production'][:5]:  # Show first 5
        print(f"  Province: {gap['province']}, Source: {gap['source']}, "
              f"Gap: {gap['from_year']} → {gap['to_year']} ({gap['missing_years']} years missing)")


# Example 5: Get Completeness Metrics
async def example_completeness():
    """Get field completeness percentages."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Completeness Metrics")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)
    service = DataQualityService(client)

    completeness = await service.get_completeness_metrics()

    if 'prices' in completeness:
        print("\nPrice Table Completeness:")
        for field, percentage in completeness['prices'].items():
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"  {status} {field}: {percentage}%")

    if 'production' in completeness:
        print("\nProduction Table Completeness:")
        for field, percentage in completeness['production'].items():
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"  {status} {field}: {percentage}%")


# Example 6: API Usage (via HTTP)
def example_api_usage():
    """Demonstrate API usage with curl commands."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: API Usage")
    print("=" * 80)

    print("\n# Get quality summary")
    print("curl http://localhost:8000/api/quality/summary")

    print("\n# Get coverage metrics")
    print("curl http://localhost:8000/api/quality/coverage")

    print("\n# Get completeness metrics")
    print("curl http://localhost:8000/api/quality/completeness")

    print("\n# Get temporal gaps (60 day threshold)")
    print("curl http://localhost:8000/api/quality/gaps?gap_threshold_days=60")

    print("\n# Detect outliers (3σ threshold)")
    print("curl http://localhost:8000/api/quality/outliers?std_dev_threshold=3.0")

    print("\n# Filter by commodity")
    print("curl 'http://localhost:8000/api/quality/outliers?commodity_id=822301a4-ee9d-4d13-ba98-09aebdbc32eb'")

    print("\n# Check service health")
    print("curl http://localhost:8000/api/quality/health")


# Example 7: Dashboard Integration
def example_dashboard_integration():
    """Show how dashboard uses the service."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Dashboard Integration")
    print("=" * 80)

    print("""
# In dashboard/pages/6_🔍_Data_Quality.py

import streamlit as st
from app.services.data_quality_service import DataQualityService

# Initialize service
service = DataQualityService(supabase_client)

# Get metrics
summary = await service.get_quality_summary()
coverage = await service.get_coverage_metrics()
outliers = await service.detect_outliers()

# Display
st.metric("Quality Score", summary['quality_score']['overall'])

# Plot coverage
fig = px.pie(
    values=coverage['prices']['by_commodity'].values(),
    names=coverage['prices']['by_commodity'].keys()
)
st.plotly_chart(fig)

# Show outliers table
st.dataframe(outliers['prices'])
    """)


# Example 8: Automated Monitoring
def example_automated_monitoring():
    """Show how to set up automated monitoring."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Automated Monitoring")
    print("=" * 80)

    print("""
# In app/scheduler/jobs.py

from app.scheduler.scheduler import scheduler
from app.services.data_quality_service import DataQualityService

@scheduler.scheduled_job('cron', hour=2, minute=0)  # Daily at 2 AM
async def daily_quality_check():
    '''Run daily data quality checks.'''
    service = DataQualityService(supabase_client)

    # Get summary
    summary = await service.get_quality_summary()

    # Check for critical alerts
    critical_alerts = [
        alert for alert in summary['alerts']
        if alert['severity'] == 'error'
    ]

    if critical_alerts:
        # Send email notification
        send_alert_email(
            subject=f"Data Quality Alert: {len(critical_alerts)} critical issues",
            body=format_alerts(critical_alerts)
        )

    # Log quality score
    logger.info(f"Daily quality score: {summary['quality_score']['overall']}/100")

    # Run full audit if score drops below threshold
    if summary['quality_score']['overall'] < 70:
        subprocess.run(["python", "scripts/audit_data_quality.py"])
    """)


# Example 9: Custom Quality Checks
async def example_custom_checks():
    """Create custom quality checks."""
    print("\n" + "=" * 80)
    print("EXAMPLE 9: Custom Quality Checks")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    client = create_client(supabase_url, supabase_key)

    print("\n# Custom Check: Cashew data volume")

    # Get prices for cashew
    prices = client.table("prices").select("*").execute()
    cashew_prices = [p for p in prices.data if p.get('commodity_id') == '10f49e7a-21e2-4108-9b9c-612d14a72f21']

    cashew_count = len(cashew_prices)
    threshold = 50

    if cashew_count < threshold:
        print(f"  ❌ FAIL: Only {cashew_count} cashew records (threshold: {threshold})")
        print(f"  Recommendation: Add more cashew-specific data sources")
    else:
        print(f"  ✅ PASS: {cashew_count} cashew records (threshold: {threshold})")

    print("\n# Custom Check: Recent data availability")

    from datetime import datetime, timedelta

    latest_date = max(p['date'] for p in prices.data if p.get('date'))
    days_old = (datetime.utcnow() - datetime.fromisoformat(latest_date)).days

    if days_old > 30:
        print(f"  ⚠️ WARNING: Latest data is {days_old} days old")
        print(f"  Recommendation: Run collectors to fetch recent data")
    else:
        print(f"  ✅ OK: Latest data is {days_old} days old")


# Main execution
async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("DATA QUALITY SYSTEM - USAGE EXAMPLES")
    print("=" * 80)

    # Async examples
    await example_quality_summary()
    await example_coverage_metrics()
    await example_detect_outliers()
    await example_temporal_gaps()
    await example_completeness()
    await example_custom_checks()

    # Non-async examples
    example_api_usage()
    example_dashboard_integration()
    example_automated_monitoring()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
