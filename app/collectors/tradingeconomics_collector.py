"""TradingEconomics commodity price collector (scraping/API)."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TradingEconomicsCollector(BaseCollector):
    """
    Collector for TradingEconomics commodity prices.

    Supports:
    - Web scraping (free, no API key)
    - API free tier (500 requests/month, requires key)

    Data sources:
    - Rubber: https://tradingeconomics.com/commodity/rubber
    """

    BASE_URL = "https://tradingeconomics.com/commodity"
    API_URL = "https://api.tradingeconomics.com"

    def __init__(
        self,
        commodity: str = "rubber",
        use_api: bool = False,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        super().__init__("TradingEconomics")
        self.commodity = commodity.lower()
        self.use_api = use_api
        self.api_key = api_key or settings.tradingeconomics_api_key if hasattr(settings, 'tradingeconomics_api_key') else None
        self.timeout = timeout

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect commodity price data.

        Returns:
            [{
                "commodity": "rubber",
                "date": "2026-01-01",
                "price_usd_per_unit": 1825,  # USD/ton
                "price_cents_per_kg": 182.5,
                "change_percent_day": -1.2,
                "source": "TradingEconomics",
                "metadata": {...}
            }]
        """
        records = []

        try:
            if self.use_api and self.api_key:
                price_data = await self._fetch_via_api()
            else:
                price_data = await self._fetch_via_scraping()

            if price_data:
                records.append(price_data)
        except Exception as e:
            logger.error(f"TradingEconomics collection failed: {e}", exc_info=True)

        return records

    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate price data."""
        required_fields = ["commodity", "date", "price_usd_per_unit", "source"]
        if not all(field in data for field in required_fields):
            return False

        # Validate price ranges
        if self.commodity == "rubber":
            price_cents_kg = data.get("price_cents_per_kg", 0)
            if not (150 <= price_cents_kg <= 220):
                logger.warning(f"Rubber price {price_cents_kg} cents/kg outside expected range 150-220")

        return True

    async def _fetch_via_scraping(self) -> Optional[Dict[str, Any]]:
        """
        Scrape commodity page HTML.

        Extracts:
        - Current price (cents/kg)
        - Daily change %
        - Last updated timestamp
        """
        url = f"{self.BASE_URL}/{self.commodity}"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract price (adjust selectors based on actual HTML structure)
                # Common patterns: .price-value, #p, .last-price, etc.
                price_elem = soup.select_one('.te-price, #p, .last-price, [id*="price"]')
                if not price_elem:
                    logger.warning(f"TradingEconomics: Could not find price element for {self.commodity}")
                    return None

                price_text = price_elem.text.strip()
                price_cents_kg = float(price_text.replace(',', ''))

                # Extract change %
                change_elem = soup.select_one('.te-change, .change, [class*="change"]')
                change_pct = 0.0
                if change_elem:
                    change_text = change_elem.text.strip().replace('%', '').replace('+', '')
                    try:
                        change_pct = float(change_text)
                    except ValueError:
                        pass

                # Convert cents/kg to USD/ton
                price_usd_ton = price_cents_kg * 10

                return {
                    "commodity": self.commodity,
                    "date": datetime.now().date().isoformat(),
                    "price_usd_per_unit": price_usd_ton,
                    "price_cents_per_kg": price_cents_kg,
                    "change_percent_day": change_pct,
                    "source": "TradingEconomics",
                    "metadata": {
                        "method": "scraping",
                        "url": url,
                        "scraped_at": datetime.now().isoformat()
                    }
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"TradingEconomics HTTP error: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"TradingEconomics scraping error: {e}")
                return None

    async def _fetch_via_api(self) -> Optional[Dict[str, Any]]:
        """
        Fetch via TradingEconomics API (free tier: 500 req/month).

        API endpoint: GET /markets/commodity/{symbol}
        Requires: ?c=guest:{api_key}
        """
        if not self.api_key:
            logger.warning("TradingEconomics API key not configured, falling back to scraping")
            return await self._fetch_via_scraping()

        # Map commodity to TradingEconomics symbol
        symbol_map = {
            "rubber": "RUBBER",
            "cashew": "CASHEW"  # If available
        }
        symbol = symbol_map.get(self.commodity, self.commodity.upper())

        url = f"{self.API_URL}/markets/commodity/{symbol}"
        params = {"c": f"guest:{self.api_key}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                # Parse API response (adjust based on actual API structure)
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                elif isinstance(data, dict):
                    item = data
                else:
                    logger.warning(f"Unexpected API response format: {data}")
                    return None

                price = item.get("Last", item.get("Price", 0))
                change_pct = item.get("DailyChange", item.get("Change", 0))

                # Assume API returns price in cents/kg for rubber
                price_usd_ton = price * 10

                return {
                    "commodity": self.commodity,
                    "date": datetime.now().date().isoformat(),
                    "price_usd_per_unit": price_usd_ton,
                    "price_cents_per_kg": price,
                    "change_percent_day": change_pct,
                    "source": "TradingEconomics API",
                    "metadata": {
                        "method": "api",
                        "symbol": symbol,
                        "fetched_at": datetime.now().isoformat()
                    }
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"TradingEconomics API error: {e.response.status_code}, falling back to scraping")
                return await self._fetch_via_scraping()
            except Exception as e:
                logger.error(f"TradingEconomics API error: {e}, falling back to scraping")
                return await self._fetch_via_scraping()

    async def fetch_history_30d(self) -> List[Dict[str, Any]]:
        """
        Fetch 30-day historical prices.

        Note: Historical data may require premium API access.
        Scraping historical data is more complex (requires parsing charts).

        For now, returns empty list (to be implemented if needed).
        """
        logger.info("fetch_history_30d() not implemented yet (requires premium API or chart scraping)")
        return []
