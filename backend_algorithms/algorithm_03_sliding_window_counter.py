"""Algorithm 03: Sliding Window Counter.

Keep counts for the current and previous fixed windows.
Estimate the previous window's contribution using elapsed time.
Add that weighted count to the current count.
Reject when the estimate reaches the configured limit.
This saves memory but is an approximation.
"""

# Technical Example:
# limiter = SlidingWindowCounter(limit=3, window_seconds=60)
# Calling limiter.allow("alice") three times returns True.
# A fourth request is rejected while the estimated count is at least 3.

# Easy Example:
# A shop estimates how busy it is by comparing this hour with the last hour.
# Three customers arrive very quickly.
# The shop temporarily asks the next customer to wait.

import time
from typing import Callable


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
            previous_count = current_count if current == previous + 1 else 0
            current_count, previous = 0, current
        fraction = (now % self.window) / self.window
        estimate = previous_count * (1 - fraction) + current_count
        if estimate >= self.limit:
            self._windows[key] = (previous, current_count, previous_count)
            return False
        self._windows[key] = (previous, current_count + 1, previous_count)
        return True

__all__ = ["SlidingWindowCounter"]
