"""
Data Quality API Routes

Provides REST API endpoints for accessing data quality metrics.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.services.data_quality_service import DataQualityService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["Data Quality"])

# Initialize service (will be properly injected in production)
try:
    from supabase import create_client
    supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    quality_service = DataQualityService(supabase_client)
except Exception as e:
    logger.error(f"Failed to initialize quality service: {e}")
    quality_service = None


@router.get("/summary")
async def get_quality_summary():
    """
    Get high-level data quality summary.

    Returns:
        - timestamp: When metrics were calculated
        - record_counts: Count of records per table
        - quality_score: Overall quality score (0-100)
        - alerts: Active quality alerts

    Example:
        GET /api/quality/summary
    """
    if not quality_service:
        raise HTTPException(status_code=503, detail="Quality service unavailable")

    try:
        summary = await quality_service.get_quality_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting quality summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage")
async def get_coverage_metrics():
    """
    Get data coverage metrics.

    Returns coverage by:
        - Commodity (cashew vs rubber)
        - Source (MEF, WITS, ODC, GDrive)
        - Geography (provinces)
        - Time (date ranges)

    Example:
        GET /api/quality/coverage
    """
    if not quality_service:
        raise HTTPException(status_code=503, detail="Quality service unavailable")

    try:
        coverage = await quality_service.get_coverage_metrics()
        return coverage
    except Exception as e:
        logger.error(f"Error getting coverage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/completeness")
async def get_completeness_metrics():
    """
    Get data completeness metrics.

    Returns percentage of non-null values for each field in:
        - prices table
        - production table

    Example:
        GET /api/quality/completeness
    """
    if not quality_service:
        raise HTTPException(status_code=503, detail="Quality service unavailable")

    try:
        completeness = await quality_service.get_completeness_metrics()
        return completeness
    except Exception as e:
        logger.error(f"Error getting completeness metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps")
async def get_temporal_gaps(
    commodity_id: Optional[str] = Query(None, description="Filter by commodity ID"),
    gap_threshold_days: int = Query(60, description="Minimum gap size in days", ge=1, le=365)
):
    """
    Identify temporal gaps in data.

    Args:
        commodity_id: Optional filter by specific commodity
        gap_threshold_days: Minimum gap size to report (default: 60 days)

    Returns:
        - prices: List of date gaps in price data
        - production: List of year gaps in production data

    Example:
        GET /api/quality/gaps
        GET /api/quality/gaps?commodity_id=822301a4-ee9d-4d13-ba98-09aebdbc32eb
        GET /api/quality/gaps?gap_threshold_days=90
    """
    if not quality_service:
        raise HTTPException(status_code=503, detail="Quality service unavailable")

    try:
        gaps = await quality_service.get_temporal_gaps(
            commodity_id=commodity_id,
            gap_threshold_days=gap_threshold_days
        )
        return gaps
    except Exception as e:
        logger.error(f"Error getting temporal gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outliers")
async def get_outliers(
    commodity_id: Optional[str] = Query(None, description="Filter by commodity ID"),
    std_dev_threshold: float = Query(3.0, description="Standard deviation threshold", ge=1.0, le=5.0)
):
    """
    Detect statistical outliers in price data.

    Uses standard deviation method to identify prices that are
    significantly different from the mean.

    Args:
        commodity_id: Optional filter by specific commodity
        std_dev_threshold: Number of standard deviations (default: 3.0)

    Returns:
        - prices: List of outlier records
        - statistics: Mean, stdev, min, max, median

    Example:
        GET /api/quality/outliers
        GET /api/quality/outliers?commodity_id=822301a4-ee9d-4d13-ba98-09aebdbc32eb
        GET /api/quality/outliers?std_dev_threshold=2.5
    """
    if not quality_service:
        raise HTTPException(status_code=503, detail="Quality service unavailable")

    try:
        outliers = await quality_service.detect_outliers(
            commodity_id=commodity_id,
            std_dev_threshold=std_dev_threshold
        )
        return outliers
    except Exception as e:
        logger.error(f"Error detecting outliers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def quality_health():
    """
    Health check for quality service.

    Returns:
        - status: "healthy" or "degraded"
        - service_available: boolean
        - version: API version

    Example:
        GET /api/quality/health
    """
    return {
        "status": "healthy" if quality_service else "degraded",
        "service_available": quality_service is not None,
        "version": "1.0.0"
    }
