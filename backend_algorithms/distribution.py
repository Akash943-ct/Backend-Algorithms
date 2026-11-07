"""Load balancing, consistent hashing, pagination, and ID generation."""

import bisect
import hashlib
import itertools
import time
from dataclasses import dataclass


# ALGORITHM 17: Load Balancing
# Load balancing spreads requests across multiple backend servers.
# Round robin gives servers turns in a repeating sequence.
# Weighted round robin gives stronger servers more turns.
# Least connections chooses the server handling the fewest active requests.
# Real deployments also remove unhealthy servers using health checks.
class LoadBalancer:
    def __init__(self, servers: dict[str, int] | list[str]):
        self.servers = list(servers)
        self.weights = servers if isinstance(servers, dict) else {server: 1 for server in servers}
        self._round_robin = itertools.cycle(self.servers)
        self._connections = {server: 0 for server in self.servers}

    def round_robin(self) -> str:
        return next(self._round_robin)

    def weighted_round_robin(self) -> str:
        expanded = [server for server, weight in self.weights.items() for _ in range(weight)]
        return expanded[next(self._counter) % len(expanded)] if hasattr(self, "_counter") else self._init_counter(expanded)

    def _init_counter(self, expanded: list[str]) -> str:
        self._counter = itertools.count(1)
        return expanded[0]

    def least_connections(self) -> str:
        return min(self._connections, key=self._connections.get)

    def connection_opened(self, server: str) -> None:
        self._connections[server] += 1

    def connection_closed(self, server: str) -> None:
        self._connections[server] = max(0, self._connections[server] - 1)


# ALGORITHM 18: Consistent Hashing
# Consistent hashing places servers and keys on the same circular hash ring.
# A key is assigned to the next server found clockwise on the ring.
# Virtual replicas give each server many positions for better balance.
# Adding or removing one server moves only a portion of the keys.
# This is useful for distributed caches and partitioned services.
class ConsistentHashRing:
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


@dataclass(frozen=True)
class CursorPage:
    items: list
    next_cursor: object | None


# ALGORITHM 21: Cursor (Keyset) Pagination
# Cursor pagination returns a small slice after a known last item.
# The cursor stores the last sort-key value from the previous page.
# The next query starts strictly after that value.
# It avoids scanning and discarding many rows at large offsets.
# A stable, unique sort key is required for reliable results.
def paginate_cursor(items: list, last_seen=None, limit: int = 20, key=lambda item: item) -> CursorPage:
    if limit <= 0:
        raise ValueError("limit must be positive")
    ordered = sorted(items, key=key)
    start = 0 if last_seen is None else bisect.bisect_right([key(item) for item in ordered], last_seen)
    page = ordered[start:start + limit]
    return CursorPage(page, key(page[-1]) if len(page) == limit else None)


# ALGORITHM 22: Snowflake-Style Unique ID Generation
# A Snowflake ID combines time, machine identity, and a sequence number.
# The timestamp makes IDs roughly sortable by creation time.
# The machine field lets multiple servers generate IDs independently.
# The sequence field separates IDs created in the same millisecond.
# Clock rollback is rejected because it could create duplicate or unordered IDs.
class Snowflake:
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


# ALGORITHM 20: Hash-Based Sharding
# Sharding divides a large dataset across several database partitions.
# This implementation hashes a key to choose a shard consistently.
# Similar keys are spread across shards rather than stored in one database.
# Adding shards changes many assignments with simple modulo hashing.
# Production systems may use consistent hashing or a directory service.
class ShardMap:
    def __init__(self, shards: list[str]):
        if not shards:
            raise ValueError("at least one shard is required")
        self.shards = list(shards)

    def shard_for(self, key: str) -> str:
        digest = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
        return self.shards[digest % len(self.shards)]


_BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ALGORITHM 22: Base62 ID Encoding
# Base62 represents a number using digits, lowercase letters, and uppercase letters.
# Each division by 62 produces one encoded character.
# The remainders are collected from right to left.
# Reversing them produces the final short string representation.
# This is useful for compact URL and identifier codes.
def base62_encode(value: int) -> str:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return _BASE62[0]
    result = []
    while value:
        value, remainder = divmod(value, 62)
        result.append(_BASE62[remainder])
    return "".join(reversed(result))
