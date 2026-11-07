"""Algorithm 12: TOTP Two-Factor Authentication.

TOTP divides time into short fixed intervals.
The shared secret and interval produce an HMAC value.
Dynamic truncation converts that value into a short code.
Verification allows a small clock-drift window.
Login attempts must be rate-limited to prevent guessing.
"""

# Technical Example:
# authenticator = TOTPAuthenticator(b"shared-secret")
# code = authenticator.code(timestamp=60)
# Output: code is a six-digit string such as "123456".
# authenticator.verify(code, timestamp=60) returns True.

# Easy Example:
# A door lock shows a new six-number code every half minute.
# Enter the code currently shown on the matching phone.
# The current code opens the door; an old code does not.

import hashlib
import hmac
import time


class TOTPAuthenticator:
    """Generate and verify six-digit time-based one-time passwords."""

    def __init__(self, secret: bytes, step: int = 30):
        self.secret, self.step = secret, step

    def code(self, timestamp: int | None = None) -> str:
        counter = int((time.time() if timestamp is None else timestamp) // self.step)
        digest = hmac.new(self.secret, counter.to_bytes(8, "big"), hashlib.sha1).digest()
        offset = digest[-1] & 15
        number = int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF
        return f"{number % 1_000_000:06d}"

    def verify(self, code: str, timestamp: int | None = None, drift: int = 1) -> bool:
        timestamp = int(time.time() if timestamp is None else timestamp)
        return any(hmac.compare_digest(self.code(timestamp + offset * self.step), code) for offset in range(-drift, drift + 1))

__all__ = ["TOTPAuthenticator"]
