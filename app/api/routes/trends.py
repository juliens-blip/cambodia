"""API routes for market trends analysis."""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from datetime import date
import logging

from app.services.supabase_service import SupabaseService
from app.services.perplexity_service import PerplexityService
from app.services.market_trends_service import MarketTrendsService
from app.services.public_prices_service import PublicPricesService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trends", tags=["Market Trends"])

# Initialize services (singleton)
_supabase = None
_perplexity = None
_trends = None
_public_prices = None


def get_services():
    """Get or initialize services."""
    global _supabase, _perplexity, _trends, _public_prices

    if _supabase is None:
        _supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    if _perplexity is None:
        _perplexity = PerplexityService(
            api_key=settings.perplexity_api_key,
            max_requests_per_month=1000
        )
    if _trends is None:
        _trends = MarketTrendsService(_supabase, _perplexity)
    if _public_prices is None:
        _public_prices = PublicPricesService()

    return _supabase, _perplexity, _trends, _public_prices


@router.get("/latest/{commodity}")
async def get_latest_trend(commodity: str):
    """
    Get the latest market trend analysis for a commodity.

    - **commodity**: 'cashew' or 'rubber'

    Returns the most recent trend analysis including:
    - Twitter/X sentiment (last 48h)
    - Stock market data
    - Overall trend direction
    - AI-generated insights
    """
    try:
        _, _, trends, _ = get_services()

        result = await trends.get_latest_trend(commodity)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No trend data found for {commodity}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{commodity}")
async def get_trend_history(
    commodity: str,
    days: int = Query(default=30, ge=1, le=90)
):
    """
    Get trend history for a commodity.

    - **commodity**: 'cashew' or 'rubber'
    - **days**: Number of days to look back (1-90)

    Returns historical trend data for charting and analysis.
    """
    try:
        _, _, trends, _ = get_services()

        history = await trends.get_trend_history(commodity, days)

        return {
            "commodity": commodity,
            "days": days,
            "count": len(history),
            "data": history
        }

    except Exception as e:
        logger.error(f"Error getting trend history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{commodity}")
