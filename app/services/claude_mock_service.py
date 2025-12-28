"""Claude MOCK service for template-based report generation."""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class ClaudeMockService:
    """
    Mock Claude service for report generation using templates.

    Uses templates instead of real Claude API to save costs.
    Can be upgraded to real Claude API later if budget allows.
    """

    def __init__(self, mock_mode: bool = True):
        """
        Initialize Claude Mock service.

        Args:
            mock_mode: If True, use templates. If False, would use real API.
        """
        self.mock_mode = mock_mode

    async def generate_daily_report(
        self,
        commodity: str,
        price_data: Optional[Dict[str, Any]] = None,
        perplexity_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate daily market report.

        Args:
            commodity: 'cashew' or 'rubber'
            price_data: Latest price data from collectors
            perplexity_analysis: Perplexity research results

        Returns:
            Dict with report content and metadata
        """
        today = date.today()

        # Extract data
        latest_price = price_data.get("price_usd", 0) if price_data else 0
        yesterday_price = price_data.get("previous_price_usd", 0) if price_data else 0
        volume = price_data.get("volume_tons", 0) if price_data else 0
        destination = price_data.get("destination_country", "Unknown") if price_data else "Unknown"

        # Calculate change
        if yesterday_price > 0:
            change = ((latest_price - yesterday_price) / yesterday_price) * 100
            change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        else:
            change_str = "N/A"

        # Extract Perplexity summary
        perplexity_summary = ""
        if perplexity_analysis:
            response = perplexity_analysis.get("response_text", "")
            # Take first 500 chars as summary
            perplexity_summary = response[:500] + "..." if len(response) > 500 else response

        # Generate insights (template-based)
        insights = self._generate_insights(commodity, latest_price, change, perplexity_summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(commodity, change, perplexity_summary)

        # Build report content
        content = f"""# {commodity.title()} Daily Report - {today.strftime('%Y-%m-%d')}

## Executive Summary
- **Current Price**: ${latest_price:.2f}/ton ({change_str} vs yesterday)
- **Volume Traded**: {volume} tons
- **Top Destination**: {destination}

## Market Conditions
{perplexity_summary}

## Key Insights
{chr(10).join(f'- {insight}' for insight in insights)}

## Recommendations
{chr(10).join(f'- {rec}' for rec in recommendations)}

---
*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Cambodia Time*
*Report Type: Daily Market Analysis (MOCK)*
"""

        report = {
            "commodity": commodity,
            "report_type": "daily",
            "title": f"{commodity.title()} Daily Report - {today.isoformat()}",
            "content": content,
            "insights": insights,
            "recommendations": recommendations,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "mock_mode": self.mock_mode,
                "price_usd": latest_price,
                "price_change_pct": change if yesterday_price > 0 else None,
                "volume_tons": volume,
                "destination": destination
            }
        }

        logger.info(f"Generated daily report for {commodity} (MOCK)")
        return report

    async def generate_weekly_report(
        self,
        commodity: str,
        week_data: Optional[Dict[str, Any]] = None,
        perplexity_deep_dive: Optional[Dict[str, Any]] = None,
        geopolitical_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate weekly comprehensive report.

        Args:
            commodity: 'cashew' or 'rubber'
            week_data: Aggregated data for the week
            perplexity_deep_dive: Deep research from Perplexity
            geopolitical_analysis: Geopolitical events analysis from Perplexity

        Returns:
            Dict with report content and metadata
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Extract week data
        avg_price = week_data.get("avg_price_usd", 0) if week_data else 0
        total_volume = week_data.get("total_volume_tons", 0) if week_data else 0
        price_trend = week_data.get("trend", "stable") if week_data else "stable"

        # Extract deep dive analysis
        deep_analysis = ""
        if perplexity_deep_dive:
            deep_analysis = perplexity_deep_dive.get("response_text", "")

        # Extract geopolitical analysis
        geo_analysis = ""
        geo_citations = []
        if geopolitical_analysis:
            geo_analysis = geopolitical_analysis.get("response_text", "")
            geo_citations = geopolitical_analysis.get("citations", [])

        # Build weekly content
        content = f"""# {commodity.title()} Weekly Deep Dive - Week {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}

## Week Overview
- **Average Price**: ${avg_price:.2f}/ton
- **Total Volume**: {total_volume} tons
- **Price Trend**: {price_trend.title()}

## Comprehensive Market Analysis
{deep_analysis[:1500]}

## Geopolitical Factors & Global Impact
{geo_analysis[:1500] if geo_analysis else "No significant geopolitical events impacting market this week."}

### Key Events Affecting {commodity.title()} Trade:
- **China Demand**: Major buyer of Cambodian {commodity} - monitor manufacturing output
- **Regional Competition**: Vietnam, Thailand production levels impact global pricing
- **Trade Policies**: Export/import restrictions, tariffs, sanctions
- **Global Harvest**: Production forecasts from competing countries

## Market Outlook (Next 30 Days)
Based on current trends and geopolitical factors, we anticipate:
- Price stability with potential {price_trend} momentum
- Continued demand from major markets (especially China for processed products)
- Monitor regional competition dynamics and global harvest forecasts

## Strategic Recommendations
- Optimize export timing based on price trends
- Diversify destination markets to reduce risk
- Monitor quality standards for premium pricing

---
*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Cambodia Time*
*Report Type: Weekly Comprehensive Analysis (MOCK)*
"""

        report = {
            "commodity": commodity,
            "report_type": "weekly",
            "title": f"{commodity.title()} Weekly Deep Dive - {week_start.isoformat()}",
            "content": content,
            "insights": [],
            "recommendations": [],
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "mock_mode": self.mock_mode,
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "avg_price_usd": avg_price,
                "total_volume_tons": total_volume,
                "trend": price_trend,
                "geopolitical_citations": geo_citations,
                "has_geopolitical_analysis": bool(geo_analysis)
            }
        }

        logger.info(f"Generated weekly report for {commodity} (MOCK)")
        return report

    def _generate_insights(
        self,
        commodity: str,
        price: float,
        change: Any,
        perplexity_summary: str
    ) -> List[str]:
        """Generate template-based insights."""
        insights = []

        # Price-based insights
        if isinstance(change, (int, float)):
            if change > 5:
                insights.append(f"Significant price increase of {change:.2f}% indicates strong demand")
            elif change < -5:
                insights.append(f"Price decline of {change:.2f}% may signal oversupply or reduced demand")
            else:
                insights.append("Price remains stable with minimal fluctuation")

        # Commodity-specific insights
        if commodity == "cashew":
            insights.append("Vietnam processing capacity continues to influence regional pricing")
        elif commodity == "rubber":
            insights.append("Global automotive demand impacts natural rubber prices")

        # Generic insights
        insights.append("Monitor seasonal patterns for optimal export timing")

        return insights

    def _generate_recommendations(
        self,
        commodity: str,
        change: Any,
        perplexity_summary: str
    ) -> List[str]:
        """Generate template-based recommendations."""
        recommendations = []

        # Price-based recommendations
        if isinstance(change, (int, float)):
            if change > 5:
                recommendations.append("Consider accelerating exports to capitalize on high prices")
            elif change < -5:
                recommendations.append("Hold inventory if possible; wait for price recovery")
            else:
                recommendations.append("Maintain regular export schedule")

        # Quality recommendations
        recommendations.append("Focus on premium quality grades for better margins")

        # Market diversification
        recommendations.append("Explore emerging markets to reduce dependency on traditional buyers")

        return recommendations
