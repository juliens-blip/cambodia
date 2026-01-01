"""Cambodia macro indicators service (MEF/NBC/CSX context)."""
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.services.csx_index_service import get_csx_index_service
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class CambodiaMacroService:
    """Fetch and format Cambodia macro indicators for analysis prompts."""

    def __init__(
        self,
        supabase: SupabaseService,
        mef_realtime_base: Optional[str] = None,
        timeout: float = 15.0
    ):
        self.supabase = supabase
        self.csx_service = get_csx_index_service(supabase.client)
        self.mef_realtime_base = (mef_realtime_base or settings.mef_realtime_api_url).rstrip("/")
        self.timeout = timeout

    async def build_macro_context(self, commodity: str) -> Dict[str, Any]:
        exchange_rate = await self._get_exchange_rate("USD")
        csx_summary = await self._get_csx_summary()
        csx_index = await self._get_csx_index()

        csx_summary_stats = self._summarize_csx_summary(csx_summary)
        csx_index = await self._with_csx_fallback(csx_index)

        fx_info = self._normalize_exchange_rate(exchange_rate)
        fx_trend = self._analyze_fx_trend(fx_info.get("change_pct"))
        fx_impact = self._interpret_fx_impact(commodity, fx_trend)

        csx_change_pct = self._parse_number((csx_index or {}).get("change_percent"))
        csx_sentiment = self._interpret_csx_sentiment(csx_change_pct)

        context_text = self._format_context(
            fx_info=fx_info,
            fx_trend=fx_trend,
            fx_impact=fx_impact,
            csx_summary=csx_summary_stats,
            csx_index=csx_index,
            csx_sentiment=csx_sentiment
        )

        return {
            "exchange_rate": fx_info,
            "csx_summary": csx_summary_stats,
            "csx_index": csx_index or {},
            "fx_trend": fx_trend,
            "fx_impact": fx_impact,
            "csx_sentiment": csx_sentiment,
            "context_text": context_text
        }

    async def build_macro_context_text(self, commodity: str) -> str:
        context = await self.build_macro_context(commodity)
        return context.get("context_text", "")

    async def _get_exchange_rate(self, currency_id: str = "USD") -> Optional[Dict[str, Any]]:
        data = await self._fetch_mef_json(f"exchange-rate?currency_id={currency_id}")
        return data.get("data") if data else None

    async def _get_csx_summary(self) -> list:
        data = await self._fetch_mef_json("csx-summary")
        return data.get("data", []) if data else []

    async def _get_csx_index(self) -> Optional[Dict[str, Any]]:
        data = await self._fetch_mef_json("csx-index")
        return data.get("data") if data else None

    async def _fetch_mef_json(self, path: str) -> Optional[Dict[str, Any]]:
        url = f"{self.mef_realtime_base}/{path}"
        last_error = None
        for verify in (True, False):
            try:
                async with httpx.AsyncClient(verify=verify, timeout=self.timeout) as client:
                    response = await client.get(url)
                if response.status_code == 200:
                    if not verify:
                        logger.warning("MEF SSL verification disabled for %s", path)
                    return response.json()
                logger.debug("MEF %s status %s", path, response.status_code)
                return None
            except httpx.TransportError as exc:
                last_error = exc
                if verify and "CERTIFICATE_VERIFY_FAILED" in str(exc):
                    logger.warning("MEF SSL verification failed for %s, retrying without verification.", path)
                    continue
                logger.debug("MEF %s error: %s", path, exc)
                return None
            except Exception as exc:
                logger.debug("MEF %s error: %s", path, exc)
                return None

        if last_error:
            logger.debug("MEF %s error: %s", path, last_error)
        return None

    async def _with_csx_fallback(self, csx_index: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if self._has_csx_data(csx_index):
            return csx_index

        try:
            latest = await self.csx_service.get_latest_csx_index()
            if latest:
                return {
                    "value": latest.value,
                    "change_percent": latest.change_percent,
                    "updated_at": latest.updated_at
                }
        except Exception as exc:
            logger.debug("CSX fallback error: %s", exc)

        return csx_index

    def _has_csx_data(self, csx_index: Optional[Dict[str, Any]]) -> bool:
        if not csx_index:
            return False
        value = self._parse_number(csx_index.get("value"))
        change = self._parse_number(csx_index.get("change_percent"))
        return value is not None or change is not None

    def _summarize_csx_summary(self, summary_rows: list) -> Dict[str, Any]:
        stats = {
            "count": 0,
            "up": 0,
            "down": 0,
            "flat": 0,
            "total_value": 0.0,
            "total_volume": 0.0
        }

        if not summary_rows:
            return stats

        for row in summary_rows:
            status = (row or {}).get("change_up_down")
            if status == "up":
                stats["up"] += 1
            elif status == "down":
                stats["down"] += 1
            else:
                stats["flat"] += 1

            value = self._parse_number((row or {}).get("value"))
            if value is not None:
                stats["total_value"] += value

            volume = self._parse_number((row or {}).get("volume"))
            if volume is not None:
                stats["total_volume"] += volume

            stats["count"] += 1

        return stats

    def _normalize_exchange_rate(self, exchange_rate: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not exchange_rate:
            return {}

        return {
            "average": self._parse_number(exchange_rate.get("average")),
            "bid": self._parse_number(exchange_rate.get("bid")),
            "ask": self._parse_number(exchange_rate.get("ask")),
            "valid_date": exchange_rate.get("valid_date") or exchange_rate.get("date"),
            "change_pct": self._extract_change_pct(exchange_rate)
        }

    def _extract_change_pct(self, exchange_rate: Dict[str, Any]) -> Optional[float]:
        for key in ("change_percent", "change_pct", "change", "pct_change", "chg_pct"):
            value = self._parse_number(exchange_rate.get(key))
            if value is not None:
                return value
        return None

    def _analyze_fx_trend(self, change_pct: Optional[float]) -> str:
        if change_pct is None:
            return "unknown"
        if change_pct > 0.1:
            return "weakening"
        if change_pct < -0.1:
            return "strengthening"
        return "stable"

    def _interpret_fx_impact(self, commodity: str, trend: str) -> str:
        label = f"{commodity} exports" if commodity else "exports"
        if trend == "weakening":
            return (
                f"KHR weaker supports {label} revenues but raises USD-priced input costs"
            )
        if trend == "strengthening":
            return (
                f"KHR stronger can pressure {label} margins but lowers USD input costs"
            )
        if trend == "stable":
            return f"Stable FX keeps {label} margins steady"
        return ""

    def _interpret_csx_sentiment(self, change_pct: Optional[float]) -> str:
        if change_pct is None:
            return ""
        if change_pct >= 1.0:
            return "positive risk sentiment"
        if change_pct <= -1.0:
            return "risk-off sentiment"
        return "neutral sentiment"

    def _format_context(
        self,
        fx_info: Dict[str, Any],
        fx_trend: str,
        fx_impact: str,
        csx_summary: Dict[str, Any],
        csx_index: Optional[Dict[str, Any]],
        csx_sentiment: str
    ) -> str:
        parts = []

        has_fx = any(
            fx_info.get(key) is not None
            for key in ("average", "bid", "ask")
        )
        if has_fx:
            avg = self._format_number(fx_info.get("average"))
            bid = self._format_number(fx_info.get("bid"))
            ask = self._format_number(fx_info.get("ask"))
            valid_date = fx_info.get("valid_date") or "N/A"
            parts.append(
                f"USD/KHR exchange rate: avg {avg}, bid {bid}, ask {ask} on {valid_date}."
            )

        if fx_trend == "weakening":
            parts.append("FX trend: KHR weakening.")
        elif fx_trend == "strengthening":
            parts.append("FX trend: KHR strengthening.")
        elif fx_trend == "stable":
            parts.append("FX trend: stable.")

        if fx_impact:
            parts.append(f"FX impact: {fx_impact}.")

        if csx_summary.get("count", 0) > 0:
            up = csx_summary.get("up", 0)
            down = csx_summary.get("down", 0)
            flat = csx_summary.get("flat", 0)
            total_value = self._format_number(csx_summary.get("total_value"))
            total_volume = self._format_number(csx_summary.get("total_volume"))
            parts.append(
                "CSX summary: "
                f"{up} up, {down} down, {flat} flat; "
                f"total value {total_value} KHR; total volume {total_volume}."
            )

        if csx_index:
            index_value = self._parse_number(csx_index.get("value"))
            change_pct = self._parse_number(csx_index.get("change_percent"))
            if index_value is not None or change_pct is not None:
                value_text = self._format_number(index_value, decimals=2)
                change_text = f"{change_pct:+.2f}%" if change_pct is not None else "N/A"
                parts.append(f"CSX index: {value_text} (change {change_text}).")

        if csx_sentiment:
            parts.append(f"CSX sentiment: {csx_sentiment}.")

        return "\n".join(parts).strip()

    def _parse_number(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace(",", "")
        try:
            return float(text)
        except ValueError:
            return None

    def _format_number(self, value: Optional[float], decimals: int = 0) -> str:
        if value is None:
            return "N/A"
        if decimals == 0:
            return f"{value:,.0f}"
        return f"{value:,.{decimals}f}"
