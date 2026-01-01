"""Public commodity prices service - Static/Historical data."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PublicPricesService:
    """Service to provide public commodity price data."""

    # Static historical prices (USD/ton) - Real-world approximate values
    CASHEW_PRICE_BASIS = "kernel_fob_vietnam_w320"
    CASHEW_PRICE_TYPE = "kernel"
    CASHEW_PRICES = {
        # 2025 prices (approximate based on market reports)
        "2025-12-27": 8500,
        "2025-12-26": 8450,
        "2025-12-25": 8400,
        "2025-12-24": 8420,
        "2025-12-23": 8380,
        "2025-12-20": 8350,
        "2025-12-19": 8320,
        "2025-12-18": 8300,
        "2025-12-17": 8280,
        "2025-12-16": 8250,
        "2025-12-13": 8200,
        "2025-12-12": 8180,
        "2025-12-11": 8150,
        "2025-12-10": 8100,
        "2025-12-09": 8080,
        "2025-12-06": 8050,
        "2025-12-05": 8020,
        "2025-12-04": 8000,
        "2025-12-03": 7980,
        "2025-12-02": 7950,
        # November 2025
        "2025-11-29": 7920,
        "2025-11-28": 7900,
        "2025-11-27": 7880,
        "2025-11-26": 7850,
        "2025-11-25": 7820,
    }

    RUBBER_PRICES = {
        # 2025 prices (USD/ton) - Natural rubber prices
        "2025-12-27": 1798,
        "2025-12-26": 1785,
        "2025-12-25": 1770,
        "2025-12-24": 1775,
        "2025-12-23": 1760,
        "2025-12-20": 1750,
        "2025-12-19": 1740,
        "2025-12-18": 1730,
        "2025-12-17": 1720,
        "2025-12-16": 1710,
        "2025-12-13": 1700,
        "2025-12-12": 1690,
        "2025-12-11": 1680,
        "2025-12-10": 1670,
        "2025-12-09": 1660,
        "2025-12-06": 1650,
        "2025-12-05": 1640,
        "2025-12-04": 1630,
        "2025-12-03": 1620,
        "2025-12-02": 1610,
        # November 2025
        "2025-11-29": 1600,
        "2025-11-28": 1590,
        "2025-11-27": 1580,
        "2025-11-26": 1570,
        "2025-11-25": 1560,
    }

    def get_price_history(
        self,
        commodity: str,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """
        Get historical price data for a commodity.

        Args:
            commodity: Commodity name (cashew, rubber)
            days: Number of days of history

        Returns:
            List of price data dictionaries
        """
        commodity_lower = commodity.lower()

        # Select price source
        if commodity_lower == "cashew":
            prices_dict = self.CASHEW_PRICES
            price_basis = self.CASHEW_PRICE_BASIS
            price_type = self.CASHEW_PRICE_TYPE
        elif commodity_lower == "rubber":
            prices_dict = self.RUBBER_PRICES
            price_basis = "tsr20_spot"
            price_type = "raw_rubber"
        else:
            logger.warning(f"Unknown commodity: {commodity}")
            return []

        # Generate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        result = []
        for date_str, price in sorted(prices_dict.items(), reverse=True):
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if start_date <= date <= end_date:
                result.append({
                    "date": date_str,
                    "price_usd": price,
                    "commodity": commodity_lower,
                    "price_basis": price_basis,
                    "price_type": price_type,
                    "price_unit": "USD/ton"
                })

        logger.info(f"Retrieved {len(result)} price points for {commodity} ({days} days)")
        return result

    def get_latest_price(self, commodity: str) -> Optional[Dict[str, any]]:
        """
        Get the latest price for a commodity.

        Args:
            commodity: Commodity name

        Returns:
            Price data dictionary or None
        """
        history = self.get_price_history(commodity, days=1)
        return history[0] if history else None

    def get_price_statistics(
        self,
        commodity: str,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate price statistics.

        Args:
            commodity: Commodity name
            days: Number of days

        Returns:
            Statistics dictionary
        """
        history = self.get_price_history(commodity, days)

        if not history:
            return {
                "current": 0,
                "average": 0,
                "highest": 0,
                "lowest": 0,
                "change_pct": 0,
                "price_basis": None,
                "price_type": None,
                "price_unit": "USD/ton"
            }

        prices = [item["price_usd"] for item in history]

        current = prices[0]
        average = sum(prices) / len(prices)
        highest = max(prices)
        lowest = min(prices)

        # Calculate percentage change
        if len(prices) > 1:
            oldest = prices[-1]
            change_pct = ((current - oldest) / oldest) * 100
        else:
            change_pct = 0

        stats = {
            "current": current,
            "average": average,
            "highest": highest,
            "lowest": lowest,
            "change_pct": change_pct
        }
        if commodity.lower() == "cashew":
            stats["price_basis"] = self.CASHEW_PRICE_BASIS
            stats["price_type"] = self.CASHEW_PRICE_TYPE
            stats["price_unit"] = "USD/ton"
        elif commodity.lower() == "rubber":
            stats["price_basis"] = "tsr20_spot"
            stats["price_type"] = "raw_rubber"
            stats["price_unit"] = "USD/ton"

        return stats
