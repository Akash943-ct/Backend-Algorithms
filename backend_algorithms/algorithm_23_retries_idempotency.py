"""Algorithm 23: Retries and Idempotency.

Retries can recover from temporary network or service failures.
Exponential backoff increases the delay after each failure.
Jitter prevents many clients retrying at the same instant.
An idempotency key identifies one logical operation.
Repeated keys return the first result instead of repeating side effects.
"""

# Technical Example:
# store.execute("payment-42", charge_card)
# store.execute("payment-42", charge_card)
# Output: charge_card runs once; both calls return its first result.
# A decorated retry function can run up to the configured attempt count.

# Easy Example:
# If a phone call fails, try again; but do not place the same order twice.
# The first call fails, and the same order button is pressed twice.
# The call is retried, while the order is created only once.

import random
import time
from functools import wraps
from typing import Callable


class IdempotencyStore:
    """Return one stored result for every logical operation key."""

    def __init__(self):
        self._results: dict[str, object] = {}

    def execute(self, key: str, operation: Callable[[], object]) -> object:
        if key not in self._results:
            self._results[key] = operation()
        return self._results[key]


def retry(attempts: int = 3, base_delay: float = 0.1, max_delay: float = 5, retry_on=(Exception,)):
    """Retry transient failures with capped exponential backoff and jitter."""
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

__all__ = ["IdempotencyStore", "retry"]
