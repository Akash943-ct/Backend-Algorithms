"""Algorithm 13: LRU Cache.

LRU means Least Recently Used.
The cache records which item was accessed most recently.
A lookup moves its item to the newest position.
When full, the oldest position is evicted.
This is useful when recent access predicts future access.
"""

# Technical Example:
# cache = LRUCache(2); cache.put("a", 1); cache.put("b", 2)
# cache.get("a"); cache.put("c", 3)
# Output: cache.get("b") returns None because "b" was least recent.

# Easy Example:
# A small desk keeps only two books and removes the book untouched longest.
# Read book A, read book B, read A again, then add book C.
# Book B is removed because it was used least recently.

from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


class LRUCache(Generic[T]):
    """Evict the least recently used value when capacity is exceeded."""

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

__all__ = ["LRUCache"]
