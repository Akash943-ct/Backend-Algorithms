"""Algorithm 09: Password Hashing.

Passwords must never be stored as plain text.
A random salt makes each stored hash unique.
PBKDF2 repeats hashing to make guessing expensive.
Verification repeats the same derivation and compares safely.
Production systems should prefer Argon2id or bcrypt libraries.
"""

# Technical Example:
# encoded = PasswordHasher().hash("correct horse")
# verify("correct horse", encoded) returns True.
# verify("wrong password", encoded) returns False.

# Easy Example:
# A school stores a difficult-to-reverse fingerprint of each student's secret word.
# Compare the fingerprint made from the correct word and a wrong word.
# The correct word matches; the wrong word does not.

import base64
import hashlib
import hmac
import secrets


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class PasswordHasher:
    """Hash passwords with salted, deliberately expensive PBKDF2."""

    def hash(self, password: str, iterations: int = 600_000) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        return f"pbkdf2_sha256${iterations}${_b64(salt)}${_b64(digest)}"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, raw_iterations, salt, expected = encoded.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(raw_iterations))
            return hmac.compare_digest(actual, _unb64(expected))
        except (ValueError, TypeError):
            return False

__all__ = ["PasswordHasher"]
