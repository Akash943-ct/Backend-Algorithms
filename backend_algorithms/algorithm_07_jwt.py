"""Algorithm 07: JWT Access Tokens.

A JWT contains a header, claims, and a signature.
The signature proves that trusted code created the token.
The verifier pins the allowed algorithm before checking it.
Expiry, issuer, and audience claims limit token misuse.
JWT payloads are visible, so secrets must never be stored there.
"""

# Technical Example:
# token = JWT(b"secret").encode({"sub": "user-42"})
# Output is a signed string in the form "header.payload.signature".
# JWT(b"secret").decode(token)["sub"] returns "user-42".

# Easy Example:
# A school gives a signed hall pass with a student's name and expiry time.
# The guard checks the pass and the school's stamp.
# A valid, unexpired pass allows entry; a changed pass is rejected.

import base64
import hashlib
import hmac
import json
import time


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class JWT:
    """Create and verify signed HS256 JSON Web Tokens."""

    def __init__(self, secret: bytes, issuer: str | None = None, audience: str | None = None):
        self.secret, self.issuer, self.audience = secret, issuer, audience

    def encode(self, claims: dict, lifetime_seconds: int = 900) -> str:
        now = int(time.time())
        payload = {**claims, "iat": now, "exp": now + lifetime_seconds}
        header = {"alg": "HS256", "typ": "JWT"}
        unsigned = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
        signature = hmac.new(self.secret, unsigned.encode(), hashlib.sha256).digest()
        return f"{unsigned}.{_b64(signature)}"

    def decode(self, token: str, leeway: int = 0) -> dict:
        try:
            header_text, payload_text, signature = token.split(".")
            header, payload = json.loads(_unb64(header_text)), json.loads(_unb64(payload_text))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("invalid JWT")
        if header.get("alg") != "HS256":
            raise ValueError("unsupported JWT algorithm")
        unsigned = f"{header_text}.{payload_text}"
        expected = hmac.new(self.secret, unsigned.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            raise ValueError("invalid JWT signature")
        if payload.get("exp", 0) < int(time.time()) - leeway:
            raise ValueError("expired JWT")
        if self.issuer is not None and payload.get("iss") != self.issuer:
            raise ValueError("invalid issuer")
        if self.audience is not None and payload.get("aud") != self.audience:
            raise ValueError("invalid audience")
        return payload

__all__ = ["JWT"]
