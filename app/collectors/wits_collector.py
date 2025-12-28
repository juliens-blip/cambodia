"""WITS World Bank API collector."""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class WITSCollector(BaseCollector):
    """Collector for WITS World Bank trade data."""

    def __init__(
        self,
        api_url: str,
        reporter: str = "KHM",
        product_map: Optional[Dict[str, str]] = None,
        partner: str = "wld"
    ):
        """
        Initialize WITS collector.

        Args:
            api_url: WITS API base URL
            reporter: ISO3 reporter code (default KHM)
            product_map: Optional mapping of commodity to WITS product group codes
        """
        super().__init__("WITS")
        self.base_url = self._normalize_base_url(api_url)
        self.reporter = reporter.lower()
        self.product_map = product_map or {
            "cashew": "16-24_FoodProd",
            "rubber": "39-40_PlastiRub"
        }
        self.indicator = "XPRT-TRD-VL"
        self.partner = partner.lower()

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from WITS TradeStats API.

        Returns:
            List of trade records
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                records = []
                headers = {"User-Agent": "Mozilla/5.0"}
                year_list = self._build_year_list(years_back=5)

                for commodity, product_code in self.product_map.items():
                    url = (
                        f"{self.base_url}/SDMX/V21/datasource/tradestats-trade"
                        f"/reporter/{self.reporter}"
                        f"/year/{year_list}"
                        f"/partner/{self.partner}"
                        f"/product/{product_code}"
                        f"/indicator/{self.indicator}"
                    )

                    try:
                        response = await client.get(url, params={"format": "JSON"}, headers=headers)
                        response.raise_for_status()
                        payload = response.json()
                        records.extend(self._parse_sdmx_json(payload, commodity, product_code))

                    except httpx.HTTPStatusError as e:
                        logger.warning(
                            "WITS API error for product %s: %s",
                            product_code,
                            e.response.status_code
                        )
                        continue

                return records

            except Exception as e:
                logger.error(f"WITS API error: {e}")
                raise

    def _normalize_base_url(self, api_url: str) -> str:
        if "/API/V1" in api_url:
            return api_url.split("/API/V1")[0] + "/API/V1"
        return api_url.rstrip("/")

    def _build_year_list(self, years_back: int = 5) -> str:
        current_year = datetime.utcnow().year
        start_year = max(1988, current_year - years_back + 1)
        return ";".join(str(year) for year in range(start_year, current_year + 1))

    def _parse_sdmx_json(
        self,
        payload: Dict[str, Any],
        commodity: str,
        product_code: str
    ) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []

        data_sets = payload.get("dataSets") or []
        if not data_sets:
            return records

        series = data_sets[0].get("series") or {}
        structure = payload.get("structure") or {}
        dimensions = structure.get("dimensions") or {}
        series_dims = dimensions.get("series") or []
        obs_dims = dimensions.get("observation") or []

        if not series_dims or not obs_dims:
            return records

        obs_values = obs_dims[0].get("values") or []

        for key, series_data in series.items():
            try:
                index_values = [int(idx) for idx in key.split(":")]
            except ValueError:
                continue

            if len(index_values) != len(series_dims):
                continue

            dim_values = []
            for dim, idx in zip(series_dims, index_values):
                values = dim.get("values") or []
                dim_values.append(values[idx] if idx < len(values) else {})

            freq, reporter, partner, product, indicator = dim_values
            partner_code = partner.get("id") or ""
            partner_name = partner.get("name") or partner_code
            indicator_name = indicator.get("name") or indicator.get("id")
            product_name = product.get("name") or product_code

            observations = series_data.get("observations") or {}
            for obs_key, obs_value in observations.items():
                try:
                    obs_index = int(obs_key)
                except ValueError:
                    continue

                if obs_index >= len(obs_values):
                    continue

                time_value = obs_values[obs_index].get("id")
                if not time_value:
                    continue

                try:
                    value_thousand_usd = float(obs_value[0])
                except (TypeError, ValueError, IndexError):
                    continue

                if value_thousand_usd <= 0:
                    continue

                record = {
                    "commodity": commodity,
                    "date": f"{time_value}-01-01",
                    "price_usd": value_thousand_usd,
                    "volume_tons": None,
                    "destination_country": partner_name,
                    "source": "WITS",
                    "metadata": {
                        "metric_type": "export_value_usd",
                        "value_unit": "thousand_usd",
                        "calculation": "value_usd = value_thousand_usd * 1000",
                        "indicator": indicator.get("id"),
                        "indicator_name": indicator_name,
                        "product_code": product_code,
                        "product_name": product_name,
                        "partner_code": partner_code,
                        "reporter_code": reporter.get("id"),
                        "frequency": freq.get("id")
                    }
                }
                records.append(record)

        return records

    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate WITS data record.

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

        if not isinstance(data["price_usd"], (int, float)) or data["price_usd"] < 0:
            return False

        return True
