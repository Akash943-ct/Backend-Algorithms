"""Algorithm 16: Cache Stampede Prevention.

Many callers can observe the same hot key expiring.
Without protection, all callers rebuild it at once.
Single-flight lets one loader produce the replacement value.
Other callers reuse that result instead of hitting the database.
Production multi-server systems need distributed locking.
"""

# Technical Example:
# single.get_or_set("homepage", lambda: "fresh page")
# single.get_or_set("homepage", lambda: "database reload")
# Output: both calls return "fresh page"; the loader runs only once.

# Easy Example:
# When many children ask for the same story, one person reads it aloud.
# Five children ask for the story at the same time.
# The story is fetched once and shared with all five children.

from typing import Generic, TypeVar

T = TypeVar("T")


class SingleFlight(Generic[T]):
    """Run one loader for a key and reuse its result for later callers."""

    def __init__(self):
        self._values: dict[str, T] = {}

    def get_or_set(self, key: str, loader) -> T:
        if key not in self._values:
            self._values[key] = loader()
        return self._values[key]

__all__ = ["SingleFlight"]
