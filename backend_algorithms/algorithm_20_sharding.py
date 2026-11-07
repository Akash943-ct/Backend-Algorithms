"""Algorithm 20: Hash-Based Sharding.

Sharding splits one large dataset across multiple databases.
This implementation hashes a key to choose a shard.
The same key normally maps to the same shard.
Adding shards with modulo hashing remaps many existing keys.
Shard keys must avoid hot spots and cross-shard joins.
"""

# Technical Example:
# shards = ShardMap(["database-a", "database-b"])
# shards.shard_for("user-42")
# Output: "database-a" or "database-b".
# The same key returns the same shard while the shard list is unchanged.

# Easy Example:
# Put students into classrooms using their roll numbers.
# Send roll number 42 to a classroom using the same rule each time.
# Roll number 42 always goes to the same classroom.

import hashlib


class ShardMap:
    """Select a database shard by hashing a record's stable key."""

    def __init__(self, shards: list[str]):
        if not shards:
            raise ValueError("at least one shard is required")
        self.shards = list(shards)

    def shard_for(self, key: str) -> str:
        digest = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
        return self.shards[digest % len(self.shards)]

__all__ = ["ShardMap"]
