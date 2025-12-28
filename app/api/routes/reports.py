"""Reports API routes."""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional

router = APIRouter()


@router.get("/")
async def get_reports(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    report_type: Optional[str] = Query(None, description="Report type: 'daily', 'weekly', 'crisis'"),
    limit: int = Query(10, ge=1, le=100)
):
    """Get reports for a commodity."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        reports = await supabase.get_reports(
            commodity_obj["id"],
            report_type=report_type,
            limit=limit
        )

        return {
            "commodity": commodity,
            "report_type": report_type or "all",
            "count": len(reports),
            "data": reports
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_report(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    report_type: str = Query("daily", description="Report type: 'daily' or 'weekly'")
):
    """Get the latest report for a commodity."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        reports = await supabase.get_reports(
            commodity_obj["id"],
            report_type=report_type,
            limit=1
        )

        if not reports:
            raise HTTPException(status_code=404, detail="No reports found")

        return reports[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses")
async def get_perplexity_analyses(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    query_type: Optional[str] = Query(None, description="Query type: 'price', 'geopolitics', 'market'"),
    limit: int = Query(10, ge=1, le=100)
):
    """Get Perplexity analyses for a commodity."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        analyses = await supabase.get_recent_analyses(
            commodity_obj["id"],
            query_type=query_type,
            limit=limit
        )

        return {
            "commodity": commodity,
            "query_type": query_type or "all",
            "count": len(analyses),
            "data": analyses
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geopolitical-events")
async def get_geopolitical_events(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    impact_level: Optional[str] = Query(None, description="Impact level: 'low', 'medium', 'high', 'critical'")
):
    """Get recent geopolitical events affecting commodity markets."""
    try:
        supabase = request.app.state.supabase

        events = await supabase.get_recent_events(
            limit=limit,
            impact_level=impact_level
        )

        return {
            "count": len(events),
            "impact_level": impact_level or "all",
            "data": events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
