"""
Cambodia Agri Analytics - Data Quality Audit Script

This script performs comprehensive data quality checks on the Supabase database:
1. Data integrity (null values, outliers, invalid ranges)
2. Inter-source consistency (MEF vs WITS comparisons)
3. Temporal continuity (gaps in date sequences)
4. Duplicate detection (despite upsert mechanisms)
5. Foreign key validity (commodity_id references)
6. Unit validation (thousand_usd vs usd)
7. Coverage analysis (commodities, provinces, time periods)

Outputs:
- JSON report (data_quality_report.json)
- Markdown report (DATA_QUALITY_REPORT.md)
- Console summary
"""

import asyncio
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()


class DataQualityAuditor:
    """
    Performs comprehensive data quality audits on Cambodia Agri Analytics database.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize auditor with Supabase credentials.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
        """
        self.client = create_client(supabase_url, supabase_key)
        self.report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            },
            "summary": {},
            "integrity_checks": {},
            "consistency_checks": {},
            "temporal_checks": {},
            "coverage_metrics": {},
            "recommendations": []
        }

    async def run_full_audit(self) -> Dict[str, Any]:
        """
        Run complete data quality audit.

        Returns:
            Complete audit report dictionary
        """
        logger.info("Starting full data quality audit...")

        # 1. Database summary
        logger.info("Collecting database summary...")
        self.report["summary"] = await self._collect_summary()

        # 2. Integrity checks
        logger.info("Running integrity checks...")
        self.report["integrity_checks"] = await self._check_data_integrity()

        # 3. Consistency checks
        logger.info("Running consistency checks...")
        self.report["consistency_checks"] = await self._check_inter_source_consistency()

        # 4. Temporal checks
        logger.info("Running temporal continuity checks...")
        self.report["temporal_checks"] = await self._check_temporal_continuity()

        # 5. Coverage metrics
        logger.info("Calculating coverage metrics...")
        self.report["coverage_metrics"] = await self._calculate_coverage_metrics()

        # 6. Generate recommendations
        logger.info("Generating recommendations...")
        self.report["recommendations"] = self._generate_recommendations()

        logger.info("Audit complete!")
        return self.report

    async def _collect_summary(self) -> Dict[str, Any]:
        """Collect database summary statistics."""
        summary = {}

        tables = ["commodities", "prices", "production", "perplexity_analyses",
                  "claude_reports", "data_sources"]

        for table in tables:
            try:
                result = self.client.table(table).select("id", count="exact").execute()
                summary[f"{table}_count"] = result.count
            except Exception as e:
                logger.error(f"Error counting {table}: {e}")
                summary[f"{table}_count"] = 0

        # Get distinct sources
        try:
            price_sources = self.client.table("prices").select("source").execute()
            summary["price_sources"] = list(set(row["source"] for row in price_sources.data))

            prod_sources = self.client.table("production").select("source").execute()
            summary["production_sources"] = list(set(row["source"] for row in prod_sources.data))
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            summary["price_sources"] = []
            summary["production_sources"] = []

        return summary

    async def _check_data_integrity(self) -> Dict[str, Any]:
        """
        Check data integrity across tables.

        Checks:
        - Null values in critical fields
        - Invalid price/production values (negative, zero, extreme outliers)
        - Foreign key validity (commodity_id)
        - Unit consistency
        """
        integrity = {
            "prices": await self._check_prices_integrity(),
            "production": await self._check_production_integrity(),
            "foreign_keys": await self._check_foreign_keys()
        }

        return integrity

    async def _check_prices_integrity(self) -> Dict[str, Any]:
        """Check prices table integrity."""
        checks = {}

        # Get all prices
        try:
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data
            total_count = len(price_data)

            # Null value checks
            null_commodity_id = sum(1 for p in price_data if not p.get("commodity_id"))
            null_date = sum(1 for p in price_data if not p.get("date"))
            null_price = sum(1 for p in price_data if p.get("price_usd_per_unit") is None)
            null_source = sum(1 for p in price_data if not p.get("source"))

            checks["null_values"] = {
                "total_records": total_count,
                "null_commodity_id": null_commodity_id,
                "null_date": null_date,
                "null_price_usd_per_unit": null_price,
                "null_source": null_source,
                "null_percentage": round((null_commodity_id + null_date + null_price + null_source) / (total_count * 4) * 100, 2) if total_count > 0 else 0
            }

            # Invalid value checks
            negative_prices = sum(1 for p in price_data if p.get("price_usd_per_unit") and p["price_usd_per_unit"] < 0)
            zero_prices = sum(1 for p in price_data if p.get("price_usd_per_unit") == 0)

            # Outlier detection (values > 3 std dev from mean)
            valid_prices = [p["price_usd_per_unit"] for p in price_data if p.get("price_usd_per_unit") and p["price_usd_per_unit"] > 0]
            if valid_prices:
                import statistics
                mean_price = statistics.mean(valid_prices)
                stdev_price = statistics.stdev(valid_prices) if len(valid_prices) > 1 else 0
                outliers = [p for p in valid_prices if abs(p - mean_price) > 3 * stdev_price]

                checks["value_validation"] = {
                    "negative_prices": negative_prices,
                    "zero_prices": zero_prices,
                    "outliers_count": len(outliers),
                    "mean_price": round(mean_price, 2),
                    "stdev_price": round(stdev_price, 2),
                    "min_price": round(min(valid_prices), 2),
                    "max_price": round(max(valid_prices), 2)
                }
            else:
                checks["value_validation"] = {
                    "negative_prices": negative_prices,
                    "zero_prices": zero_prices,
                    "outliers_count": 0,
                    "error": "No valid prices found"
                }

            # Unit consistency check
            thousand_usd_count = sum(1 for p in price_data
                                    if p.get("metadata") and
                                    isinstance(p["metadata"], dict) and
                                    p["metadata"].get("value_unit") == "thousand_usd")

            usd_count = sum(1 for p in price_data
                           if p.get("metadata") and
                           isinstance(p["metadata"], dict) and
                           p["metadata"].get("value_unit") == "usd")

            no_unit_count = total_count - thousand_usd_count - usd_count

            checks["unit_consistency"] = {
                "thousand_usd_records": thousand_usd_count,
                "usd_records": usd_count,
                "no_unit_specified": no_unit_count,
                "warning": "Mixed units detected" if usd_count > 0 and thousand_usd_count > 0 else None
            }

            # Duplicate check (despite upsert)
            # Check for records with same commodity_id, date, source, destination_country
            duplicates = []
            seen = set()
            for p in price_data:
                key = (
                    p.get("commodity_id"),
                    p.get("date"),
                    p.get("source"),
                    p.get("destination_country")
                )
                if key in seen:
                    duplicates.append(key)
                else:
                    seen.add(key)

            checks["duplicates"] = {
                "potential_duplicates": len(duplicates),
                "sample_duplicates": list(duplicates[:5]) if duplicates else []
            }

        except Exception as e:
            logger.error(f"Error checking prices integrity: {e}")
            checks["error"] = str(e)

        return checks

    async def _check_production_integrity(self) -> Dict[str, Any]:
        """Check production table integrity."""
        checks = {}

        try:
            production = self.client.table("production").select("*").execute()
            prod_data = production.data
            total_count = len(prod_data)

            # Null value checks
            null_commodity_id = sum(1 for p in prod_data if not p.get("commodity_id"))
            null_year = sum(1 for p in prod_data if not p.get("year"))
            null_province = sum(1 for p in prod_data if not p.get("province"))
            null_source = sum(1 for p in prod_data if not p.get("source"))

            checks["null_values"] = {
                "total_records": total_count,
                "null_commodity_id": null_commodity_id,
                "null_year": null_year,
                "null_province": null_province,
                "null_source": null_source
            }

            # Data completeness (optional fields)
            has_area = sum(1 for p in prod_data if p.get("area_hectares") is not None)
            has_production = sum(1 for p in prod_data if p.get("production_tons") is not None)
            has_yield = sum(1 for p in prod_data if p.get("yield_kg_per_ha") is not None)
            has_geolocation = sum(1 for p in prod_data if p.get("geolocation") is not None)

            checks["data_completeness"] = {
                "area_hectares_coverage": round(has_area / total_count * 100, 2) if total_count > 0 else 0,
                "production_tons_coverage": round(has_production / total_count * 100, 2) if total_count > 0 else 0,
                "yield_kg_per_ha_coverage": round(has_yield / total_count * 100, 2) if total_count > 0 else 0,
                "geolocation_coverage": round(has_geolocation / total_count * 100, 2) if total_count > 0 else 0
            }

            # Invalid value checks
            negative_area = sum(1 for p in prod_data if p.get("area_hectares") and p["area_hectares"] < 0)
            negative_production = sum(1 for p in prod_data if p.get("production_tons") and p["production_tons"] < 0)
            negative_yield = sum(1 for p in prod_data if p.get("yield_kg_per_ha") and p["yield_kg_per_ha"] < 0)

            checks["value_validation"] = {
                "negative_area": negative_area,
                "negative_production": negative_production,
                "negative_yield": negative_yield
            }

            # Duplicate check
            duplicates = []
            seen = set()
            for p in prod_data:
                key = (
                    p.get("commodity_id"),
                    p.get("year"),
                    p.get("province"),
                    p.get("source")
                )
                if key in seen:
                    duplicates.append(key)
                else:
                    seen.add(key)

            checks["duplicates"] = {
                "potential_duplicates": len(duplicates),
                "sample_duplicates": list(duplicates[:5]) if duplicates else []
            }

        except Exception as e:
            logger.error(f"Error checking production integrity: {e}")
            checks["error"] = str(e)

        return checks

    async def _check_foreign_keys(self) -> Dict[str, Any]:
        """Check foreign key validity."""
        checks = {}

        try:
            # Get all commodity IDs
            commodities = self.client.table("commodities").select("id, name").execute()
            valid_commodity_ids = set(c["id"] for c in commodities.data)
            commodity_map = {c["id"]: c["name"] for c in commodities.data}

            # Check prices
            prices = self.client.table("prices").select("commodity_id").execute()
            price_commodity_ids = [p["commodity_id"] for p in prices.data]
            invalid_price_fks = sum(1 for cid in price_commodity_ids if cid not in valid_commodity_ids)

            # Check production
            production = self.client.table("production").select("commodity_id").execute()
            prod_commodity_ids = [p["commodity_id"] for p in production.data]
            invalid_prod_fks = sum(1 for cid in prod_commodity_ids if cid not in valid_commodity_ids)

            checks["foreign_key_validation"] = {
                "valid_commodity_ids": list(valid_commodity_ids),
                "commodity_names": commodity_map,
                "prices_invalid_fk": invalid_price_fks,
                "production_invalid_fk": invalid_prod_fks,
                "status": "PASS" if invalid_price_fks == 0 and invalid_prod_fks == 0 else "FAIL"
            }

        except Exception as e:
            logger.error(f"Error checking foreign keys: {e}")
            checks["error"] = str(e)

        return checks

    async def _check_inter_source_consistency(self) -> Dict[str, Any]:
        """
        Check consistency between different data sources.

        Compares MEF vs WITS export values for overlapping periods.
        """
        consistency = {}

        try:
            # Get all prices grouped by source
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data

            # Group by commodity and date
            by_commodity_date = defaultdict(list)
            for p in price_data:
                key = (p.get("commodity_id"), p.get("date"))
                by_commodity_date[key].append(p)

            # Find overlaps between sources
            overlaps = []
            for (commodity_id, date), records in by_commodity_date.items():
                if len(records) > 1:
                    sources = [r["source"] for r in records]
                    if "MEF" in sources and "WITS" in sources:
                        mef_record = next(r for r in records if r["source"] == "MEF")
                        wits_record = next(r for r in records if r["source"] == "WITS")

                        mef_value = mef_record.get("price_usd_per_unit", 0)
                        wits_value = wits_record.get("price_usd_per_unit", 0)

                        # Calculate percentage difference
                        if mef_value > 0 and wits_value > 0:
                            diff_pct = abs(mef_value - wits_value) / ((mef_value + wits_value) / 2) * 100

                            overlaps.append({
                                "commodity_id": commodity_id,
                                "date": date,
                                "mef_value": mef_value,
                                "wits_value": wits_value,
                                "difference_percentage": round(diff_pct, 2)
                            })

            consistency["source_comparison"] = {
                "total_overlapping_records": len(overlaps),
                "sample_comparisons": overlaps[:10] if overlaps else [],
                "high_discrepancy_count": sum(1 for o in overlaps if o["difference_percentage"] > 20),
                "avg_difference_percentage": round(sum(o["difference_percentage"] for o in overlaps) / len(overlaps), 2) if overlaps else 0
            }

        except Exception as e:
            logger.error(f"Error checking inter-source consistency: {e}")
            consistency["error"] = str(e)

        return consistency

    async def _check_temporal_continuity(self) -> Dict[str, Any]:
        """
        Check temporal continuity in data.

        Identifies gaps in date sequences for each commodity and source.
        """
        temporal = {}

        try:
            # Get all prices ordered by date
            prices = self.client.table("prices").select("*").order("date").execute()
            price_data = prices.data

            # Group by commodity and source
            by_commodity_source = defaultdict(list)
            for p in price_data:
                key = (p.get("commodity_id"), p.get("source"))
                by_commodity_source[key].append(p["date"])

            # Find gaps (missing months)
            gaps_analysis = []
            for (commodity_id, source), dates in by_commodity_source.items():
                if len(dates) < 2:
                    continue

                dates_sorted = sorted(dates)
                gaps = []

                for i in range(len(dates_sorted) - 1):
                    current = datetime.fromisoformat(dates_sorted[i])
                    next_date = datetime.fromisoformat(dates_sorted[i + 1])

                    # Calculate expected gap (in days)
                    gap_days = (next_date - current).days

                    # Flag gaps > 60 days (roughly 2 months)
                    if gap_days > 60:
                        gaps.append({
                            "from": dates_sorted[i],
                            "to": dates_sorted[i + 1],
                            "gap_days": gap_days
                        })

                if gaps:
                    gaps_analysis.append({
                        "commodity_id": commodity_id,
                        "source": source,
                        "total_records": len(dates_sorted),
                        "date_range": f"{dates_sorted[0]} to {dates_sorted[-1]}",
                        "gaps_count": len(gaps),
                        "largest_gap_days": max(g["gap_days"] for g in gaps),
                        "sample_gaps": gaps[:3]
                    })

            temporal["price_gaps"] = {
                "total_commodity_source_combinations": len(by_commodity_source),
                "combinations_with_gaps": len(gaps_analysis),
                "gap_details": gaps_analysis
            }

            # Production temporal analysis
            production = self.client.table("production").select("*").order("year").execute()
            prod_data = production.data

            by_commodity_province = defaultdict(list)
            for p in prod_data:
                key = (p.get("commodity_id"), p.get("province"), p.get("source"))
                by_commodity_province[key].append(p["year"])

            prod_gaps = []
            for (commodity_id, province, source), years in by_commodity_province.items():
                if len(years) < 2:
                    continue

                years_sorted = sorted(years)
                gaps = []

                for i in range(len(years_sorted) - 1):
                    gap = years_sorted[i + 1] - years_sorted[i]
                    if gap > 1:  # Missing year(s)
                        gaps.append({
                            "from": years_sorted[i],
                            "to": years_sorted[i + 1],
                            "missing_years": gap - 1
                        })

                if gaps:
                    prod_gaps.append({
                        "commodity_id": commodity_id,
                        "province": province,
                        "source": source,
                        "year_range": f"{years_sorted[0]} to {years_sorted[-1]}",
                        "gaps_count": len(gaps),
                        "sample_gaps": gaps[:3]
                    })

            temporal["production_gaps"] = {
                "total_combinations": len(by_commodity_province),
                "combinations_with_gaps": len(prod_gaps),
                "gap_details": prod_gaps
            }

        except Exception as e:
            logger.error(f"Error checking temporal continuity: {e}")
            temporal["error"] = str(e)

        return temporal

    async def _calculate_coverage_metrics(self) -> Dict[str, Any]:
        """
        Calculate coverage metrics.

        Measures:
        - Coverage by commodity (cashew vs rubber)
        - Coverage by source
        - Temporal coverage (date ranges)
        - Geographic coverage (provinces)
        - Field completeness percentages
        """
        coverage = {}

        try:
            # Get commodities
            commodities = self.client.table("commodities").select("*").execute()
            commodity_map = {c["id"]: c["name"] for c in commodities.data}

            # Price coverage by commodity
            prices = self.client.table("prices").select("*").execute()
            price_data = prices.data

            price_by_commodity = defaultdict(int)
            for p in price_data:
                commodity_name = commodity_map.get(p["commodity_id"], "unknown")
                price_by_commodity[commodity_name] += 1

            coverage["price_coverage_by_commodity"] = dict(price_by_commodity)

            # Price coverage by source
            price_by_source = defaultdict(int)
            for p in price_data:
                price_by_source[p["source"]] += 1

            coverage["price_coverage_by_source"] = dict(price_by_source)

            # Temporal coverage for prices
            if price_data:
                dates = [p["date"] for p in price_data if p.get("date")]
                coverage["price_temporal_coverage"] = {
                    "earliest_date": min(dates) if dates else None,
                    "latest_date": max(dates) if dates else None,
                    "total_records": len(price_data)
                }

            # Production coverage
            production = self.client.table("production").select("*").execute()
            prod_data = production.data

            prod_by_commodity = defaultdict(int)
            for p in prod_data:
                commodity_name = commodity_map.get(p["commodity_id"], "unknown")
                prod_by_commodity[commodity_name] += 1

            coverage["production_coverage_by_commodity"] = dict(prod_by_commodity)

            # Geographic coverage
            provinces = list(set(p["province"] for p in prod_data if p.get("province")))
            coverage["geographic_coverage"] = {
                "total_provinces": len(provinces),
                "provinces": sorted(provinces)
            }

            # Temporal coverage for production
            if prod_data:
                years = [p["year"] for p in prod_data if p.get("year")]
                coverage["production_temporal_coverage"] = {
                    "earliest_year": min(years) if years else None,
                    "latest_year": max(years) if years else None,
                    "total_records": len(prod_data)
                }

        except Exception as e:
            logger.error(f"Error calculating coverage metrics: {e}")
            coverage["error"] = str(e)

        return coverage

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate recommendations based on audit findings.

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Check prices count
        price_count = self.report["summary"].get("prices_count", 0)
        if price_count < 100:
            recommendations.append({
                "priority": "HIGH",
                "category": "Data Coverage",
                "issue": "Low price data volume",
                "recommendation": f"Only {price_count} price records found. Consider collecting more historical data from MEF and WITS.",
                "action": "Extend date range in collectors to fetch 10+ years of data"
            })

        # Check production count
        prod_count = self.report["summary"].get("production_count", 0)
        if prod_count < 50:
            recommendations.append({
                "priority": "HIGH",
                "category": "Data Coverage",
                "issue": "Low production data volume",
                "recommendation": f"Only {prod_count} production records found. Production data is critical for analysis.",
                "action": "Run seed with --include-odc flag, or implement additional scrapers for government agricultural reports"
            })

        # Check for null values
        price_integrity = self.report["integrity_checks"].get("prices", {})
        null_values = price_integrity.get("null_values", {})
        null_pct = null_values.get("null_percentage", 0)

        if null_pct > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Data Integrity",
                "issue": f"High null value percentage ({null_pct}%)",
                "recommendation": "Review collectors to ensure all required fields are extracted properly",
                "action": "Add validation in collectors before storing data"
            })

        # Check for duplicates
        duplicate_count = price_integrity.get("duplicates", {}).get("potential_duplicates", 0)
        if duplicate_count > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Data Integrity",
                "issue": f"Found {duplicate_count} potential duplicate price records",
                "recommendation": "Duplicates should not exist with upsert mechanism. Check if unique constraints are properly applied.",
                "action": "Run migration scripts/migrations/001_add_unique_constraint_prices.sql and re-seed data"
            })

        # Check temporal gaps
        temporal = self.report["temporal_checks"]
        price_gaps = temporal.get("price_gaps", {})
        gaps_count = price_gaps.get("combinations_with_gaps", 0)

        if gaps_count > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Temporal Continuity",
                "issue": f"Found {gaps_count} commodity-source combinations with date gaps",
                "recommendation": "Historical data has gaps. Consider re-collecting data for missing periods.",
                "action": "Review gap_details in report and target specific date ranges for re-collection"
            })

        # Check unit consistency
        unit_check = price_integrity.get("unit_consistency", {})
        if unit_check.get("warning"):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Data Standardization",
                "issue": "Mixed units detected (thousand_usd and usd)",
                "recommendation": "Standardize all price values to the same unit for consistency",
                "action": "Add normalization layer in API or dashboard to convert all to USD"
            })

        # Check source diversity
        price_sources = self.report["summary"].get("price_sources", [])
        if len(price_sources) < 3:
            recommendations.append({
                "priority": "LOW",
                "category": "Data Coverage",
                "issue": f"Limited data sources ({len(price_sources)} sources)",
                "recommendation": "Diversify data sources to improve reliability and coverage",
                "action": "Add FAO, UNCTAD, or local market price collectors"
            })

        # Check geographic coverage
        coverage = self.report["coverage_metrics"]
        geo_coverage = coverage.get("geographic_coverage", {})
        province_count = geo_coverage.get("total_provinces", 0)

        if province_count < 10:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Geographic Coverage",
                "issue": f"Limited geographic coverage ({province_count} provinces)",
                "recommendation": "Cambodia has 25 provinces. Expand data collection to cover more regions.",
                "action": "Search for provincial-level agricultural statistics or KML files for missing provinces"
            })

        # Check completeness
        prod_integrity = self.report["integrity_checks"].get("production", {})
        completeness = prod_integrity.get("data_completeness", {})

        low_fields = []
        for field, pct in completeness.items():
            if pct < 50:
                low_fields.append((field, pct))

        if low_fields:
            recommendations.append({
                "priority": "LOW",
                "category": "Data Completeness",
                "issue": f"Low completeness for: {', '.join(f[0] for f in low_fields)}",
                "recommendation": "Enrich production data with missing fields where possible",
                "action": "Cross-reference with additional sources or use estimation models for missing values"
            })

        # Always recommend running analyses
        analyses_count = self.report["summary"].get("perplexity_analyses_count", 0)
        reports_count = self.report["summary"].get("claude_reports_count", 0)

        if analyses_count == 0 or reports_count == 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Analytics",
                "issue": "No AI analyses or reports generated yet",
                "recommendation": "Run daily_pipeline to generate Perplexity analyses and Claude reports",
                "action": "Execute: python scripts/seed_collectors.py (then wait for scheduled job, or manually trigger daily_pipeline)"
            })

        return recommendations


