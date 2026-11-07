"""Algorithm 14: LFU and TTL Cache Eviction.

LFU means Least Frequently Used and counts accesses.
It evicts the item with the smallest usage count.
TTL gives an item a deadline independent of access frequency.
TTL prevents stale values from living forever.
Together they address popularity and freshness.
"""

# Technical Example:
# lfu = LFUCache(2); lfu.put("hot", "A"); lfu.get("hot")
# lfu.put("cold", "B"); lfu.put("new", "C")
# Output: lfu.get("hot") returns "A"; the less-used "cold" is evicted.
# TTLCache stores a value such as ("session", "active", ttl=30) until expiry.

# Easy Example:
# A shelf removes the book read the fewest times, while a lunch ticket expires at noon.
# Read one book often and leave another unread; wait until the ticket's time ends.
# The unread book is removed, and the expired ticket is no longer accepted.

import time
from typing import Generic, TypeVar
from dataclasses import dataclass

T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires: float


class TTLCache(Generic[T]):
    """Expire cached values after their configured time-to-live."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._items: dict[str, _Entry[T]] = {}

    def put(self, key: str, value: T, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._items[key] = _Entry(value, self.clock() + ttl)

    def get(self, key: str, default: T | None = None) -> T | None:
        entry = self._items.get(key)
        if entry is None:
            return default
        if entry.expires <= self.clock():
            del self._items[key]
            return default
        return entry.value


class LFUCache(Generic[T]):
    """Evict the least frequently accessed cached value."""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity, self._tick = capacity, 0
        self._items: dict[str, tuple[T, int, int]] = {}

    def get(self, key: str, default: T | None = None) -> T | None:
        item = self._items.get(key)
        if item is None:
            return default
        value, frequency, _ = item
        self._tick += 1
        self._items[key] = (value, frequency + 1, self._tick)
        return value

    def put(self, key: str, value: T) -> None:
        self._tick += 1
        frequency = self._items.get(key, (value, 0, 0))[1] + 1
        self._items[key] = (value, frequency, self._tick)
        if len(self._items) > self.capacity:
            victim = min(self._items, key=lambda item: (self._items[item][1], self._items[item][2]))
            del self._items[victim]

__all__ = ["LFUCache", "TTLCache"]
