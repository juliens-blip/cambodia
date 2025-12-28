"""Rate limiting middleware for budget protection."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """3-tier rate limiting: hourly, daily, monthly."""

    def __init__(
        self,
        hourly_limit: int = 50,
        daily_limit: int = 500,
        monthly_limit: int = 5000
    ):
        """
        Initialize rate limiter.

        Args:
            hourly_limit: Max queries per hour per session
            daily_limit: Max queries per day total
            monthly_limit: Max queries per month total
        """
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit

        # In-memory storage (use Redis in production)
        self.hourly_counters: Dict[str, Tuple[datetime, int]] = {}
        self.daily_counter = (datetime.now().date(), 0)
        self.monthly_counter = (datetime.now().replace(day=1).date(), 0)

    def check_limits(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if request is within limits.

        Args:
            session_id: User session identifier

        Returns:
            (allowed, reason) tuple
        """
        now = datetime.now()

        # Check monthly limit
        if now.replace(day=1).date() > self.monthly_counter[0]:
            # New month, reset counter
            self.monthly_counter = (now.replace(day=1).date(), 0)

        if self.monthly_counter[1] >= self.monthly_limit:
            return False, f"Monthly limit exceeded ({self.monthly_limit} queries/month)"

        # Check daily limit
        if now.date() > self.daily_counter[0]:
            # New day, reset counter
            self.daily_counter = (now.date(), 0)

        if self.daily_counter[1] >= self.daily_limit:
            return False, f"Daily limit exceeded ({self.daily_limit} queries/day)"

        # Check hourly limit per session
        if session_id in self.hourly_counters:
            last_reset, count = self.hourly_counters[session_id]
            if now - last_reset > timedelta(hours=1):
                # Reset hourly counter
                self.hourly_counters[session_id] = (now, 0)
                count = 0

            if count >= self.hourly_limit:
                return False, f"Hourly limit exceeded ({self.hourly_limit} queries/hour)"
        else:
            self.hourly_counters[session_id] = (now, 0)

        return True, "OK"

    def increment(self, session_id: str):
        """Increment all counters."""
        now = datetime.now()

        # Increment hourly
        if session_id in self.hourly_counters:
            last_reset, count = self.hourly_counters[session_id]
            self.hourly_counters[session_id] = (last_reset, count + 1)
        else:
            self.hourly_counters[session_id] = (now, 1)

        # Increment daily
        self.daily_counter = (self.daily_counter[0], self.daily_counter[1] + 1)

        # Increment monthly
        self.monthly_counter = (self.monthly_counter[0], self.monthly_counter[1] + 1)

        logger.info(f"Rate limit incremented for {session_id}: "
                   f"hourly={self.hourly_counters[session_id][1]}/{self.hourly_limit}, "
                   f"daily={self.daily_counter[1]}/{self.daily_limit}, "
                   f"monthly={self.monthly_counter[1]}/{self.monthly_limit}")

    def get_stats(self) -> Dict[str, int]:
        """Get current usage statistics."""
        return {
            "hourly_sessions": len(self.hourly_counters),
            "daily_queries": self.daily_counter[1],
            "daily_limit": self.daily_limit,
            "monthly_queries": self.monthly_counter[1],
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": self.monthly_limit - self.monthly_counter[1]
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""

        # Skip rate limiting for:
        # 1. Health check and docs
        # 2. All GET requests (read-only, no cost)
        # 3. Stats endpoint
        exempt_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/", "/stats"]

        if request.url.path in exempt_paths or request.method == "GET":
            return await call_next(request)

        # Only rate limit POST endpoints that cost money:
        # - /api/v1/rag/query ($0.005)
        # - /api/v1/trends/analyze/* ($0.005)
        # Note: /api/v1/search is free, but we still rate limit for abuse protection

        # Get session ID from headers or IP
        session_id = request.headers.get("X-Session-ID", request.client.host)

        # Check limits
        allowed, reason = self.rate_limiter.check_limits(session_id)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {session_id}: {reason}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "reason": reason,
                    "stats": self.rate_limiter.get_stats()
                }
            )

        # Increment counter
        self.rate_limiter.increment(session_id)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        stats = self.rate_limiter.get_stats()
        response.headers["X-RateLimit-Monthly-Limit"] = str(stats["monthly_limit"])
        response.headers["X-RateLimit-Monthly-Remaining"] = str(stats["monthly_remaining"])

        return response
