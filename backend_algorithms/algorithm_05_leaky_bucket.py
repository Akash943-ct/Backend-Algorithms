"""Algorithm 05: Leaky Bucket.

Requests enter a bounded queue.
The queue drains at a constant configured rate.
This smooths bursts before work reaches a dependency.
Requests are rejected when the queue is full.
It trades burst tolerance for predictable output.
"""

# Technical Example:
# bucket = LeakyBucket(capacity=2, drain_rate=1)
# Two immediate enqueues return True.
# A third immediate enqueue returns False because the queue is full.

# Easy Example:
# Two dishes fit on a serving tray, and a waiter carries away one dish each minute.
# Put three dishes on the tray at the same time.
# Two dishes fit; the third dish stays off the tray.

import time
from collections import deque
from typing import Callable


class LeakyBucket:
    """Queue requests and release them at a constant rate."""

    def __init__(self, capacity: int, drain_rate: float, clock: Callable[[], float] = time.monotonic):
        if capacity <= 0 or drain_rate <= 0:
            raise ValueError("capacity and drain_rate must be positive")
        self.capacity, self.rate, self.clock = capacity, drain_rate, clock
        self._queues: dict[str, deque[object]] = {}
        self._last: dict[str, float] = {}

    def _drain(self, key: str, now: float) -> None:
        queue = self._queues.setdefault(key, deque())
        elapsed = max(0, now - self._last.get(key, now))
        for _ in range(min(len(queue), int(elapsed * self.rate))):
            queue.popleft()
        self._last[key] = now

    def enqueue(self, key: str, item: object) -> bool:
        now = self.clock()
        self._drain(key, now)
        queue = self._queues[key]
        if len(queue) >= self.capacity:
            return False
        queue.append(item)
        return True

    def drain(self, key: str) -> list[object]:
        now = self.clock()
        self._drain(key, now)
        return list(self._queues.setdefault(key, deque()))

__all__ = ["LeakyBucket"]
