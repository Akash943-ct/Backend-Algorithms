"""Algorithm 06: Rate-Limit Response Headers.

Clients need to understand why a request was rejected.
The limit header states the maximum request count.
The remaining header states how much capacity is left.
The reset header tells the client when capacity returns.
These headers work with an HTTP 429 response.
"""

# Technical Example:
# rate_limit_headers(100, 25, 1700000060) returns {
#   "X-RateLimit-Limit": "100",
#   "X-RateLimit-Remaining": "25",
#   "X-RateLimit-Reset": "1700000060",
# }

# Easy Example:
# A sign says "100 places total, 25 places left, opens again at 6:00."
# People know how many places remain and when to try again.

def rate_limit_headers(limit: int, remaining: int, reset_at: int) -> dict[str, str]:
    """Build standard headers clients can use after a rate-limit decision."""
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset_at),
    }

__all__ = ["rate_limit_headers"]