async def main():
    """Main execution function."""
    # Load credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)

    # Run audit
    auditor = DataQualityAuditor(supabase_url, supabase_key)
    report = await auditor.run_full_audit()

    # Save JSON report
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "data_quality_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"JSON report saved to: {json_path}")

    # Generate Markdown report
    md_report = generate_markdown_report(report)
    md_path = output_dir / "DATA_QUALITY_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    logger.info(f"Markdown report saved to: {md_path}")

    # Print summary to console
    print_console_summary(report)


def generate_markdown_report(report: Dict[str, Any]) -> str:
    """
    Generate Markdown report from audit results.

    Args:
        report: Audit report dictionary

    Returns:
        Markdown formatted report
    """
    md = []
    md.append("# Cambodia Agri Analytics - Data Quality Report")
    md.append("")
    md.append(f"**Generated:** {report['metadata']['generated_at']}")
    md.append(f"**Version:** {report['metadata']['version']}")
    md.append("")

    # Summary
    md.append("## Executive Summary")
    md.append("")
    summary = report["summary"]
    md.append(f"- **Commodities:** {summary.get('commodities_count', 0)}")
    md.append(f"- **Price Records:** {summary.get('prices_count', 0)}")
    md.append(f"- **Production Records:** {summary.get('production_count', 0)}")
    md.append(f"- **Analyses:** {summary.get('perplexity_analyses_count', 0)}")
    md.append(f"- **Reports:** {summary.get('claude_reports_count', 0)}")
    md.append(f"- **Price Sources:** {', '.join(summary.get('price_sources', []))}")
    md.append(f"- **Production Sources:** {', '.join(summary.get('production_sources', []))}")
    md.append("")

    # Integrity Checks
    md.append("## Integrity Checks")
    md.append("")

    integrity = report["integrity_checks"]

    md.append("### Prices Table")
    md.append("")
    prices_integrity = integrity.get("prices", {})

    if "null_values" in prices_integrity:
        null_vals = prices_integrity["null_values"]
        md.append(f"- **Total Records:** {null_vals.get('total_records', 0)}")
        md.append(f"- **Null Percentage:** {null_vals.get('null_percentage', 0)}%")
        md.append(f"- **Null commodity_id:** {null_vals.get('null_commodity_id', 0)}")
        md.append(f"- **Null date:** {null_vals.get('null_date', 0)}")
        md.append(f"- **Null price_usd_per_unit:** {null_vals.get('null_price_usd_per_unit', 0)}")
        md.append(f"- **Null source:** {null_vals.get('null_source', 0)}")
        md.append("")

    if "value_validation" in prices_integrity:
        val_check = prices_integrity["value_validation"]
        md.append("**Value Validation:**")
        md.append(f"- Negative prices: {val_check.get('negative_prices', 0)}")
        md.append(f"- Zero prices: {val_check.get('zero_prices', 0)}")
        md.append(f"- Outliers (>3σ): {val_check.get('outliers_count', 0)}")
        md.append(f"- Mean price: ${val_check.get('mean_price', 0)}")
        md.append(f"- Price range: ${val_check.get('min_price', 0)} - ${val_check.get('max_price', 0)}")
        md.append("")

    if "unit_consistency" in prices_integrity:
        units = prices_integrity["unit_consistency"]
        md.append("**Unit Consistency:**")
        md.append(f"- thousand_usd: {units.get('thousand_usd_records', 0)}")
        md.append(f"- usd: {units.get('usd_records', 0)}")
        md.append(f"- No unit specified: {units.get('no_unit_specified', 0)}")
        if units.get("warning"):
            md.append(f"- ⚠️ **Warning:** {units['warning']}")
        md.append("")

    if "duplicates" in prices_integrity:
        dups = prices_integrity["duplicates"]
        md.append(f"**Duplicates:** {dups.get('potential_duplicates', 0)} potential duplicates found")
        md.append("")

    md.append("### Production Table")
    md.append("")
    prod_integrity = integrity.get("production", {})

    if "null_values" in prod_integrity:
        null_vals = prod_integrity["null_values"]
        md.append(f"- **Total Records:** {null_vals.get('total_records', 0)}")
        md.append("")

    if "data_completeness" in prod_integrity:
        completeness = prod_integrity["data_completeness"]
        md.append("**Data Completeness:**")
        md.append(f"- Area (hectares): {completeness.get('area_hectares_coverage', 0)}%")
        md.append(f"- Production (tons): {completeness.get('production_tons_coverage', 0)}%")
        md.append(f"- Yield (kg/ha): {completeness.get('yield_kg_per_ha_coverage', 0)}%")
        md.append(f"- Geolocation: {completeness.get('geolocation_coverage', 0)}%")
        md.append("")

    # Foreign Keys
    md.append("### Foreign Key Validation")
    md.append("")
    fk_check = integrity.get("foreign_keys", {}).get("foreign_key_validation", {})
    md.append(f"- **Status:** {fk_check.get('status', 'UNKNOWN')}")
    md.append(f"- **Valid Commodity IDs:** {len(fk_check.get('valid_commodity_ids', []))}")
    md.append(f"- **Prices Invalid FK:** {fk_check.get('prices_invalid_fk', 0)}")
    md.append(f"- **Production Invalid FK:** {fk_check.get('production_invalid_fk', 0)}")
    md.append("")

    # Consistency Checks
    md.append("## Consistency Checks")
    md.append("")
    consistency = report["consistency_checks"]

    if "source_comparison" in consistency:
        comp = consistency["source_comparison"]
        md.append(f"- **Overlapping Records (MEF vs WITS):** {comp.get('total_overlapping_records', 0)}")
        md.append(f"- **High Discrepancy Count (>20%):** {comp.get('high_discrepancy_count', 0)}")
        md.append(f"- **Average Difference:** {comp.get('avg_difference_percentage', 0)}%")
        md.append("")

    # Temporal Checks
    md.append("## Temporal Continuity")
    md.append("")
    temporal = report["temporal_checks"]

    if "price_gaps" in temporal:
        price_gaps = temporal["price_gaps"]
        md.append(f"### Price Data Gaps")
        md.append(f"- **Commodity-Source Combinations:** {price_gaps.get('total_commodity_source_combinations', 0)}")
        md.append(f"- **Combinations with Gaps:** {price_gaps.get('combinations_with_gaps', 0)}")
        md.append("")

    if "production_gaps" in temporal:
        prod_gaps = temporal["production_gaps"]
        md.append(f"### Production Data Gaps")
        md.append(f"- **Total Combinations:** {prod_gaps.get('total_combinations', 0)}")
        md.append(f"- **Combinations with Gaps:** {prod_gaps.get('combinations_with_gaps', 0)}")
        md.append("")

    # Coverage Metrics
    md.append("## Coverage Metrics")
    md.append("")
    coverage = report["coverage_metrics"]

    if "price_coverage_by_commodity" in coverage:
        md.append("### Price Coverage by Commodity")
        for commodity, count in coverage["price_coverage_by_commodity"].items():
            md.append(f"- **{commodity}:** {count} records")
        md.append("")

    if "price_coverage_by_source" in coverage:
        md.append("### Price Coverage by Source")
        for source, count in coverage["price_coverage_by_source"].items():
            md.append(f"- **{source}:** {count} records")
        md.append("")

    if "price_temporal_coverage" in coverage:
        temp_cov = coverage["price_temporal_coverage"]
        md.append("### Temporal Coverage (Prices)")
        md.append(f"- **Date Range:** {temp_cov.get('earliest_date', 'N/A')} to {temp_cov.get('latest_date', 'N/A')}")
        md.append("")

    if "geographic_coverage" in coverage:
        geo_cov = coverage["geographic_coverage"]
        md.append("### Geographic Coverage")
        md.append(f"- **Total Provinces:** {geo_cov.get('total_provinces', 0)}")
        md.append(f"- **Provinces:** {', '.join(geo_cov.get('provinces', []))}")
        md.append("")

    # Recommendations
    md.append("## Recommendations")
    md.append("")
    recommendations = report["recommendations"]

    for rec in recommendations:
        md.append(f"### {rec['category']} - Priority: {rec['priority']}")
        md.append(f"**Issue:** {rec['issue']}")
        md.append(f"**Recommendation:** {rec['recommendation']}")
        md.append(f"**Action:** {rec['action']}")
        md.append("")

    return "\n".join(md)


