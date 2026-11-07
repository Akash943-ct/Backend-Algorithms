"""Algorithm 24: Circuit Breaker.

The closed state allows calls and counts failures.
The open state rejects calls immediately during recovery.
The half-open state permits a small trial request.
A successful trial closes the circuit again.
A failed trial reopens it to protect the dependency.
"""

# Technical Example:
# breaker = CircuitBreaker(failure_threshold=2)
# breaker.call(failing_service) twice
# Output: the first two calls raise the service error.
# A third immediate call raises RuntimeError because the circuit is open.

# Easy Example:
# Stop visiting a shop after it is closed several times in a row.
# Try the shop twice while it is closed, then try immediately again.
# The first tries fail; later visits are paused until the shop may reopen.

import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Stop calling a failing dependency until a recovery trial is allowed."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30, clock=time.monotonic):
        if failure_threshold <= 0 or recovery_timeout <= 0:
            raise ValueError("threshold and timeout must be positive")
        self.threshold, self.timeout, self.clock = failure_threshold, recovery_timeout, clock
        self.state, self.failures, self._opened_at = CircuitState.CLOSED, 0, 0.0

    def call(self, function, *args, **kwargs):
        now = self.clock()
        if self.state is CircuitState.OPEN:
            if now - self._opened_at < self.timeout:
                raise RuntimeError("circuit is open")
            self.state = CircuitState.HALF_OPEN
        try:
            result = function(*args, **kwargs)
        except Exception:
            self.failures += 1
            if self.state is CircuitState.HALF_OPEN or self.failures >= self.threshold:
                self.state, self._opened_at = CircuitState.OPEN, now
            raise
        self.failures, self.state = 0, CircuitState.CLOSED
        return result

__all__ = ["CircuitBreaker", "CircuitState"]
