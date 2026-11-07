"""In-memory rate limiting algorithms. Use an atomic shared store in production."""

from collections import deque
from dataclasses import dataclass
import time
from typing import Callable


# SUPPORTING UTILITY: Rate-Limit Response Headers
def rate_limit_headers(limit: int, remaining: int, reset_at: int) -> dict[str, str]:
    """Build the metadata clients need after a rate-limit decision."""
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset_at),
    }


# ALGORITHM 1: Fixed Window Counter
# This algorithm divides time into separate, fixed-size windows.
# Each user gets a counter for the current window.
# A request increases that counter by one.
# Requests are accepted while the counter is within the limit.
# The counter resets automatically when the next window begins.
class FixedWindowLimiter:
    """Count requests independently inside each fixed-duration time window."""

    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit, self.window = limit, window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[int, int]] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        # Every key gets a counter such as (window number, requests in window).
        window_id = int(now // self.window)
        old_id, count = self._windows.get(key, (window_id, 0))
        count = count + 1 if old_id == window_id else 1
        self._windows[key] = (window_id, count)
        return count <= self.limit


# ALGORITHM 2: Sliding Window Log
# This algorithm stores the time of every accepted request.
# For each new request, old timestamps leave the rolling time window.
# The remaining timestamps represent recent traffic for this user.
# The request is rejected when that list already reaches the limit.
# It is accurate, but storing every timestamp uses more memory.
class SlidingWindowLog:
    """Keep each request timestamp for precise sliding-window decisions."""

    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit, self.window, self.clock = limit, window_seconds, clock
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        events = self._events.setdefault(key, deque())
        # Discard timestamps that are no longer inside the rolling window.
        while events and events[0] <= now - self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


# ALGORITHM 3: Sliding Window Counter
# This algorithm keeps counts for the current and previous windows.
# It estimates how many previous-window requests are still relevant.
# Requests near the end of the previous window receive less weight.
# The estimate uses less memory than storing every request timestamp.
# It is faster and cheaper, but it is an approximation.
class SlidingWindowCounter:
    """Approximate a sliding window using current and previous counters."""

    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit, self.window, self.clock = limit, window_seconds, clock
        self._windows: dict[str, tuple[int, int, int]] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        current = int(now // self.window)
        previous, current_count, previous_count = self._windows.get(key, (current, 0, 0))
        if current != previous:
            # The old current window becomes the previous window when time advances.
            previous_count = current_count if current == previous + 1 else 0
            current_count, previous = 0, current
        fraction = (now % self.window) / self.window
        # Older requests contribute less as the previous window expires.
        estimate = previous_count * (1 - fraction) + current_count
        if estimate >= self.limit:
            self._windows[key] = (previous, current_count, previous_count)
            return False
        self._windows[key] = (previous, current_count + 1, previous_count)
        return True


@dataclass
class _Bucket:
    """Mutable state for one token bucket."""

    tokens: float
    last: float


# ALGORITHM 4: Token Bucket
# Imagine a bucket that can hold a limited number of tokens.
# Tokens are added gradually according to the refill rate.
# Every accepted request removes tokens from the bucket.
# A full bucket allows a short burst of requests.
# An empty bucket rejects requests until more tokens arrive.
class TokenBucket:
    """Allow bursts up to capacity while enforcing an average refill rate."""

    def __init__(self, capacity: int, refill_rate: float, clock: Callable[[], float] = time.monotonic):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be positive")
        self.capacity, self.rate, self.clock = capacity, refill_rate, clock
        self._buckets: dict[str, _Bucket] = {}

    def allow(self, key: str, cost: float = 1) -> bool:
        if cost <= 0 or cost > self.capacity:
            raise ValueError("cost must be positive and no greater than capacity")
        now = self.clock()
        bucket = self._buckets.setdefault(key, _Bucket(self.capacity, now))
        # Refill lazily: no background timer is needed for inactive keys.
        bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.last) * self.rate)
        bucket.last = now
        if bucket.tokens < cost:
            return False
        bucket.tokens -= cost
        return True


# ALGORITHM 5: Leaky Bucket
# This algorithm puts incoming work into a bounded queue.
# A drain rate removes queued work at a steady speed.
# The queue smooths bursts before work reaches a downstream service.
# New work is rejected when the queue has reached its capacity.
# Unlike a token bucket, it produces a steady output rate.
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
        # Only whole drain slots can remove queue items.
        for _ in range(min(len(queue), int(elapsed * self.rate))):
            queue.popleft()
        self._last[key] = now

    def enqueue(self, key: str, item: object) -> bool:
        """Add an item unless this key's bounded queue is full."""
        now = self.clock()
        self._drain(key, now)
        queue = self._queues[key]
        if len(queue) >= self.capacity:
            return False
        queue.append(item)
        return True

    def drain(self, key: str) -> list[object]:
        """Return the items still waiting after applying elapsed drainage."""
        now = self.clock()
        self._drain(key, now)
        queue = self._queues.setdefault(key, deque())
        return list(queue)