def print_console_summary(report: Dict[str, Any]):
    """
    Print summary to console.

    Args:
        report: Audit report dictionary
    """
    print("\n" + "=" * 80)
    print("DATA QUALITY AUDIT SUMMARY")
    print("=" * 80)

    summary = report["summary"]
    print(f"\nDatabase Records:")
    print(f"  Commodities:     {summary.get('commodities_count', 0)}")
    print(f"  Prices:          {summary.get('prices_count', 0)}")
    print(f"  Production:      {summary.get('production_count', 0)}")
    print(f"  Analyses:        {summary.get('perplexity_analyses_count', 0)}")
    print(f"  Reports:         {summary.get('claude_reports_count', 0)}")

    print(f"\nData Sources:")
    print(f"  Price Sources:   {', '.join(summary.get('price_sources', []))}")
    print(f"  Production Srcs: {', '.join(summary.get('production_sources', []))}")

    integrity = report["integrity_checks"]
    prices_int = integrity.get("prices", {})

    if "null_values" in prices_int:
        null_pct = prices_int["null_values"].get("null_percentage", 0)
        print(f"\nData Quality:")
        print(f"  Null values:     {null_pct}%")

    if "duplicates" in prices_int:
        dup_count = prices_int["duplicates"].get("potential_duplicates", 0)
        print(f"  Duplicates:      {dup_count}")

    recommendations = report["recommendations"]
    high_priority = [r for r in recommendations if r["priority"] == "HIGH"]

    print(f"\nRecommendations:")
    print(f"  Total:           {len(recommendations)}")
    print(f"  High Priority:   {len(high_priority)}")

    if high_priority:
        print(f"\n⚠️  HIGH PRIORITY ISSUES:")
        for rec in high_priority[:3]:
            print(f"    - {rec['issue']}")

    print("\n" + "=" * 80)
    print("Full reports saved to reports/ directory")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
