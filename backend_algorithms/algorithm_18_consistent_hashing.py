"""Algorithm 18: Consistent Hashing.

Servers and keys are placed on a circular hash ring.
A key belongs to the next server clockwise.
Virtual replicas make ownership more evenly distributed.
Adding a server moves only a portion of the keys.
This is valuable for distributed caches and storage.
"""

# Technical Example:
# ring = ConsistentHashRing(); ring.add("server-a"); ring.add("server-b")
# ring.get("user-42")
# Output: either "server-a" or "server-b", selected consistently.
# Removing one server moves only keys assigned to that server.

# Easy Example:
# Put houses around a circular road and give each parcel to the next house.
# Add or remove one house from the circle.
# Only nearby parcels change owners instead of every parcel moving.

import bisect
import hashlib


class ConsistentHashRing:
    """Map keys to servers while minimizing movement during membership changes."""

    def __init__(self, replicas: int = 100):
        self.replicas = replicas
        self._ring: dict[int, str] = {}
        self._points: list[int] = []

    def add(self, server: str) -> None:
        for replica in range(self.replicas):
            point = int.from_bytes(hashlib.sha256(f"{server}:{replica}".encode()).digest()[:8], "big")
            self._ring[point] = server
        self._points = sorted(self._ring)

    def remove(self, server: str) -> None:
        self._ring = {point: value for point, value in self._ring.items() if value != server}
        self._points = sorted(self._ring)

    def get(self, key: str) -> str:
        if not self._points:
            raise LookupError("ring is empty")
        point = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
        index = bisect.bisect_left(self._points, point) % len(self._points)
        return self._ring[self._points[index]]

__all__ = ["ConsistentHashRing"]
