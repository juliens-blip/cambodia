"""MEF Cambodia API collector."""
import logging
from datetime import datetime
from typing import Any, Dict, List

import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class MEFCollector(BaseCollector):
    """Collector for MEF Cambodia (Ministry of Economy and Finance) API."""

    def __init__(self, api_url: str, dataset_id: str = "pd_68b588a0eb43bd000745b588"):
        """
        Initialize MEF collector.

        Args:
            api_url: MEF API base URL
            dataset_id: MEF public dataset ID
        """
        super().__init__("MEF")
        self.api_url = api_url.rstrip("/")
        self.dataset_id = dataset_id

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from MEF API.

        Returns:
            List of price records
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                records = []
                headers = {"User-Agent": "Mozilla/5.0"}

                page = 1
                max_pages = 5

                while page <= max_pages:
                    url = f"{self.api_url}/{self.dataset_id}/json"
                    params = {"page": page, "page_size": 200}

                    try:
                        response = await client.get(url, params=params, headers=headers)
                        response.raise_for_status()
                    except httpx.TransportError as exc:
                        logger.warning(f"SSL issue from MEF, retrying without verification: {exc}")
                        async with httpx.AsyncClient(timeout=30.0, verify=False) as insecure_client:
                            response = await insecure_client.get(url, params=params, headers=headers)
                            response.raise_for_status()

                    data = response.json()
                    items = data.get("items") or []

                    for item in items:
                        commodity_name = str(item.get("commodity", "")).lower()

                        if "cashew" in commodity_name or "anacard" in commodity_name:
                            commodity = "cashew"
                        elif any(term in commodity_name for term in ["rubber", "caoutch", "latex", "hevea"]):
                            commodity = "rubber"
                        else:
                            continue

                        year = item.get("year")
                        month = item.get("month_num") or 1
                        try:
                            year_int = int(float(year))
                            month_int = max(1, min(12, int(float(month))))
                            date_value = f"{year_int:04d}-{month_int:02d}-01"
                        except (TypeError, ValueError):
                            continue

                        value_thousand_usd = item.get("value_thousand_usd")
                        try:
                            value_thousand_usd_float = float(value_thousand_usd)
                        except (TypeError, ValueError):
                            continue

                        if value_thousand_usd_float <= 0:
                            continue

                        price_usd = value_thousand_usd_float

                        record = {
                            "commodity": commodity,
                            "date": date_value,
                            "price_usd": price_usd,
                            "volume_tons": None,
                            "destination_country": None,
                            "quality_grade": None,
                            "source": "MEF",
                            "metadata": {
                                "metric_type": "export_value_usd",
                                "value_unit": "thousand_usd",
                                "calculation": "value_usd = value_thousand_usd * 1000",
                                "chapter": item.get("chapter"),
                                "month_abb": item.get("month_abb"),
                                "value_thousand_usd": value_thousand_usd_float,
                                "row_number": item.get("row_number")
                            }
                        }
                        records.append(record)

                    total_pages = data.get("total_pages") or page
                    if page >= total_pages:
                        break
                    page += 1

                return records

            except httpx.HTTPStatusError as e:
                logger.error(f"MEF API HTTP error: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"MEF API error: {e}")
                raise

    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate MEF data record.

        Args:
            data: Data record to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["commodity", "date", "price_usd", "source"]

        if not all(field in data for field in required_fields):
            return False

        if data["commodity"] not in ["cashew", "rubber"]:
            return False

        if not isinstance(data["price_usd"], (int, float)) or data["price_usd"] <= 0:
            return False

        try:
            if isinstance(data["date"], str):
                datetime.fromisoformat(data["date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return False

        return True
