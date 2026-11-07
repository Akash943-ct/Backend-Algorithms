"""Algorithm 22: Unique ID Generation.

Snowflake IDs combine time, machine identity, and a sequence.
This lets many machines generate sortable IDs independently.
Base62 converts numeric IDs into shorter URL-friendly strings.
The sequence separates IDs created in one millisecond.
Clock rollback must be handled to preserve uniqueness.
"""

# Technical Example:
# generator = Snowflake(machine_id=1); generator.next_id(now_ms=1000)
# Output: a unique integer ID containing timestamp and machine information.
# base62_encode(125) returns "21", a shorter text representation.

# Easy Example:
# Every parcel receives a number containing the day, shop, and parcel order.
# Create two parcel numbers at the same time from one shop.
# The numbers are different and can still be sorted by creation time.

import time


class Snowflake:
    """Generate sortable IDs from time, machine identity, and a sequence."""

    def __init__(self, machine_id: int, epoch: int = 1577836800000):
        if not 0 <= machine_id < 1024:
            raise ValueError("machine_id must fit in 10 bits")
        self.machine_id, self.epoch = machine_id, epoch
        self._last_ms, self._sequence = -1, 0

    def next_id(self, now_ms: int | None = None) -> int:
        now = int(time.time() * 1000) if now_ms is None else now_ms
        if now < self._last_ms:
            raise RuntimeError("clock moved backwards")
        if now == self._last_ms:
            self._sequence = (self._sequence + 1) & 0xFFF
            if self._sequence == 0:
                now += 1
        else:
            self._sequence = 0
        self._last_ms = now
        return ((now - self.epoch) << 22) | (self.machine_id << 12) | self._sequence


_BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(value: int) -> str:
    """Convert a non-negative integer into a compact URL-friendly string."""
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return _BASE62[0]
    result = []
    while value:
        value, remainder = divmod(value, 62)
        result.append(_BASE62[remainder])
    return "".join(reversed(result))

__all__ = ["Snowflake", "base62_encode"]
