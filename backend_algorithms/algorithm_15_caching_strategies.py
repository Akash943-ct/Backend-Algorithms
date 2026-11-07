"""Algorithm 15: Caching Strategies.

Cache-aside reads the cache first and fills it after a miss.
Read-through lets the cache layer load missing data.
Write-through updates cache and database together.
Write-back is faster but risks losing unflushed data.
Write-around skips cache writes for rarely read data.
"""

# Technical Example:
# value = cache.get("user:42")
# if value is None: value = database.load("user:42"); cache.put("user:42", value)
# Output: the first call loads the database; later calls read the cache.
# This is the cache-aside strategy.

# Easy Example:
# Keep frequently used recipe cards on the kitchen table.
# Look on the table first; if the card is missing, fetch it from the cupboard.
# The first lookup visits the cupboard; later lookups use the table.

from collections import OrderedDict
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class LRUCache(Generic[T]):
    """A small cache-aside building block using least-recent eviction."""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items: OrderedDict[str, T] = OrderedDict()

    def get(self, key: str, default: T | None = None) -> T | None:
        if key not in self._items:
            return default
        self._items.move_to_end(key)
        return self._items[key]

    def put(self, key: str, value: T) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)


@dataclass
class _Entry(Generic[T]):
    value: T
    expires: float


class TTLCache(Generic[T]):
    """Add expiration to cached values so stale data is bounded."""

    def __init__(self, clock=time.monotonic):
        self.clock, self._items = clock, {}

    def put(self, key: str, value: T, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._items[key] = _Entry(value, self.clock() + ttl)

    def get(self, key: str, default: T | None = None) -> T | None:
        entry = self._items.get(key)
        if entry is None or entry.expires <= self.clock():
            self._items.pop(key, None)
            return default
        return entry.value

__all__ = ["LRUCache", "TTLCache"]
