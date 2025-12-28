"""Budget tracking and alerting service."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class BudgetService:
    """Budget tracking and alerting."""

    def __init__(
        self,
        supabase: SupabaseService,
        monthly_budget_usd: float = 5.0,
        rag_cost_per_query: float = 0.005
    ):
        """
        Initialize budget service.

        Args:
            supabase: SupabaseService instance
            monthly_budget_usd: Monthly budget limit in USD
            rag_cost_per_query: Cost per RAG query in USD
        """
        self.supabase = supabase
        self.monthly_budget = monthly_budget_usd
        self.rag_cost = rag_cost_per_query

        logger.info(f"BudgetService initialized: ${monthly_budget_usd}/month, ${rag_cost_per_query}/query")

    async def log_query(
        self,
        session_id: str,
        endpoint: str,
        query_type: str,
        cost_usd: float = 0.0,
        cached: bool = False,
        status: str = "success",
        error_message: Optional[str] = None,
        execution_time_ms: float = 0.0
    ) -> bool:
        """
        Log a query to usage_logs table.

        Args:
            session_id: Session identifier
            endpoint: API endpoint called
            query_type: Type of query (search, rag, history, stats)
            cost_usd: Cost in USD
            cached: Whether response was cached
            status: Query status (success, error, rate_limited)
            error_message: Error message if failed
            execution_time_ms: Execution time in milliseconds

        Returns:
            True if logged successfully
        """
        try:
            self.supabase.client.table("usage_logs").insert({
                "session_id": session_id,
                "endpoint": endpoint,
                "query_type": query_type,
                "cost_usd": cost_usd,
                "cached": cached,
                "status": status,
                "error_message": error_message,
                "execution_time_ms": execution_time_ms
            }).execute()

            logger.info(
                f"Usage logged: {query_type} ${cost_usd:.4f} "
                f"(cached={cached}, status={status})"
            )
            return True

        except Exception as e:
            logger.error(f"Error logging usage: {e}")
            return False

    async def get_current_month_stats(self) -> Dict[str, Any]:
        """
        Get current month budget statistics.

        Returns:
            Dict with budget stats
        """
        try:
            result = self.supabase.client.rpc("get_current_month_budget").execute()

            if result.data:
                stats = result.data[0]
                return {
                    "month": stats['month'],
                    "total_queries": stats['total_queries'],
                    "rag_queries": stats['rag_queries'],
                    "total_cost_usd": float(stats['total_cost_usd']),
                    "budget_limit_usd": float(stats['budget_limit_usd']),
                    "budget_remaining_usd": float(stats['budget_remaining_usd']),
                    "budget_utilization_pct": float(stats['budget_utilization_pct'])
                }
            else:
                # No data yet this month
                return {
                    "month": datetime.now().date().replace(day=1),
                    "total_queries": 0,
                    "rag_queries": 0,
                    "total_cost_usd": 0.0,
                    "budget_limit_usd": self.monthly_budget,
                    "budget_remaining_usd": self.monthly_budget,
                    "budget_utilization_pct": 0.0
                }

        except Exception as e:
            logger.error(f"Error getting budget stats: {e}")
            return {
                "error": str(e)
            }

    async def check_budget_alert(self) -> Optional[str]:
        """
        Check if budget alert should be triggered.

        Returns:
            Alert message if threshold exceeded, None otherwise
        """
        stats = await self.get_current_month_stats()

        if "error" in stats:
            return None

        utilization = stats['budget_utilization_pct']

        if utilization >= 95:
            return f"🚨 CRITICAL: 95% budget used (${stats['total_cost_usd']:.2f}/${stats['budget_limit_usd']:.2f})"
        elif utilization >= 90:
            return f"⚠️ WARNING: 90% budget used (${stats['total_cost_usd']:.2f}/${stats['budget_limit_usd']:.2f})"
        elif utilization >= 80:
            return f"⚠️ NOTICE: 80% budget used (${stats['total_cost_usd']:.2f}/${stats['budget_limit_usd']:.2f})"
        elif utilization >= 50:
            return f"ℹ️ INFO: 50% budget used (${stats['total_cost_usd']:.2f}/${stats['budget_limit_usd']:.2f})"

        return None

    async def can_execute_rag_query(self) -> tuple[bool, str]:
        """
        Check if RAG query can be executed within budget.

        Returns:
            (allowed, reason) tuple
        """
        stats = await self.get_current_month_stats()

        if "error" in stats:
            return True, "OK (cannot verify budget)"

        remaining = stats['budget_remaining_usd']

        if remaining < self.rag_cost:
            return False, f"Budget exceeded (${remaining:.2f} remaining, ${self.rag_cost:.2f} needed)"

        return True, "OK"

    def get_cache_savings(self, cache_hits: int, cache_misses: int) -> Dict[str, Any]:
        """
        Calculate cost savings from caching.

        Args:
            cache_hits: Number of cache hits
            cache_misses: Number of cache misses

        Returns:
            Dict with savings analysis
        """
        total_queries = cache_hits + cache_misses
        cache_hit_rate = cache_hits / total_queries if total_queries > 0 else 0

        # Cost without caching
        cost_without_cache = total_queries * self.rag_cost

        # Actual cost (only cache misses charged)
        actual_cost = cache_misses * self.rag_cost

        # Savings
        savings = cost_without_cache - actual_cost
        savings_pct = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0

        return {
            "total_queries": total_queries,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate_pct": cache_hit_rate * 100,
            "cost_without_cache_usd": cost_without_cache,
            "actual_cost_usd": actual_cost,
            "savings_usd": savings,
            "savings_pct": savings_pct
        }
