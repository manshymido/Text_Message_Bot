"""Simple in-memory cache for API responses."""

import time
from typing import Any, Optional, TypeVar

T = TypeVar("T")


class CacheEntry:
    """Cache entry with expiration."""

    def __init__(self, value: Any, ttl: float):
        """
        Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.expires_at = time.time() + ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return time.time() > self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, default_ttl: float = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time to live in seconds (5 minutes)
        """
        self.cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        entry = self.cache.get(key)
        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        self.cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }

