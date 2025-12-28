"""Cache service using Supabase query_cache table.

Alternative to Redis for query caching.
"""
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class CacheService:
    """Query cache using Supabase."""

    def __init__(self, supabase: SupabaseService, ttl_hours: int = 24):
        """
        Initialize cache service.

        Args:
            supabase: SupabaseService instance
            ttl_hours: Time to live in hours (default: 24)
        """
        self.supabase = supabase
        self.ttl_hours = ttl_hours

        logger.info(f"CacheService initialized with TTL={ttl_hours}h")

    def _hash_query(self, query: str, commodity: Optional[str] = None) -> str:
        """
        Create hash of query for cache key.

        Args:
            query: Query text
            commodity: Optional commodity filter

        Returns:
            SHA-256 hash (64 chars)
        """
        cache_key = f"{query}_{commodity or 'all'}"
        return hashlib.sha256(cache_key.encode()).hexdigest()

    async def get(
        self,
        query: str,
        commodity: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query.

        Args:
            query: Query text
            commodity: Optional commodity filter

        Returns:
            Cached response dict or None if not found/expired
        """
        query_hash = self._hash_query(query, commodity)

        try:
            result = self.supabase.client.table("query_cache").select("*").eq(
                "query_hash", query_hash
            ).execute()

            if not result.data:
                logger.info(f"Cache MISS: {query[:50]}...")
                return None

            cache_entry = result.data[0]

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry['expires_at'].replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                logger.info(f"Cache EXPIRED: {query[:50]}...")
                # Clean up expired entry
                self.supabase.client.table("query_cache").delete().eq(
                    "id", cache_entry['id']
                ).execute()
                return None

            # Increment hit count
            self.supabase.client.table("query_cache").update({
                "hit_count": cache_entry['hit_count'] + 1
            }).eq("id", cache_entry['id']).execute()

            logger.info(f"Cache HIT: {query[:50]}... (hits: {cache_entry['hit_count'] + 1})")

            return {
                "response": cache_entry['response'],
                "context_used": cache_entry.get('context_used'),
                "citations": cache_entry.get('citations', []),
                "metadata": cache_entry.get('metadata', {}),
                "cached": True
            }

        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None

    async def set(
        self,
        query: str,
        response: str,
        context_used: Optional[str] = None,
        citations: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        commodity: Optional[str] = None
    ) -> bool:
        """
        Cache a query response.

        Args:
            query: Query text
            response: Response text
            context_used: Context chunks used
            citations: List of citations
            metadata: Additional metadata
            commodity: Optional commodity filter

        Returns:
            True if successful, False otherwise
        """
        query_hash = self._hash_query(query, commodity)
        expires_at = datetime.utcnow() + timedelta(hours=self.ttl_hours)

        try:
            self.supabase.client.table("query_cache").insert({
                "query_hash": query_hash,
                "query_text": query,
                "response": response,
                "context_used": context_used,
                "citations": citations or [],
                "metadata": metadata or {},
                "expires_at": expires_at.isoformat()
            }).execute()

            logger.info(f"Cache SET: {query[:50]}... (expires: {self.ttl_hours}h)")
            return True

        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False

    async def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Returns:
            Number of entries deleted
        """
        try:
            result = self.supabase.client.rpc("cleanup_expired_cache").execute()
            count = result.data if result.data else 0
            logger.info(f"Cleared {count} expired cache entries")
            return count

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        try:
            # Total entries
            result = self.supabase.client.table("query_cache").select("id", count="exact").execute()
            total_entries = result.count if hasattr(result, 'count') else len(result.data or [])

            # Expired entries
            now = datetime.utcnow().isoformat()
            result = self.supabase.client.table("query_cache").select("id", count="exact").lt(
                "expires_at", now
            ).execute()
            expired_entries = result.count if hasattr(result, 'count') else len(result.data or [])

            # Total hits
            result = self.supabase.client.table("query_cache").select("hit_count").execute()
            total_hits = sum(entry.get('hit_count', 0) for entry in (result.data or []))

            # Average hit count
            active_entries = total_entries - expired_entries
            avg_hits = total_hits / active_entries if active_entries > 0 else 0

            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "total_hits": total_hits,
                "avg_hits_per_entry": avg_hits,
                "ttl_hours": self.ttl_hours
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e)
            }
