"""Algorithm 02: Sliding Window Log.

Store one timestamp for every request.
Remove timestamps older than the rolling time window.
Count the timestamps that remain for the client.
Reject the request when that count reaches the limit.
This is accurate but uses memory proportional to traffic.
"""

# Technical Example:
# limiter = SlidingWindowLog(limit=2, window_seconds=10)
# Two requests at seconds 0 and 5 return True.
# A request at second 6 returns False until an old timestamp expires.

# Easy Example:
# A teacher allows 2 questions from each student during any 10 minutes.
# A student asks at minute 1, minute 5, and minute 6.
# The first two questions are accepted; the third must wait.

import time
from collections import deque
from typing import Callable


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
        while events and events[0] <= now - self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True

__all__ = ["SlidingWindowLog"]
