"""Algorithm 21: Cursor Pagination.

Cursor pagination returns results after a known last item.
The cursor contains the previous page's sort-key value.
The next page starts strictly after that value.
It stays fast at deep positions compared with large offsets.
The sort key must be stable and unique.
"""

# Technical Example:
# paginate_cursor([10, 20, 30, 40], limit=2)
# Output: CursorPage(items=[10, 20], next_cursor=20).
# Calling paginate_cursor(..., last_seen=20, limit=2) returns [30, 40].

# Easy Example:
# A long book is read two pages at a time.
# Read pages 10 and 20, then continue after page 20.
# The next reading starts with page 30 instead of starting over.

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class CursorPage:
    items: list
    next_cursor: object | None


def paginate_cursor(items: list, last_seen=None, limit: int = 20, key=lambda item: item) -> CursorPage:
    """Return a stable page beginning after the previous cursor value."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    ordered = sorted(items, key=key)
    keys = [key(item) for item in ordered]
    start = 0 if last_seen is None else bisect.bisect_right(keys, last_seen)
    page = ordered[start:start + limit]
    return CursorPage(page, key(page[-1]) if len(page) == limit else None)

__all__ = ["CursorPage", "paginate_cursor"]
