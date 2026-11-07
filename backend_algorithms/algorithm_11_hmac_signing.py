"""Algorithm 11: HMAC Request Signing.

The sender combines a shared secret with a timestamp and body.
The receiver calculates the expected HMAC independently.
Constant-time comparison checks whether both signatures match.
The timestamp prevents old messages from being replayed forever.
The raw request body must be signed exactly as received.
"""

# Technical Example:
# signature = signer.sign(b'{"event":"paid"}', timestamp=1000)
# signer.verify(b'{"event":"paid"}', signature, now=1000) returns True.
# Changing the body or using an old timestamp returns False.

# Easy Example:
# Two friends agree on a secret stamp for passing notes.
# Send a note with the stamp, then change one word in the note.
# The original note is accepted; the changed note is rejected.

import hashlib
import hmac
import time


class HMACSigner:
    """Sign raw request bodies and reject stale or modified messages."""

    def __init__(self, secret: bytes, tolerance_seconds: int = 300):
        self.secret, self.tolerance = secret, tolerance_seconds

    def sign(self, body: bytes, timestamp: int | None = None) -> str:
        timestamp = int(time.time()) if timestamp is None else timestamp
        digest = hmac.new(self.secret, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        return f"{timestamp}.{digest}"

    def verify(self, body: bytes, signature: str, now: int | None = None) -> bool:
        try:
            timestamp_text, digest = signature.split(".", 1)
            timestamp = int(timestamp_text)
        except (ValueError, AttributeError):
            return False
        now = int(time.time()) if now is None else now
        if abs(now - timestamp) > self.tolerance:
            return False
        expected = hmac.new(self.secret, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, digest)

__all__ = ["HMACSigner"]
