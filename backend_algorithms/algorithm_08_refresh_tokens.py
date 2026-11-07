"""Algorithm 08: Refresh Token Rotation.

Refresh tokens obtain new short-lived access tokens.
The server stores a hash instead of the raw token.
Every successful refresh invalidates the old token.
Reusing an old token signals possible token theft.
The complete token family is then revoked.
"""

# Technical Example:
# old_token = store.issue("user-42")
# new_token = store.rotate(old_token)
# Output: new_token is different from old_token.

# Easy Example:
# A library replaces a visitor's long-term entry card after each renewal.
# The old card works once, but using it again is blocked.

import hashlib
import secrets


class RefreshTokenStore:
    """Rotate refresh tokens and revoke a family when reuse is detected."""

    def __init__(self):
        self._tokens: dict[str, tuple[str, str, bool]] = {}
        self._families: dict[str, set[str]] = {}

    def issue(self, user_id: str, family: str | None = None) -> str:
        family = family or secrets.token_urlsafe(16)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._tokens[token_hash] = (user_id, family, False)
        self._families.setdefault(family, set()).add(token_hash)
        return token

    def rotate(self, token: str) -> str:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = self._tokens.get(token_hash)
        if record is None:
            raise ValueError("invalid refresh token")
        user_id, family, used = record
        if used:
            for member in self._families.get(family, ()):
                user, family_name, _ = self._tokens[member]
                self._tokens[member] = (user, family_name, True)
            raise ValueError("refresh token reuse detected")
        self._tokens[token_hash] = (user_id, family, True)
        return self.issue(user_id, family)

__all__ = ["RefreshTokenStore"]
