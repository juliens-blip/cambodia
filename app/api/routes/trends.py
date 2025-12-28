"""API routes for market trends analysis."""
from fastapi import APIRouter, HTTPException, Query
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
