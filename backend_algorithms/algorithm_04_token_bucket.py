"""Algorithm 04: Token Bucket.

The bucket stores tokens up to a configured capacity.
Tokens refill gradually according to a fixed rate.
Each request spends tokens before it is accepted.
A full bucket permits a controlled burst.
An empty bucket makes the caller wait or retry.
"""

# Technical Example:
# bucket = TokenBucket(capacity=2, refill_rate=1)
# Three immediate calls return True, True, False.
# After one second, one token refills and the next call returns True.

# Easy Example:
# A child has a box that can hold 2 stickers and receives 1 new sticker per minute.
# The child spends both stickers immediately, then asks for another one.
# The first two actions happen; the third waits for a new sticker.

import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class _Bucket:
    tokens: float
    last: float


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
        bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.last) * self.rate)
        bucket.last = now
        if bucket.tokens < cost:
            return False
        bucket.tokens -= cost
        return True

__all__ = ["TokenBucket"]
