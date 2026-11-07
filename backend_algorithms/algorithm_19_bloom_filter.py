"""Algorithm 19: Bloom Filter.

A Bloom filter uses bits and several hash positions.
Adding a value sets all of its calculated positions.
Checking a value tests whether those positions are set.
A missing bit proves the value is absent.
All set bits mean possibly present because false positives exist.
"""

# Technical Example:
# bloom = BloomFilter(100); bloom.add("alice@example.com")
# Output: bloom.might_contain("alice@example.com") is True.
# A new value may return False, while a True result means "possibly present".

# Easy Example:
# A guest list uses several small marks to quickly check names.
# Check a name with one missing mark and a name with all marks present.
# A missing mark means "not on the list"; all marks mean "maybe on it."

import hashlib


class BloomFilter:
    """Answer membership queries compactly with possible false positives."""

    def __init__(self, size: int, hashes: int = 3):
        if size <= 0 or hashes <= 0:
            raise ValueError("size and hashes must be positive")
        self.size, self.hashes = size, hashes
        self._bits = bytearray((size + 7) // 8)

    def _positions(self, value: str):
        digest = hashlib.sha256(value.encode()).digest()
        for index in range(self.hashes):
            yield int.from_bytes(digest[index * 4:index * 4 + 4], "big") % self.size

    def add(self, value: str) -> None:
        for position in self._positions(value):
            self._bits[position // 8] |= 1 << (position % 8)

    def might_contain(self, value: str) -> bool:
        return all(self._bits[p // 8] & (1 << (p % 8)) for p in self._positions(value))

__all__ = ["BloomFilter"]
