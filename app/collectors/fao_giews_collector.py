"""FAO GIEWS / FPMA CSV collector."""
import csv
import io
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class FAOGIEWSCollector(BaseCollector):
    """Collector for FAO GIEWS/FPMA CSV exports (monthly prices)."""

    def __init__(
        self,
        csv_urls: Optional[List[str]] = None,
        country_filter: Optional[str] = None,
        commodity_keywords: Optional[List[str]] = None,
        commodity: str = "cashew",
        price_tool_url: Optional[str] = None,
        api_base_url: Optional[str] = None,
        use_api: bool = True,
        periodicity: Optional[str] = "monthly",
        timeout: float = 30.0,
        max_rows: int = 10000
    ):
        super().__init__("FAO_GIEWS")
        self.commodity = commodity.lower()
        self.csv_urls = csv_urls or self._split_urls(settings.fao_giews_csv_urls)
        self.country_filter = (country_filter or settings.fao_giews_country_filter or "Cambodia").lower()

        # Set commodity keywords based on commodity type
        if commodity_keywords:
            self.commodity_keywords = commodity_keywords
        elif self.commodity == "rubber":
            self.commodity_keywords = ["rubber", "caoutchouc", "natural rubber"]
        else:
            self.commodity_keywords = ["cashew", "anacard", "anacardium"]

        self.price_tool_url = price_tool_url or settings.fao_giews_price_tool_url
        self.api_base_url = self._normalize_api_base_url(
            api_base_url or settings.fao_giews_api_base_url
        )
        self.use_api = use_api
        self.periodicity = periodicity
        self.timeout = timeout
        self.max_rows = max_rows

    async def collect(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            if self.use_api and self.api_base_url:
                try:
                    api_records = await self._collect_api(client)
                    records.extend(api_records)
                except Exception as exc:
                    logger.warning("FAO GIEWS FPMA API failed: %s", exc)

            csv_urls = list(self.csv_urls)
            if not csv_urls:
                csv_urls = await self._discover_csv_urls(client)

            if not csv_urls:
                logger.warning("FAO GIEWS: no CSV URLs configured or discovered")
                return records

            for url in csv_urls:
                try:
                    csv_text = await self._download_csv(client, url)
                    records.extend(self._parse_csv(csv_text, url))
                except Exception as exc:
                    logger.error("FAO GIEWS CSV error (%s): %s", url, exc)

        if records:
            records = self._dedupe_records(records)
        return records

    async def validate(self, data: Dict[str, Any]) -> bool:
        required_fields = ["commodity", "date", "price_usd", "source"]
        if not all(field in data for field in required_fields):
            return False
        if data["commodity"] not in ["cashew", "rubber"]:
            return False
        if not isinstance(data["price_usd"], (int, float)):
            return False
        return True

    async def _collect_api(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        commodity_ids = await self._fetch_fpma_commodity_ids(client)
        if not commodity_ids:
            logger.info("FAO GIEWS FPMA: no commodity matches for keywords %s", self.commodity_keywords)
            return []

        iso3 = self._normalize_country_code(self.country_filter)
        series = await self._fetch_fpma_series(client, commodity_ids, iso3)
        if not series:
            logger.info("FAO GIEWS FPMA: no series for country filter %s", self.country_filter)
            return []

        series_map = {item.get("uuid"): item for item in series if item.get("uuid")}
        uuids = list(series_map.keys())
        records: List[Dict[str, Any]] = []

        for start in range(0, len(uuids), 20):
            batch = uuids[start:start + 20]
            payload = await self._fetch_fpma_prices(client, batch)
            records.extend(self._parse_fpma_prices(payload, series_map))
            if len(records) >= self.max_rows:
                break

        return records[:self.max_rows]

    async def _fetch_fpma_commodity_ids(self, client: httpx.AsyncClient) -> List[int]:
        url = urljoin(self.api_base_url, "Commodity")
        items = await self._fetch_paginated(client, url)
        matches = []
        for item in items:
            if self._matches_fpma_commodity(item):
                commodity_id = item.get("id")
                if commodity_id:
                    matches.append(commodity_id)
        return matches

    async def _fetch_fpma_series(
        self,
        client: httpx.AsyncClient,
        commodity_ids: List[int],
        iso3: str
    ) -> List[Dict[str, Any]]:
        url = urljoin(self.api_base_url, "FpmaSerie")
        series: List[Dict[str, Any]] = []

        for commodity_id in commodity_ids:
            params: Dict[str, Any] = {"commodity": commodity_id, "page_size": 200}
            if iso3:
                params["iso3_country_code"] = iso3

            items = await self._fetch_paginated(client, url, params=params)
            for item in items:
                if iso3 and item.get("iso3_country_code") != iso3:
                    continue
                if not iso3 and self.country_filter:
                    country_name = str(item.get("country_name", "")).lower()
                    if self.country_filter not in country_name:
                        continue
                series.append(item)

        return series

    async def _fetch_fpma_prices(
        self,
        client: httpx.AsyncClient,
        uuids: List[str]
    ) -> Dict[str, Any]:
        url = urljoin(self.api_base_url, "FpmaSeriePrice")
        params: Dict[str, Any] = {"uuid__in": ",".join(uuids)}
        if self.periodicity:
            params["periodicity"] = self.periodicity

        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_fpma_prices(
        self,
        payload: Dict[str, Any],
        series_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        results = payload.get("results") or []

        for item in results:
            serie_uuid = item.get("uuid")
            serie = series_map.get(serie_uuid, {})
            datapoints = item.get("datapoints") or []

            for datapoint in datapoints:
                date_value = datapoint.get("date")
                price_usd = self._parse_number(datapoint.get("price_value_dollar"))
                price_local = self._parse_number(datapoint.get("price_value"))
                currency = serie.get("currency")

                if price_usd is None and currency == "USD":
                    price_usd = price_local
                if price_usd is None or not date_value:
                    continue

                metadata = {
                    "series_uuid": serie_uuid,
                    "country": serie.get("country_name"),
                    "iso3_country_code": serie.get("iso3_country_code"),
                    "market_name": serie.get("market_name"),
                    "market_type": serie.get("market_type"),
                    "price_type": serie.get("price_type"),
                    "currency": currency,
                    "measure_unit": serie.get("measure_unit_label"),
                    "source_name": serie.get("source_name"),
                    "source_url": serie.get("source_url"),
                    "periodicity": datapoint.get("periodicity"),
                    "price_value_local": price_local,
                    "price_value_dollar": price_usd
                }

                records.append({
                    "commodity": self.commodity,
                    "date": date_value,
                    "price_usd": float(price_usd),
                    "volume_tons": None,
                    "destination_country": None,
                    "source": "FAO_GIEWS",
                    "metadata": metadata
                })

        return records

    async def _fetch_paginated(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 20
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        next_url = url
        next_params = params
        page_count = 0

        while next_url and page_count < max_pages:
            response = await client.get(next_url, params=next_params)
            response.raise_for_status()
            payload = response.json()
            results.extend(payload.get("results") or [])
            next_url = payload.get("next")
            next_params = None
            page_count += 1

        return results

    async def _discover_csv_urls(self, client: httpx.AsyncClient) -> List[str]:
        if not self.price_tool_url:
            return []

        try:
            response = await client.get(self.price_tool_url)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("FAO GIEWS discovery failed: %s", exc)
            return []

        soup = BeautifulSoup(response.text, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if self._looks_like_csv(href):
                links.append(urljoin(self.price_tool_url, href))

        return list(dict.fromkeys(links))

    async def _download_csv(self, client: httpx.AsyncClient, url: str) -> str:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_csv(self, csv_text: str, source_url: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            return records

        column_map = self._build_column_map(reader.fieldnames)
        country_col = self._find_column(column_map, ["country", "area", "countryname"])
        product_col = self._find_column(column_map, ["product", "commodity", "item"])
        market_col = self._find_column(column_map, ["market", "location", "place"])
        price_col = self._find_column(column_map, ["price", "value", "wholesale", "farmgate"])
        unit_col = self._find_column(column_map, ["unit"])
        currency_col = self._find_column(column_map, ["currency"])
        date_col = self._find_column(column_map, ["date", "period", "time"])
        year_col = self._find_column(column_map, ["year"])
        month_col = self._find_column(column_map, ["month"])
        price_type_col = self._find_column(column_map, ["pricetype", "type"])

        rows_processed = 0
        for row in reader:
            rows_processed += 1
            if rows_processed > self.max_rows:
                break

            country_value = self._safe_lower(row.get(country_col))
            if country_value:
                if self.country_filter not in country_value:
                    continue
            else:
                if self.country_filter not in source_url.lower():
                    continue

            product_value = row.get(product_col, "") if product_col else ""
            if not self._matches_commodity(product_value, source_url):
                continue

            price_value = self._parse_number(row.get(price_col))
            if price_value is None:
                continue

            date_value = self._extract_date(row, date_col, year_col, month_col)
            if not date_value:
                continue

            unit_value = row.get(unit_col) if unit_col else ""
            currency_value = row.get(currency_col) if currency_col else ""
            currency, unit = self._parse_currency_unit(unit_value, currency_value)

            metadata = {
                "source_url": source_url,
                "country": row.get(country_col) if country_col else None,
                "product": product_value or None,
                "market": row.get(market_col) if market_col else None,
                "price_type": row.get(price_type_col) if price_type_col else None,
                "price_currency": currency or None,
                "price_unit": unit or unit_value or None
            }
            if currency and currency != "USD":
                metadata["price_local_value"] = float(price_value)
                metadata["price_value_note"] = "stored in original currency"

            records.append({
                "commodity": self.commodity,
                "date": date_value,
                "price_usd": float(price_value),
                "volume_tons": None,
                "destination_country": None,
                "source": "FAO_GIEWS",
                "metadata": metadata
            })

        return records

    def _extract_date(
        self,
        row: Dict[str, Any],
        date_col: Optional[str],
        year_col: Optional[str],
        month_col: Optional[str]
    ) -> Optional[str]:
        if date_col:
            parsed = self._parse_date(row.get(date_col))
            if parsed:
                return parsed

        year_value = self._parse_number(row.get(year_col)) if year_col else None
        month_value = row.get(month_col) if month_col else None

        if year_value:
            year = int(year_value)
            month = self._parse_month(month_value) if month_value else 1
            return f"{year:04d}-{month:02d}-01"

        return None

    def _parse_date(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None

        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%b-%Y", "%B %Y"):
            try:
                parsed = datetime.strptime(text, fmt)
                return parsed.strftime("%Y-%m-01")
            except ValueError:
                continue

        if re.match(r"^\d{4}$", text):
            return f"{text}-01-01"

        return None

    def _parse_month(self, value: Any) -> int:
        if value is None:
            return 1
        text = str(value).strip()
        if text.isdigit():
            month = int(text)
            return max(1, min(12, month))

        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        key = text[:3].lower()
        return month_map.get(key, 1)

    def _build_column_map(self, headers: List[str]) -> Dict[str, str]:
        mapping = {}
        for header in headers:
            normalized = re.sub(r"[^a-z0-9]", "", header.lower())
            mapping[normalized] = header
        return mapping

    def _find_column(self, column_map: Dict[str, str], candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            normalized = re.sub(r"[^a-z0-9]", "", candidate.lower())
            for key, header in column_map.items():
                if normalized in key:
                    return header
        return None

    def _matches_commodity(self, product_value: str, source_url: str) -> bool:
        text = f"{product_value} {source_url}".lower()
        return any(keyword in text for keyword in self.commodity_keywords)

    def _parse_currency_unit(self, unit_value: str, currency_value: str) -> tuple[str, str]:
        text = f"{unit_value} {currency_value}".upper()
        currency = ""
        if "USD" in text or "$" in text:
            currency = "USD"
        elif "KHR" in text or "RIEL" in text:
            currency = "KHR"

        unit = ""
        if "KG" in text:
            unit = "KG"
        elif "TON" in text or "TONNE" in text:
            unit = "TON"

        return currency, unit

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

    def _safe_lower(self, value: Any) -> str:
        return str(value).lower() if value is not None else ""

    def _looks_like_csv(self, href: str) -> bool:
        href_lower = href.lower()
        return ".csv" in href_lower or "format=csv" in href_lower

    def _split_urls(self, raw_value: str) -> List[str]:
        if not raw_value:
            return []
        return [item.strip() for item in raw_value.split(",") if item.strip()]

    def _matches_fpma_commodity(self, item: Dict[str, Any]) -> bool:
        text = f"{item.get('commodity_name', '')} {item.get('alternative_name', '')}".lower()
        return any(keyword in text for keyword in self.commodity_keywords)

    def _normalize_api_base_url(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return value.rstrip("/") + "/"

    def _normalize_country_code(self, value: str) -> str:
        if not value:
            return ""
        text = value.strip().upper()
        if len(text) == 3:
            return text
        if text.lower() == "cambodia":
            return "KHM"
        return ""

    def _dedupe_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for record in records:
            metadata = record.get("metadata") or {}
            key = (
                record.get("commodity"),
                record.get("date"),
                record.get("price_usd"),
                record.get("source"),
                metadata.get("source_url")
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(record)
        return deduped

    def estimate_cambodia_farmgate(
        self,
        thailand_price_usd_kg: float,
        usd_khr_rate: float = 4050.0
    ) -> Dict[str, Any]:
        """
        Estimate Cambodia farmgate price from Thailand data.

        Strategy:
        - Thailand data from FAO FPMA is used as proxy
        - Cambodia prices typically 10-15% lower (less processing)
        - Apply average discount of 12.5%

        Args:
            thailand_price_usd_kg: Thailand farmgate price in USD/kg
            usd_khr_rate: USD to KHR exchange rate

        Returns:
            {
                "estimated_price_usd_kg": 1.26,
                "estimated_price_khr_kg": 5100,
                "basis": "Thailand FAO FPMA -12.5%",
                "disclaimer": "Estimated from regional data"
            }
        """
        discount = 0.125  # Average -12.5%
        cambodia_usd_kg = thailand_price_usd_kg * (1 - discount)
        cambodia_khr_kg = cambodia_usd_kg * usd_khr_rate

        return {
            "estimated_price_usd_kg": round(cambodia_usd_kg, 2),
            "estimated_price_khr_kg": round(cambodia_khr_kg, 2),
            "basis": "Thailand FAO FPMA -12.5%",
            "disclaimer": "Estimated from regional data",
            "thailand_source_price_usd_kg": thailand_price_usd_kg,
            "usd_khr_rate": usd_khr_rate
        }

