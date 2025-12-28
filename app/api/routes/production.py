"""Production API routes."""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional

router = APIRouter()


@router.get("/")
async def get_production(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    year: Optional[int] = Query(None, description="Filter by year"),
    province: Optional[str] = Query(None, description="Filter by province")
):
    """Get production data."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        if year:
            production = await supabase.get_production_by_year(
                commodity_obj["id"],
                year
            )
        elif province:
            production = await supabase.get_production_by_province(
                commodity_obj["id"],
                province
            )
        else:
            # Get recent production (last 5 years)
            from datetime import datetime
            current_year = datetime.now().year
            production = await supabase.get_production_by_year(
                commodity_obj["id"],
                current_year
            )

        return {
            "commodity": commodity,
            "filters": {"year": year, "province": province},
            "count": len(production),
            "data": production
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/provinces")
async def get_provinces_summary(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    year: int = Query(..., description="Year")
):
    """Get production summary by province for a given year."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        production = await supabase.get_production_by_year(
            commodity_obj["id"],
            year
        )

        # Group by province
        provinces = {}
        for record in production:
            prov = record["province"]
            if prov not in provinces:
                provinces[prov] = {
                    "province": prov,
                    "area_hectares": 0,
                    "production_tons": 0,
                    "avg_yield": 0
                }

            provinces[prov]["area_hectares"] += float(record.get("area_hectares", 0) or 0)
            provinces[prov]["production_tons"] += float(record.get("production_tons", 0) or 0)

        # Calculate averages
        for prov, data in provinces.items():
            if data["area_hectares"] > 0:
                data["avg_yield"] = data["production_tons"] / data["area_hectares"] * 1000

        return {
            "commodity": commodity,
            "year": year,
            "provinces": list(provinces.values())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geospatial")
async def get_geospatial_data(
    request: Request,
    commodity: str = Query(..., description="Commodity: 'cashew' or 'rubber'"),
    year: int = Query(..., description="Year")
):
    """Get production data with geolocation for mapping."""
    try:
        supabase = request.app.state.supabase

        commodity_obj = await supabase.get_or_create_commodity(
            name=commodity,
            category="nut" if commodity == "cashew" else "latex"
        )

        production = await supabase.get_production_by_year(
            commodity_obj["id"],
            year
        )

        # Filter records with geolocation
        geospatial = [
            {
                "province": record["province"],
                "production_tons": float(record.get("production_tons", 0) or 0),
                "geolocation": record.get("geolocation")
            }
            for record in production
            if record.get("geolocation")
        ]

        return {
            "commodity": commodity,
            "year": year,
            "count": len(geospatial),
            "data": geospatial
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
