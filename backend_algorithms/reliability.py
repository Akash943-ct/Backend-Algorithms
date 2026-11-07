"""Retries and circuit breaker state machine."""

import random
import time
from enum import Enum
from functools import wraps
from typing import Callable


# ALGORITHM 23: Idempotency Keys
# An idempotency key identifies one logical client operation.
# The first request runs the operation and stores its result.
# Repeated requests with the same key return the stored result.
# This prevents retries from charging or creating the same resource twice.
# A production store should persist keys with an expiration and atomic writes.
class IdempotencyStore:
    def __init__(self):
        self._results: dict[str, object] = {}

    def execute(self, key: str, operation: Callable[[], object]) -> object:
        if key not in self._results:
            self._results[key] = operation()
        return self._results[key]


# ALGORITHM 23: Retries with Exponential Backoff and Jitter
# Retries give temporary failures another chance to succeed.
# Exponential backoff increases the wait after each failed attempt.
# Jitter randomizes the wait so clients do not retry simultaneously.
# The attempt limit prevents infinite loops and unbounded load.
# Only transient failures should be retried in a real client.
def retry(attempts: int = 3, base_delay: float = 0.1, max_delay: float = 5, retry_on=(Exception,)):
    if attempts <= 0:
        raise ValueError("attempts must be positive")

    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return function(*args, **kwargs)
                except retry_on:
                    if attempt == attempts - 1:
                        raise
                    delay = min(max_delay, base_delay * (2 ** attempt))
                    time.sleep(random.uniform(0, delay))
        return wrapped
    return decorator


# SUPPORTING STATE: Circuit Breaker States
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# ALGORITHM 24: Circuit Breaker
# A circuit breaker protects a service from repeatedly calling a failing dependency.
# Closed means calls flow normally while failures are counted.
# Open rejects calls immediately during the recovery timeout.
# Half-open permits a trial call after the timeout has elapsed.
# A successful trial closes the circuit; another failure opens it again.
class CircuitBreaker:
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