async def analyze_trends(
    commodity: str,
    force_refresh: bool = Query(default=False)
):
    """
    Trigger new trend analysis for a commodity.

    - **commodity**: 'cashew' or 'rubber'
    - **force_refresh**: Force new analysis even if today's exists

    This endpoint:
    1. Searches Twitter/X for recent tweets (48h)
    2. Fetches stock market data
    3. Generates AI analysis via Perplexity
    4. Stores results in database

    Cost: ~$0.005 per analysis (Perplexity API)

    Note: Automatically runs daily via scheduled script.
    Use this endpoint for manual/on-demand analysis only.
    """
    try:
        _, _, trends, _ = get_services()

        result = await trends.analyze_and_store_trends(
            commodity=commodity,
            force_refresh=force_refresh
        )

        return result

    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_trend_alerts():
    """
    Get unread market alerts.

    Returns alerts triggered by:
    - Significant price movements (>5%)
    - Sentiment shifts to bearish
    - High volatility events

    Alerts are auto-generated when new trends are stored.
    """
    try:
        _, _, trends, _ = get_services()

        alerts = await trends.get_unread_alerts()

        return {
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """
    Mark an alert as read.

    - **alert_id**: UUID of the alert
    """
    try:
        _, _, trends, _ = get_services()

        success = await trends.mark_alert_read(alert_id)

        if success:
            return {"status": "success", "message": "Alert marked as read"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update alert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_trends_summary():
    """
    Get summary of all commodities' latest trends.

    Returns:
    - Latest trend for each commodity
    - Overall market sentiment
    - Active alerts count
    """
    try:
        _, _, trends, _ = get_services()

        commodities = ['cashew', 'rubber']
        summary = {}

        for commodity in commodities:
            latest = await trends.get_latest_trend(commodity)
            if latest:
                summary[commodity] = {
                    'trend_date': latest.get('trend_date'),
                    'overall_trend': latest.get('overall_trend'),
                    'twitter_sentiment': latest.get('twitter_sentiment'),
                    'confidence_score': latest.get('confidence_score'),
                    'stock_change_pct': latest.get('stock_change_pct')
                }

        # Get alerts
        alerts = await trends.get_unread_alerts()

        return {
            'commodities': summary,
            'alerts_count': len(alerts),
            'last_updated': max([v.get('trend_date', '') for v in summary.values()] or [''])
        }

    except Exception as e:
        logger.error(f"Error getting trends summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/prices/{commodity}")
async def get_public_prices(
    commodity: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get public commodity price data (historical).

    - **commodity**: 'cashew' or 'rubber'
    - **days**: Number of days of history (1-365)

    Returns public market price data including:
    - Historical prices (USD/ton)
    - Price statistics (current, average, high, low)
    - Percentage change over period

    **Note:** This data is from public market sources and
    supplements the AI-analyzed trends data.
    """
    try:
        _, _, _, public_prices = get_services()

        history = public_prices.get_price_history(commodity, days)
        stats = public_prices.get_price_statistics(commodity, days)

        return {
            "commodity": commodity,
            "days": days,
            "count": len(history),
            "data": history,
            "statistics": stats,
            "source": "Public Market Data (Historical)"
        }

    except Exception as e:
        logger.error(f"Error getting public prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario/{commodity}")
async def generate_scenario_analysis(
    commodity: str,
    scenario_type: str = Query(default="realistic", regex="^(pessimistic|realistic|optimistic)$"),
    price_data: Optional[dict] = Body(default=None),
    twitter_data: Optional[dict] = Body(default=None),
    docs_context: Optional[str] = Body(default=None),
    macro_context: Optional[str] = Body(default=None)
):
    """
    Generate AI scenario analysis for a commodity.
    
    - **commodity**: 'cashew' or 'rubber'
    - **scenario_type**: 'pessimistic', 'realistic', or 'optimistic'
    - **price_data**: Optional current price data (from /public/prices)
    - **twitter_data**: Optional Twitter sentiment data (from /latest)
    - **docs_context**: Optional semantic search context (GDrive docs)
    - **macro_context**: Optional macro indicators context (MEF/NBC/CSX)
    
    Uses Perplexity AI to generate market scenario analysis.
    Cost: ~$0.005 per analysis.
    """
    try:
        _, perplexity, _, public_prices = get_services()
        
        # Get price data if not provided
        if not price_data:
            try:
                history = public_prices.get_price_history(commodity, 30)
                stats = public_prices.get_price_statistics(commodity, 30)
                price_data = {"statistics": stats, "data": history}
            except Exception:
                price_data = {"statistics": {"current": 0, "change_pct": 0}}
        
        # Extract key metrics
        current_price = price_data.get("statistics", {}).get("current", 0)
        price_change = price_data.get("statistics", {}).get("change_pct", 0)
        
        # Get Twitter sentiment if available
        twitter_sentiment = "neutral"
        overall_trend = "neutral"
        if twitter_data:
            twitter_sentiment = twitter_data.get("twitter_sentiment", "neutral")
            overall_trend = twitter_data.get("overall_trend", "neutral")

        docs_used = bool(docs_context and docs_context.strip())
        docs_count = docs_context.count("[Source ") if docs_used else 0
        docs_block = ""
        if docs_used:
            docs_block = (
                "LOCAL DOCUMENTS (Google Drive):\n"
                f"{docs_context}\n\n"
                "---\n\n"
                "Use the local documents as primary sources and cite them explicitly.\n\n"
            )

        macro_used = bool(macro_context and macro_context.strip())
        macro_block = ""
        if macro_used:
            macro_block = (
                "MACRO INDICATORS (MEF/NBC/CSX):\n"
                f"{macro_context}\n\n"
                "---\n\n"
                "Use macro indicators as supporting context for the analysis.\n\n"
            )

        # Build Cambodia-specific context for cashew (Phase 1.3)
        cambodia_block = ""
        if commodity == 'cashew':
            cambodia_block = """
=== CAMBODIA MARKET POSITION (CASHEW) ===

**Global Ranking:**
- 2nd largest RCN producer worldwide (~850,000 tonnes/year)
- Share of global production: ~15-18%
- Main competitor: Ivory Coast (1st), India (3rd)

**Export Structure:**
- Total exports: ~815,000 tonnes RCN (2024)
- Destination breakdown:
  * Vietnam: 90% (processing, then re-export as kernels)
  * China: 5% (direct consumption/processing)
  * Others: 5%
- Export value: $1.15-1.5 billion USD

**Producer Profile:**
- ~500,000 farming families
- Main provinces: Kampong Thom, Kratie, Mondulkiri
- Farmgate price sensitivity: High (livelihood dependent)

**Market Vulnerabilities:**
- Price-taker position: Vietnamese processors dictate RCN prices
- No bargaining power: Limited domestic processing alternatives
- FX exposure: USD/KHR fluctuations affect farmer revenues

**Price Reference Guide:**
- RCN FOB Cambodia: $1,500-2,500/ton (unprocessed)
- Kernels FOB Vietnam: $6,000-7,000/ton (W320 grade)
- Farmgate Cambodia: 3,000-5,000 KHR/kg

===

**CRITICAL FOR ALL SCENARIOS:** You MUST explicitly discuss:
1. Impact on Cambodian farmer revenues (farmgate prices in KHR)
2. Export earnings implications (RCN volumes x prices)
3. Dependency on Vietnamese demand/processing
4. Opportunities for domestic value addition

"""

        # Build prompt based on scenario type with Cambodia context
        scenario_prompts = {
            'pessimistic': f"""As a conservative market analyst, provide a PESSIMISTIC (bearish) analysis for {commodity} market.

{docs_block}{macro_block}{cambodia_block}Current market data:
- Current price: ${current_price}/ton
- Price change (30 days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Focus on:
1. **Price Outlook**: Downside risks for BOTH RCN (Cambodia export) and Kernels (Vietnam)
2. **Risk Factors for Cambodia**:
   - Vietnamese processor margin squeeze = lower RCN prices
   - Reduced Vietnamese demand = unsold RCN inventory
   - Currency risk: KHR depreciation hurting farmer purchasing power
   - Supply gluts from competing African producers
3. **Bearish Scenarios for Cambodia**: What could hurt Cambodian farmers in 3-6 months
4. **Farmer Impact**: Expected farmgate price range in KHR/kg under this scenario

Be realistic but cautious. Distinguish RCN vs Kernel prices. Keep response under 350 words.""",

            'realistic': f"""As a balanced market analyst, provide a REALISTIC (neutral) analysis for {commodity} market.

{docs_block}{macro_block}{cambodia_block}Current market data:
- Current price: ${current_price}/ton
- Price change (30 days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Focus on:
1. **Price Outlook**: Most likely trajectory for BOTH RCN and Kernels
2. **Balanced View for Cambodia**:
   - Upside: Growing Vietnamese processing capacity, stable Chinese demand
   - Downside: Competition from Ivory Coast/Nigeria, processor margin pressure
   - Neutral: Status quo continuation with seasonal variations
3. **Probable Scenarios**: What's most likely for Cambodian exports in 3-6 months
4. **Farmer Outlook**: Expected farmgate price range in KHR/kg (realistic estimate)

Be objective and data-driven. Distinguish RCN ($1,500-2,500) vs Kernel ($6,000-7,000) prices. Keep response under 350 words.""",

            'optimistic': f"""As an opportunity-focused market analyst, provide an OPTIMISTIC (bullish) analysis for {commodity} market.

{docs_block}{macro_block}{cambodia_block}Current market data:
- Current price: ${current_price}/ton
- Price change (30 days): {price_change:+.2f}%
- Twitter sentiment: {twitter_sentiment}
- Overall trend: {overall_trend}

Focus on:
1. **Price Outlook**: Upside potential for BOTH RCN and Kernels
2. **Opportunities for Cambodia**:
   - Domestic processing expansion = higher value retention
   - Bio/organic certification = premium pricing opportunities
   - Supply constraints in Africa = increased demand for Cambodian RCN
   - Vietnamese export growth to US/EU = higher RCN prices
3. **Bullish Scenarios for Cambodia**: What could benefit Cambodian farmers in 3-6 months
4. **Farmer Upside**: Best-case farmgate price range in KHR/kg under this scenario

Be realistic but optimistic. Distinguish RCN vs Kernel prices. Keep response under 350 words."""
        }
        
        prompt = scenario_prompts.get(scenario_type, scenario_prompts['realistic'])
        
        # Call Perplexity directly using internal _query method
        result = await perplexity._query(prompt, commodity, f"scenario_{scenario_type}")
        
        return {
            "commodity": commodity,
            "scenario_type": scenario_type,
            "analysis": result.get("response_text", "Analysis not available"),
            "citations": result.get("citations", []),
            "price_context": {
                "current_price": current_price,
                "price_change_pct": price_change
            },
            "docs_used": docs_used,
            "docs_count": docs_count,
            "macro_used": macro_used
        }
        
    except Exception as e:
        logger.error(f"Error generating scenario analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
