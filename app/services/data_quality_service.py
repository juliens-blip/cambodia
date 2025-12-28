"""
Data Quality Service

Provides reusable data quality metrics and monitoring functions
for use in API endpoints and dashboard pages.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from supabase import Client

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Service for calculating and monitoring data quality metrics.

    Used by:
    - API endpoints (/api/data-quality)
    - Dashboard pages (Data Quality page)
    - Automated monitoring jobs
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize service with Supabase client.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client

    async def get_quality_summary(self) -> Dict[str, Any]:
        """
        Get high-level data quality summary.

        Returns:
            Dictionary with quality metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "record_counts": await self._get_record_counts(),
            "quality_score": await self._calculate_quality_score(),
            "alerts": await self._get_quality_alerts()
        }

    async def get_coverage_metrics(self) -> Dict[str, Any]:
        """
        Get data coverage metrics.

        Returns:
            Coverage metrics by commodity, source, geography, time
        """
        metrics = {}

        try:
            # Get commodity mapping
            commodities = self.client.table("commodities").select("*").execute()
            commodity_map = {c["id"]: c["name"] for c in commodities.data}

            # Price coverage
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data

            price_by_commodity = defaultdict(int)
            price_by_source = defaultdict(int)

            for p in price_data:
                commodity_name = commodity_map.get(p["commodity_id"], "unknown")
                price_by_commodity[commodity_name] += 1
                price_by_source[p["source"]] += 1

            metrics["prices"] = {
                "by_commodity": dict(price_by_commodity),
                "by_source": dict(price_by_source),
                "total": len(price_data)
            }

            # Production coverage
            production = self.client.table("production").select("*").execute()
            prod_data = production.data

            prod_by_commodity = defaultdict(int)
            prod_by_province = defaultdict(int)

            for p in prod_data:
                commodity_name = commodity_map.get(p["commodity_id"], "unknown")
                prod_by_commodity[commodity_name] += 1
                prod_by_province[p.get("province", "unknown")] += 1

            metrics["production"] = {
                "by_commodity": dict(prod_by_commodity),
                "by_province": dict(prod_by_province),
                "total": len(prod_data)
            }

            # Temporal coverage
            if price_data:
                dates = [p["date"] for p in price_data if p.get("date")]
                metrics["temporal"] = {
                    "prices": {
                        "earliest": min(dates) if dates else None,
                        "latest": max(dates) if dates else None,
                        "span_days": (datetime.fromisoformat(max(dates)) - datetime.fromisoformat(min(dates))).days if dates else 0
                    }
                }

            if prod_data:
                years = [p["year"] for p in prod_data if p.get("year")]
                if "temporal" not in metrics:
                    metrics["temporal"] = {}
                metrics["temporal"]["production"] = {
                    "earliest": min(years) if years else None,
                    "latest": max(years) if years else None,
                    "span_years": max(years) - min(years) + 1 if years else 0
                }

        except Exception as e:
            logger.error(f"Error calculating coverage metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    async def get_completeness_metrics(self) -> Dict[str, Any]:
        """
        Get data completeness metrics (% non-null for each field).

        Returns:
            Completeness percentages by field
        """
        metrics = {}

        try:
            # Price completeness
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data
            total_prices = len(price_data)

            if total_prices > 0:
                metrics["prices"] = {
                    "commodity_id": round(sum(1 for p in price_data if p.get("commodity_id")) / total_prices * 100, 2),
                    "date": round(sum(1 for p in price_data if p.get("date")) / total_prices * 100, 2),
                    "price_usd_per_unit": round(sum(1 for p in price_data if p.get("price_usd_per_unit") is not None) / total_prices * 100, 2),
                    "volume_tons": round(sum(1 for p in price_data if p.get("volume_tons") is not None) / total_prices * 100, 2),
                    "source": round(sum(1 for p in price_data if p.get("source")) / total_prices * 100, 2),
                    "destination_country": round(sum(1 for p in price_data if p.get("destination_country")) / total_prices * 100, 2),
                    "quality_grade": round(sum(1 for p in price_data if p.get("quality_grade")) / total_prices * 100, 2)
                }

            # Production completeness
            production = self.client.table("production").select("*").execute()
            prod_data = production.data
            total_prod = len(prod_data)

            if total_prod > 0:
                metrics["production"] = {
                    "commodity_id": round(sum(1 for p in prod_data if p.get("commodity_id")) / total_prod * 100, 2),
                    "year": round(sum(1 for p in prod_data if p.get("year")) / total_prod * 100, 2),
                    "province": round(sum(1 for p in prod_data if p.get("province")) / total_prod * 100, 2),
                    "area_hectares": round(sum(1 for p in prod_data if p.get("area_hectares") is not None) / total_prod * 100, 2),
                    "production_tons": round(sum(1 for p in prod_data if p.get("production_tons") is not None) / total_prod * 100, 2),
                    "yield_kg_per_ha": round(sum(1 for p in prod_data if p.get("yield_kg_per_ha") is not None) / total_prod * 100, 2),
                    "geolocation": round(sum(1 for p in prod_data if p.get("geolocation")) / total_prod * 100, 2),
                    "source": round(sum(1 for p in prod_data if p.get("source")) / total_prod * 100, 2)
                }

        except Exception as e:
            logger.error(f"Error calculating completeness metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    async def get_temporal_gaps(
        self,
        commodity_id: Optional[str] = None,
        gap_threshold_days: int = 60
    ) -> Dict[str, Any]:
        """
        Identify temporal gaps in data.

        Args:
            commodity_id: Optional filter by commodity
            gap_threshold_days: Minimum gap size to report (default 60 days)

        Returns:
            Dictionary with gap information
        """
        gaps = {"prices": [], "production": []}

        try:
            # Price gaps
            query = self.client.table("prices").select("*").order("date")
            if commodity_id:
                query = query.eq("commodity_id", commodity_id)

            prices = query.execute()
            price_data = prices.data

            # Group by commodity and source
            by_commodity_source = defaultdict(list)
            for p in price_data:
                key = (p.get("commodity_id"), p.get("source"))
                by_commodity_source[key].append(p["date"])

            for (cid, source), dates in by_commodity_source.items():
                if len(dates) < 2:
                    continue

                dates_sorted = sorted(dates)
                for i in range(len(dates_sorted) - 1):
                    current = datetime.fromisoformat(dates_sorted[i])
                    next_date = datetime.fromisoformat(dates_sorted[i + 1])
                    gap_days = (next_date - current).days

                    if gap_days > gap_threshold_days:
                        gaps["prices"].append({
                            "commodity_id": cid,
                            "source": source,
                            "from_date": dates_sorted[i],
                            "to_date": dates_sorted[i + 1],
                            "gap_days": gap_days
                        })

            # Production gaps
            query = self.client.table("production").select("*").order("year")
            if commodity_id:
                query = query.eq("commodity_id", commodity_id)

            production = query.execute()
            prod_data = production.data

            by_commodity_province = defaultdict(list)
            for p in prod_data:
                key = (p.get("commodity_id"), p.get("province"), p.get("source"))
                by_commodity_province[key].append(p["year"])

            for (cid, province, source), years in by_commodity_province.items():
                if len(years) < 2:
                    continue

                years_sorted = sorted(years)
                for i in range(len(years_sorted) - 1):
                    gap = years_sorted[i + 1] - years_sorted[i]
                    if gap > 1:  # Missing years
                        gaps["production"].append({
                            "commodity_id": cid,
                            "province": province,
                            "source": source,
                            "from_year": years_sorted[i],
                            "to_year": years_sorted[i + 1],
                            "missing_years": gap - 1
                        })

        except Exception as e:
            logger.error(f"Error calculating temporal gaps: {e}")
            gaps["error"] = str(e)

        return gaps

    async def detect_outliers(
        self,
        commodity_id: Optional[str] = None,
        std_dev_threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect statistical outliers in price data.

        Args:
            commodity_id: Optional filter by commodity
            std_dev_threshold: Number of standard deviations for outlier threshold

        Returns:
            Dictionary with outlier information
        """
        outliers = {"prices": [], "statistics": {}}

        try:
            query = self.client.table("prices").select("*")
            if commodity_id:
                query = query.eq("commodity_id", commodity_id)

            prices = query.execute()
            price_data = prices.data

            # Get valid prices
            valid_prices = [
                p for p in price_data
                if p.get("price_usd_per_unit") is not None and p["price_usd_per_unit"] > 0
            ]

            if len(valid_prices) < 2:
                return outliers

            import statistics

            price_values = [p["price_usd_per_unit"] for p in valid_prices]
            mean = statistics.mean(price_values)
            stdev = statistics.stdev(price_values) if len(price_values) > 1 else 0

            outliers["statistics"] = {
                "mean": round(mean, 2),
                "stdev": round(stdev, 2),
                "min": round(min(price_values), 2),
                "max": round(max(price_values), 2),
                "median": round(statistics.median(price_values), 2)
            }

            # Detect outliers
            for p in valid_prices:
                price = p["price_usd_per_unit"]
                if abs(price - mean) > std_dev_threshold * stdev:
                    outliers["prices"].append({
                        "id": p["id"],
                        "commodity_id": p["commodity_id"],
                        "date": p["date"],
                        "price": price,
                        "source": p["source"],
                        "deviation_from_mean": round(abs(price - mean), 2),
                        "std_dev_count": round(abs(price - mean) / stdev, 2) if stdev > 0 else 0
                    })

        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            outliers["error"] = str(e)

        return outliers

    async def _get_record_counts(self) -> Dict[str, int]:
        """Get record counts for all tables."""
        counts = {}
        tables = ["commodities", "prices", "production", "perplexity_analyses",
                  "claude_reports", "data_sources"]

        for table in tables:
            try:
                result = self.client.table(table).select("id", count="exact").execute()
                counts[table] = result.count
            except Exception as e:
                logger.error(f"Error counting {table}: {e}")
                counts[table] = 0

        return counts

    async def _calculate_quality_score(self) -> Dict[str, Any]:
        """
        Calculate overall data quality score (0-100).

        Score components:
        - Completeness (40%): % of non-null fields
        - Validity (30%): % of valid values (no negatives, outliers)
        - Consistency (20%): Inter-source agreement
        - Timeliness (10%): Recency of data
        """
        score = {
            "overall": 0,
            "components": {}
        }

        try:
            # Completeness score
            completeness = await self.get_completeness_metrics()
            if "prices" in completeness:
                price_completeness = list(completeness["prices"].values())
                avg_completeness = sum(price_completeness) / len(price_completeness)
                score["components"]["completeness"] = round(avg_completeness, 2)
            else:
                score["components"]["completeness"] = 0

            # Validity score (based on outliers and invalid values)
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data

            if price_data:
                negative_count = sum(1 for p in price_data if p.get("price_usd_per_unit") and p["price_usd_per_unit"] < 0)
                zero_count = sum(1 for p in price_data if p.get("price_usd_per_unit") == 0)
                invalid_count = negative_count + zero_count

                validity_pct = (1 - invalid_count / len(price_data)) * 100 if len(price_data) > 0 else 100
                score["components"]["validity"] = round(validity_pct, 2)
            else:
                score["components"]["validity"] = 100

            # Timeliness score (based on most recent data)
            if price_data:
                latest_date = max(p["date"] for p in price_data if p.get("date"))
                days_since = (datetime.utcnow() - datetime.fromisoformat(latest_date)).days

                # Score: 100 if < 30 days, decreasing to 0 at 365 days
                timeliness_pct = max(0, 100 - (days_since - 30) * (100 / 335)) if days_since > 30 else 100
                score["components"]["timeliness"] = round(timeliness_pct, 2)
            else:
                score["components"]["timeliness"] = 0

            # Consistency score (placeholder - would need more complex analysis)
            score["components"]["consistency"] = 85  # Placeholder

            # Calculate weighted overall score
            score["overall"] = round(
                score["components"]["completeness"] * 0.4 +
                score["components"]["validity"] * 0.3 +
                score["components"]["consistency"] * 0.2 +
                score["components"]["timeliness"] * 0.1,
                2
            )

        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            score["error"] = str(e)

        return score

    async def _get_quality_alerts(self) -> List[Dict[str, str]]:
        """
        Get active data quality alerts.

        Returns:
            List of alert dictionaries
        """
        alerts = []

        try:
            # Check for low record counts
            counts = await self._get_record_counts()

            if counts.get("prices", 0) < 100:
                alerts.append({
                    "severity": "warning",
                    "category": "coverage",
                    "message": f"Low price data volume: {counts['prices']} records",
                    "recommendation": "Collect more historical data"
                })

            if counts.get("production", 0) < 50:
                alerts.append({
                    "severity": "warning",
                    "category": "coverage",
                    "message": f"Low production data volume: {counts['production']} records",
                    "recommendation": "Enable ODC collector or add more sources"
                })

            # Check for recent data
            prices = self.client.table("prices").select("date").order("date", desc=True).limit(1).execute()
            if prices.data:
                latest_date = prices.data[0]["date"]
                days_since = (datetime.utcnow() - datetime.fromisoformat(latest_date)).days

                if days_since > 90:
                    alerts.append({
                        "severity": "error",
                        "category": "timeliness",
                        "message": f"Price data is {days_since} days old",
                        "recommendation": "Run collectors to fetch recent data"
                    })

            # Check for null values
            price_data = self.client.table("prices").select("*").execute().data
            if price_data:
                null_count = sum(1 for p in price_data if not p.get("commodity_id") or not p.get("date"))
                if null_count > 0:
                    alerts.append({
                        "severity": "error",
                        "category": "integrity",
                        "message": f"{null_count} records with null critical fields",
                        "recommendation": "Review and fix data collection processes"
                    })

        except Exception as e:
            logger.error(f"Error getting quality alerts: {e}")
            alerts.append({
                "severity": "error",
                "category": "system",
                "message": f"Error checking alerts: {str(e)}",
                "recommendation": "Check system logs"
            })

        return alerts


# Standalone async functions for backward compatibility

async def get_quality_metrics(supabase_client: Client) -> Dict[str, Any]:
    """
    Get comprehensive quality metrics.

    Args:
        supabase_client: Supabase client instance

    Returns:
        Dictionary with all quality metrics
    """
    service = DataQualityService(supabase_client)

    return {
        "summary": await service.get_quality_summary(),
        "coverage": await service.get_coverage_metrics(),
        "completeness": await service.get_completeness_metrics(),
        "gaps": await service.get_temporal_gaps(),
        "outliers": await service.detect_outliers()
    }
