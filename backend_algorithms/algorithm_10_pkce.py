"""Algorithm 10: OAuth 2.0 PKCE.

The client creates a secret code verifier.
It sends a hash-derived challenge during authorization.
The provider returns a temporary authorization code.
The client must later prove the original verifier.
Stolen authorization codes are therefore much less useful.
"""

# Technical Example:
# verifier = "client-secret-verifier"
# challenge = pkce_challenge(verifier)
# Output: challenge is a deterministic Base64URL SHA-256 string.
# The same verifier always produces the same challenge.

# Easy Example:
# A coat-check desk gives you a secret claim ticket and records a matching mark.
# Return with the secret ticket to collect the coat.
# The coat is returned only when your secret ticket matches the recorded mark.

import base64
import hashlib
import hmac
import secrets


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def new_pkce_verifier() -> str:
    return secrets.token_urlsafe(32)


def pkce_challenge(verifier: str) -> str:
    return _b64(hashlib.sha256(verifier.encode("ascii")).digest())


def validate_oauth_state(expected: str, received: str) -> None:
    if not hmac.compare_digest(expected, received):
        raise ValueError("invalid OAuth state")

__all__ = ["new_pkce_verifier", "pkce_challenge", "validate_oauth_state"]
