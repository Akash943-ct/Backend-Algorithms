"""Algorithm 01: Fixed Window Counter.

Time is divided into fixed blocks such as one minute.
Each client receives a counter for the current block.
Requests increment the counter and are rejected after the limit.
The counter resets when the next block begins.
This is simple and cheap, but boundary bursts are possible.
"""

# Technical Example:
# limiter = FixedWindowLimiter(limit=2, window_seconds=60)
# limiter.allow("alice"), limiter.allow("alice")  # True, True
# A third call in the same 60-second window returns False.

# Easy Example:
# Easy Example: A cinema allows only 2 people into a small room each minute.
# Two people enter; a third person arrives before the minute ends.
# The first two enter, and the third person waits.

import time
from typing import Callable


class FixedWindowLimiter:
    """Count requests independently inside each fixed-duration time window."""

    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit, self.window, self.clock = limit, window_seconds, clock
        self._windows: dict[str, tuple[int, int]] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        window_id = int(now // self.window)
        old_id, count = self._windows.get(key, (window_id, 0))
        count = count + 1 if old_id == window_id else 1
        self._windows[key] = (window_id, count)
        return count <= self.limit

__all__ = ["FixedWindowLimiter"]
