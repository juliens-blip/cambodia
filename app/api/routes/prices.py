"""Price API routes."""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

router = APIRouter()


@router.get("/")
async def get_prices(
    request: Request,
    commodity: Optional[str] = Query(None, description="Filter by commodity: 'cashew' or 'rubber'"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get price records.

    Args:
        commodity: Optional commodity filter
        limit: Number of records to return
        offset: Pagination offset

    Returns:
        List of price records
    """
    try:
        supabase = request.app.state.supabase

        # Get commodity ID if specified
        commodity_id = None
        if commodity:
            commodity_obj = await supabase.get_or_create_commodity(
                name=commodity,
                category="nut" if commodity == "cashew" else "latex"
            )
            commodity_id = commodity_obj["id"]

        # Get prices
        if commodity_id:
            prices = await supabase.get_latest_prices(commodity_id, limit=limit)
        else:
            # Get all prices (would need a new method)
            prices = []

        return {
            "count": len(prices),
            "data": prices
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_price(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'")
):
    """Get latest price for a commodity."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        prices = await supabase.get_latest_prices(commodity_obj["id"], limit=1)

        if not prices:
            raise HTTPException(status_code=404, detail="No prices found")

        return prices[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/range")
async def get_price_range(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get prices within a date range."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        prices = await supabase.get_price_range(
            commodity_obj["id"],
            start_date,
            end_date
        )

        return {
            "commodity": commodity,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "count": len(prices),
            "data": prices
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_price_trends(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    days: int = Query(30, ge=1, le=365, description="Number of days")
):
    """Get price trends over specified number of days."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        # Calculate date range
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)

        prices = await supabase.get_price_range(
            commodity_obj["id"],
            start_date,
            end_date
        )

        # Calculate trend
        if len(prices) >= 2:
            first_price = prices[-1]["price_usd_per_unit"]
            last_price = prices[0]["price_usd_per_unit"]
            change_pct = ((float(last_price) - float(first_price)) / float(first_price)) * 100
        else:
            change_pct = 0.0

        return {
            "commodity": commodity,
            "period_days": days,
            "count": len(prices),
            "change_percent": round(change_pct, 2),
            "data": prices
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
