"""Rate limiting for bot operations."""

import time
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(
        self,
        max_requests_per_minute: int = 10,
        max_requests_per_hour: int = 100,
        max_requests_per_day: int = 500,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_minute: Maximum requests per minute per user/chat
            max_requests_per_hour: Maximum requests per hour per user/chat
            max_requests_per_day: Maximum requests per day per user/chat
        """
        self.max_per_minute = max_requests_per_minute
        self.max_per_hour = max_requests_per_hour
        self.max_per_day = max_requests_per_day

        # Store request timestamps: {identifier: [timestamps]}
        self.requests: Dict[str, list] = defaultdict(list)

    def _cleanup_old_requests(self, identifier: str, cutoff_time: float):
        """Remove old request timestamps."""
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff_time
        ]

    def is_allowed(self, identifier: str) -> Tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.

        Args:
            identifier: Unique identifier (user_id or chat_id)

        Returns:
            Tuple of (is_allowed, reason)
        """
        now = time.time()
        requests = self.requests[identifier]

        # Cleanup old requests (older than 24 hours)
        self._cleanup_old_requests(identifier, now - 86400)

        # Check per-minute limit
        minute_ago = now - 60
        recent_minute = [ts for ts in requests if ts > minute_ago]
        if len(recent_minute) >= self.max_per_minute:
            return False, "Rate limit exceeded: too many requests per minute"

        # Check per-hour limit
        hour_ago = now - 3600
        recent_hour = [ts for ts in requests if ts > hour_ago]
        if len(recent_hour) >= self.max_per_hour:
            return False, "Rate limit exceeded: too many requests per hour"

        # Check per-day limit
        day_ago = now - 86400
        recent_day = [ts for ts in requests if ts > day_ago]
        if len(recent_day) >= self.max_per_day:
            return False, "Rate limit exceeded: too many requests per day"

        # Record this request
        requests.append(now)

        return True, "OK"

    def record_request(self, identifier: str):
        """
        Record a request (alternative to is_allowed for explicit recording).

        Args:
            identifier: Unique identifier
        """
        self.requests[identifier].append(time.time())

    def get_stats(self, identifier: str) -> dict:
        """
        Get rate limit statistics for an identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with statistics
        """
        now = time.time()
        requests = self.requests[identifier]

        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400

        return {
            "requests_last_minute": len([ts for ts in requests if ts > minute_ago]),
            "requests_last_hour": len([ts for ts in requests if ts > hour_ago]),
            "requests_last_day": len([ts for ts in requests if ts > day_ago]),
            "max_per_minute": self.max_per_minute,
            "max_per_hour": self.max_per_hour,
            "max_per_day": self.max_per_day,
        }

    def reset(self, identifier: str = None):
        """
        Reset rate limit for an identifier or all identifiers.

        Args:
            identifier: Optional identifier to reset, or None to reset all
        """
        if identifier:
            self.requests.pop(identifier, None)
        else:
            self.requests.clear()

