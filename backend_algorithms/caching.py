"""Cache and probabilistic data structures."""

from collections import OrderedDict
import hashlib
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


# ALGORITHM 13: LRU (Least Recently Used) Cache
# LRU keeps recently accessed values near the front of an ordered collection.
# A dictionary provides fast lookup by key.
# Reading or writing an item marks it as recently used.
# When the cache is full, the oldest unused item is removed.
# This works well when recently used data is likely to be used again.
class LRUCache(Generic[T]):
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


# ALGORITHM 14: TTL (Time To Live) Cache Eviction
# TTL gives every cached value an expiration time.
# The expiration is calculated when the value is stored.
# A lookup compares the expiration time with the current clock.
# Expired values are removed and treated as cache misses.
# TTL prevents cached data from remaining stale forever.
class TTLCache(Generic[T]):
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


# ALGORITHM 14: LFU (Least Frequently Used) Cache
# LFU counts how often each cached value is accessed.
# A frequently used value receives a higher frequency score.
# When the cache is full, the lowest-frequency value is evicted.
# A tick breaks ties between values with the same frequency.
# LFU preserves consistently popular values better than simple recency.
class LFUCache(Generic[T]):
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items: dict[str, tuple[T, int, int]] = {}
        self._tick = 0

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


# ALGORITHM 16: Single-Flight Cache Stampede Prevention
# A cache stampede happens when many callers rebuild one missing hot key.
# Single-flight stores the result of the first loader call.
# Later callers reuse that stored result instead of repeating the work.
# This example demonstrates the coordination idea for one process.
# A production version needs locks or distributed coordination for many servers.
class SingleFlight(Generic[T]):
    """Coalesce concurrent cache rebuilds; callers share the first result."""

    def __init__(self):
        self._values: dict[str, T] = {}

    def get_or_set(self, key: str, loader) -> T:
        if key not in self._values:
            self._values[key] = loader()
        return self._values[key]


# ALGORITHM 19: Bloom Filter
# A Bloom filter stores membership hints in a compact bit array.
# Adding a value sets several bit positions selected by hash calculations.
# Checking a value tests whether all of those positions are set.
# A missing bit proves the value was never added.
# Set bits can still cause false positives, but never false negatives.
class BloomFilter:
    def __init__(self, size: int, hashes: int = 3):
        if size <= 0 or hashes <= 0:
            raise ValueError("size and hashes must be positive")
        self.size, self.hashes = size, hashes
        self._bits = bytearray((size + 7) // 8)

    def _positions(self, value: str):
        digest = hashlib.sha256(value.encode()).digest()
        for index in range(self.hashes):
            yield int.from_bytes(digest[index * 4:index * 4 + 4], "big") % self.size

    def add(self, value: str) -> None:
        for position in self._positions(value):
            self._bits[position // 8] |= 1 << (position % 8)

    def might_contain(self, value: str) -> bool:
        return all(self._bits[p // 8] & (1 << (p % 8)) for p in self._positions(value))
