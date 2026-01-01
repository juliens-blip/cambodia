"""WITS World Bank API collector."""
import io
import logging
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class WITSCollector(BaseCollector):
    """Collector for WITS World Bank trade data."""

    def __init__(
        self,
        api_url: str,
        reporter: str = "KHM",
        product_map: Optional[Dict[str, str]] = None,
        partner: str = "wld",
        tradeflow: str = "E",
        hs6_download_url: str = "https://wits.worldbank.org/Download.aspx",
        use_hs6_download: bool = True
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
        self.tradeflow = tradeflow.upper()
        self.hs6_download_url = hs6_download_url
        self.use_hs6_download = use_hs6_download

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
                    if self.use_hs6_download and self._is_hs6_product(product_code):
                        records.extend(
                            await self._collect_hs6_download(
                                client,
                                commodity,
                                product_code,
                                year_list.split(";")
                            )
                        )
                        continue

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

    def _is_hs6_product(self, product_code: str) -> bool:
        return product_code.isdigit() and len(product_code) == 6

    async def _collect_hs6_download(
        self,
        client: httpx.AsyncClient,
        commodity: str,
        product_code: str,
        years: List[str]
    ) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        headers = {"User-Agent": "Mozilla/5.0"}

        for year in years:
            params = {
                "Reporter": self.reporter.upper(),
                "Year": year,
                "Tradeflow": self.tradeflow,
                "Partner": self.partner.upper(),
                "product": product_code,
                "Type": "HS6Productdata",
                "Lang": "en"
            }
            try:
                response = await client.get(self.hs6_download_url, params=params, headers=headers)
                response.raise_for_status()
                rows = self._parse_xlsx_rows(response.content)
                records.extend(
                    self._parse_hs6_rows(rows, commodity, product_code, year)
                )
            except httpx.HTTPStatusError as exc:
                logger.warning("WITS HS6 download error (%s): %s", product_code, exc)
                continue

        return records

    def _parse_xlsx_rows(self, content: bytes) -> List[List[str]]:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            shared_strings = self._parse_shared_strings(zf)
            sheet_name = "xl/worksheets/sheet2.xml"
            if sheet_name not in zf.namelist():
                sheet_name = "xl/worksheets/sheet1.xml"
            sheet = zf.read(sheet_name)
            root = ET.fromstring(sheet)
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

            rows = []
            for row in root.findall("s:sheetData/s:row", ns):
                values = self._parse_xlsx_row(row, shared_strings, ns)
                if values:
                    rows.append(values)
            return rows

    def _parse_shared_strings(self, zf: zipfile.ZipFile) -> List[str]:
        if "xl/sharedStrings.xml" not in zf.namelist():
            return []
        data = zf.read("xl/sharedStrings.xml")
        root = ET.fromstring(data)
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        shared_strings = []
        for si in root.findall("s:si", ns):
            parts = [t.text or "" for t in si.findall(".//s:t", ns)]
            shared_strings.append("".join(parts))
        return shared_strings

    def _parse_xlsx_row(
        self,
        row: ET.Element,
        shared_strings: List[str],
        ns: Dict[str, str]
    ) -> List[str]:
        cells = row.findall("s:c", ns)
        if not cells:
            return []

        has_refs = any(cell.get("r") for cell in cells)
        if not has_refs:
            values = []
            for cell in cells:
                value_node = cell.find("s:v", ns)
                if value_node is None:
                    values.append("")
                    continue
                value = value_node.text or ""
                if cell.get("t") == "s":
                    try:
                        value = shared_strings[int(value)]
                    except (ValueError, IndexError):
                        value = ""
                values.append(value)
            return values

        values_map: Dict[int, str] = {}
        max_index = -1
        for cell in cells:
            cell_ref = cell.get("r", "")
            match = re.match(r"([A-Z]+)", cell_ref)
            if not match:
                continue
            col_index = self._column_index(match.group(1))
            value_node = cell.find("s:v", ns)
            if value_node is None:
                continue
            value = value_node.text or ""
            if cell.get("t") == "s":
                try:
                    value = shared_strings[int(value)]
                except (ValueError, IndexError):
                    value = ""
            values_map[col_index] = value
            max_index = max(max_index, col_index)

        if max_index < 0:
            return []
        row_values = [""] * (max_index + 1)
        for index, value in values_map.items():
            row_values[index] = value
        return row_values

    def _parse_hs6_rows(
        self,
        rows: List[List[str]],
        commodity: str,
        product_code: str,
        year: str
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []
        header = [str(col).strip() for col in rows[0]]
        records: List[Dict[str, Any]] = []

        for row in rows[1:]:
            row_map = {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
            trade_value_thousand = self._parse_number(row_map.get("Trade Value 1000USD"))
            if trade_value_thousand is None:
                continue

            value_usd = trade_value_thousand * 1000
            quantity = self._parse_number(row_map.get("Quantity"))
            unit = str(row_map.get("Quantity Unit") or "").strip()
            volume_tons = None
            if quantity is not None:
                unit_lower = unit.lower()
                if unit_lower == "kg":
                    volume_tons = quantity / 1000.0
                elif unit_lower in ["ton", "tons", "tonne", "tonnes"]:
                    volume_tons = quantity

            unit_price_usd = None
            if volume_tons and volume_tons > 0:
                unit_price_usd = value_usd / volume_tons
            if unit_price_usd is None:
                # Skip rows without a computable unit value to avoid overflow.
                continue

            metadata = {
                "metric_type": "export_value_usd",
                "value_unit": "thousand_usd",
                "calculation": "value_usd = value_thousand_usd * 1000",
                "indicator": self.indicator,
                "product_code": product_code,
                "product_name": row_map.get("Product Description"),
                "reporter_name": row_map.get("Reporter"),
                "partner_name": row_map.get("Partner"),
                "tradeflow": row_map.get("TradeFlow") or self.tradeflow,
                "dataset": "WITS_HS6_DOWNLOAD",
                "quantity": quantity,
                "quantity_unit": unit,
                "trade_value_thousand_usd": trade_value_thousand,
                "trade_value_usd": value_usd
            }

            records.append({
                "commodity": commodity,
                "date": f"{year}-01-01",
                "price_usd": float(unit_price_usd),
                "volume_tons": volume_tons,
                "destination_country": row_map.get("Partner") or self.partner.upper(),
                "source": "WITS",
                "metadata": metadata
            })

        return records

    def _column_index(self, letters: str) -> int:
        index = 0
        for char in letters:
            index = index * 26 + (ord(char.upper()) - ord("A") + 1)
        return index - 1

    def _parse_number(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    async def fetch_cambodia_rubber_exports(self, year: int = 2024) -> Dict[str, Any]:
        """
        Fetch Cambodia rubber exports via WITS HS6 download.

        Product: HS 4001 (Natural rubber, latex form)
        Reporter: KHM (Cambodia)

        Args:
            year: Year to fetch data for

        Returns:
            {
                "year": 2024,
                "product": "4001",
                "total_export_tons": 120000,
                "total_export_value_usd": 219000000,
                "avg_price_usd_ton": 1825,
                "top_partners": {
                    "CHN": {"tons": 72000, "value_usd": 131400000},
                    "VNM": {"tons": 24000, "value_usd": 43800000},
                    ...
                }
            }
        """
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            product_code = "4001"  # Natural rubber HS code
            headers = {"User-Agent": "Mozilla/5.0"}

            params = {
                "Reporter": self.reporter.upper(),
                "Year": str(year),
                "Tradeflow": "E",  # Exports
                "Partner": "ALL",  # All partners
                "product": product_code,
                "Type": "HS6Productdata",
                "Lang": "en"
            }

            try:
                response = await client.get(self.hs6_download_url, params=params, headers=headers)
                response.raise_for_status()

                rows = self._parse_xlsx_rows(response.content)
                if not rows or len(rows) < 2:
                    logger.warning(f"WITS: No rubber export data for {year}")
                    return self._empty_rubber_export_result(year)

                # Parse header and data rows
                header = [str(col).strip() for col in rows[0]]

                total_value_usd = 0.0
                total_tons = 0.0
                partners = {}

                for row in rows[1:]:
                    row_map = {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}

                    trade_value_thousand = self._parse_number(row_map.get("Trade Value 1000USD"))
                    if trade_value_thousand is None:
                        continue

                    value_usd = trade_value_thousand * 1000
                    total_value_usd += value_usd

                    # Parse quantity
                    quantity = self._parse_number(row_map.get("Quantity"))
                    unit = str(row_map.get("Quantity Unit") or "").strip().lower()

                    tons = None
                    if quantity is not None:
                        if unit == "kg":
                            tons = quantity / 1000.0
                        elif unit in ["ton", "tons", "tonne", "tonnes"]:
                            tons = quantity

                    if tons:
                        total_tons += tons

                    # Track partners
                    partner_name = row_map.get("Partner", "Unknown")
                    if partner_name not in partners:
                        partners[partner_name] = {"tons": 0.0, "value_usd": 0.0}

                    partners[partner_name]["value_usd"] += value_usd
                    if tons:
                        partners[partner_name]["tons"] += tons

                # Calculate average price
                avg_price_usd_ton = (total_value_usd / total_tons) if total_tons > 0 else 0

                # Get top 5 partners by value
                top_partners = dict(
                    sorted(partners.items(), key=lambda x: x[1]["value_usd"], reverse=True)[:5]
                )

                result = {
                    "year": year,
                    "product": product_code,
                    "product_description": "Natural rubber (latex form)",
                    "total_export_tons": round(total_tons, 2),
                    "total_export_value_usd": round(total_value_usd, 2),
                    "avg_price_usd_ton": round(avg_price_usd_ton, 2),
                    "top_partners": top_partners,
                    "source": "WITS",
                    "fetched_at": datetime.now().isoformat()
                }

                # Validation
                if total_tons < 50000 or total_tons > 200000:
                    logger.warning(
                        f"Cambodia rubber exports {total_tons:.0f} tons outside expected range (100k-150k)"
                    )

                if avg_price_usd_ton < 1000 or avg_price_usd_ton > 3000:
                    logger.warning(
                        f"Cambodia rubber avg price {avg_price_usd_ton:.0f} USD/t outside expected range (1,500-2,000)"
                    )

                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"WITS HS6 download error for rubber: {e.response.status_code}")
                return self._empty_rubber_export_result(year)
            except Exception as e:
                logger.error(f"WITS rubber export fetch error: {e}", exc_info=True)
                return self._empty_rubber_export_result(year)

    def _empty_rubber_export_result(self, year: int) -> Dict[str, Any]:
        """Return empty result structure for rubber exports."""
        return {
            "year": year,
            "product": "4001",
            "product_description": "Natural rubber (latex form)",
            "total_export_tons": 0,
            "total_export_value_usd": 0,
            "avg_price_usd_ton": 0,
            "top_partners": {},
            "source": "WITS",
            "fetched_at": datetime.now().isoformat(),
            "error": "No data available"
        }

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
