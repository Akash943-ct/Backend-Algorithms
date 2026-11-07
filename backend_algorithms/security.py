"""Small security primitives. Review and harden these before production use."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


# ALGORITHM 7: JWT Access Tokens
# A JWT contains a header, claims payload, and cryptographic signature.
# The encoder adds issue and expiry times to the claims.
# The decoder checks the fixed HS256 algorithm before verifying the signature.
# It also validates expiry, issuer, and audience when configured.
# JWTs are signed, not encrypted, so secret data must not be put in claims.
class JWT:
    def __init__(self, secret: bytes, issuer: str | None = None, audience: str | None = None):
        self.secret, self.issuer, self.audience = secret, issuer, audience

    def encode(self, claims: dict, lifetime_seconds: int = 900) -> str:
        now = int(time.time())
        payload = {**claims, "iat": now, "exp": now + lifetime_seconds}
        header = {"alg": "HS256", "typ": "JWT"}
        unsigned = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
        return f"{unsigned}.{_b64(hmac.new(self.secret, unsigned.encode(), hashlib.sha256).digest())}"

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
        now = int(time.time())
        if payload.get("exp", 0) < now - leeway:
            raise ValueError("expired JWT")
        if self.issuer is not None and payload.get("iss") != self.issuer:
            raise ValueError("invalid issuer")
        if self.audience is not None and payload.get("aud") != self.audience:
            raise ValueError("invalid audience")
        return payload


# ALGORITHM 9: Password Hashing
# Password hashing converts a password into a one-way derived value.
# A fresh random salt makes identical passwords hash differently.
# PBKDF2 repeats the work many times to slow password guessing.
# Verification hashes the supplied password with the stored parameters.
# Production systems should prefer a dedicated Argon2id or bcrypt library.
class PasswordHasher:
    """PBKDF2 fallback; prefer Argon2id or bcrypt for deployed password storage."""

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


# ALGORITHM 11: HMAC Request and Webhook Signing
# HMAC combines a shared secret with the timestamp and raw message body.
# The sender sends the timestamp and resulting signature to the receiver.
# The receiver independently calculates the expected signature.
# Constant-time comparison prevents timing information from leaking.
# Timestamp tolerance limits how long an intercepted message can be replayed.
class HMACSigner:
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


# ALGORITHM 10: OAuth 2.0 PKCE Code Challenge
# PKCE protects an OAuth authorization code during the redirect flow.
# The client creates a secret verifier before starting authorization.
# It sends a SHA-256 challenge derived from that verifier to the provider.
# Later, the client proves possession by sending the original verifier.
# An attacker who steals only the authorization code cannot redeem it.
def pkce_challenge(verifier: str) -> str:
    return _b64(hashlib.sha256(verifier.encode("ascii")).digest())


def new_pkce_verifier() -> str:
    return secrets.token_urlsafe(32)


def validate_oauth_state(expected: str, received: str) -> None:
    if not hmac.compare_digest(expected, received):
        raise ValueError("invalid OAuth state")


# ALGORITHM 8: Refresh Token Rotation and Reuse Detection
# A refresh token is exchanged for a new access and refresh token.
# This store keeps only a hash of each refresh token.
# Rotation marks the old token as used immediately after a successful exchange.
# Reusing an old token indicates possible theft of the token family.
# Reuse detection then invalidates every token in that family.
class RefreshTokenStore:
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
                user, fam, _ = self._tokens[member]
                self._tokens[member] = (user, fam, True)
            raise ValueError("refresh token reuse detected")
        self._tokens[token_hash] = (user_id, family, True)
        return self.issue(user_id, family)


# ALGORITHM 12: TOTP Two-Factor Authentication
# TOTP creates a short numeric code from a secret and the current time.
# Time is divided into fixed intervals, normally 30 seconds.
# HMAC produces a changing value that is truncated to six digits.
# Verification checks the current interval and nearby intervals for clock drift.
# Login attempts should be rate-limited because the code space is small.
class TOTPAuthenticator:
    """HOTP/TOTP authenticator with a configurable clock step."""

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
