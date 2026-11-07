"""Algorithm 17: Load Balancing.

A load balancer chooses a backend for each request.
Round robin rotates evenly through the server list.
Weighted round robin favors stronger servers.
Least connections favors servers with less active work.
Health checks should remove failing servers from selection.
"""

# Technical Example:
# balancer = LoadBalancer(["api-1", "api-2"])
# balancer.round_robin(), balancer.round_robin()
# Output: "api-1", then "api-2"; the next call cycles to "api-1".

# Easy Example:
# A teacher sends students to two equally sized lines.
# Send four students one at a time using alternating lines.
# The students go to line 1, line 2, line 1, and line 2.

import itertools


class LoadBalancer:
    """Choose servers with round robin, weights, or active connections."""

    def __init__(self, servers: dict[str, int] | list[str]):
        self.servers = list(servers)
        self.weights = servers if isinstance(servers, dict) else {server: 1 for server in servers}
        self._round_robin = itertools.cycle(self.servers)
        self._connections = {server: 0 for server in self.servers}
        self._counter = itertools.count()

    def round_robin(self) -> str:
        return next(self._round_robin)

    def weighted_round_robin(self) -> str:
        expanded = [server for server, weight in self.weights.items() for _ in range(weight)]
        return expanded[next(self._counter) % len(expanded)]

    def least_connections(self) -> str:
        return min(self._connections, key=self._connections.get)

    def connection_opened(self, server: str) -> None:
        self._connections[server] += 1

    def connection_closed(self, server: str) -> None:
        self._connections[server] = max(0, self._connections[server] - 1)

__all__ = ["LoadBalancer"]
