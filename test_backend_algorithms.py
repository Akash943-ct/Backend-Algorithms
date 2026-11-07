import unittest

from backend_algorithms import (
    BloomFilter,
    CircuitBreaker,
    ConsistentHashRing,
    FixedWindowLimiter,
    IdempotencyStore,
    LeakyBucket,
    LFUCache,
    JWT,
    LRUCache,
    RefreshTokenStore,
    ShardMap,
    SlidingWindowLog,
    PasswordHasher,
    Snowflake,
    TTLCache,
    TokenBucket,
    base62_encode,
    paginate_cursor,
    retry,
)
from backend_algorithms.security import (
    HMACSigner,
    TOTPAuthenticator,
    new_pkce_verifier,
    pkce_challenge,
    validate_oauth_state,
)


class FakeClock:
    def __init__(self, value=0):
        self.value = value

    def __call__(self):
        return self.value


class BackendAlgorithmTests(unittest.TestCase):
    def test_token_bucket_and_lru(self):
        limiter = TokenBucket(2, 1)
        self.assertTrue(limiter.allow("user"))
        self.assertTrue(limiter.allow("user"))
        self.assertFalse(limiter.allow("user"))
        cache = LRUCache(1)
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertIsNone(cache.get("a"))

    def test_rate_limiters_with_real_request_times(self):
        clock = FakeClock()
        fixed = FixedWindowLimiter(2, 60, clock)
        self.assertTrue(fixed.allow("alice"))
        self.assertTrue(fixed.allow("alice"))
        self.assertFalse(fixed.allow("alice"))
        clock.value = 60
        self.assertTrue(fixed.allow("alice"))

        clock.value = 0
        sliding = SlidingWindowLog(2, 10, clock)
        self.assertTrue(sliding.allow("alice"))
        clock.value = 5
        self.assertTrue(sliding.allow("alice"))
        clock.value = 10
        self.assertTrue(sliding.allow("alice"))

        clock.value = 0
        leaky = LeakyBucket(2, 1, clock)
        self.assertTrue(leaky.enqueue("orders", "order-1"))
        self.assertTrue(leaky.enqueue("orders", "order-2"))
        self.assertFalse(leaky.enqueue("orders", "order-3"))
        clock.value = 1
        self.assertEqual(leaky.drain("orders"), ["order-2"])

    def test_cache_expiry_and_frequency(self):
        clock = FakeClock()
        ttl = TTLCache(clock)
        ttl.put("session:42", "active", 30)
        self.assertEqual(ttl.get("session:42"), "active")
        clock.value = 30
        self.assertIsNone(ttl.get("session:42"))

        lfu = LFUCache(2)
        lfu.put("hot", "A")
        lfu.get("hot")
        lfu.put("cold", "B")
        lfu.put("new", "C")
        self.assertEqual(lfu.get("hot"), "A")
        self.assertIsNone(lfu.get("cold"))

    def test_security_primitives(self):
        jwt = JWT(b"secret")
        self.assertEqual(jwt.decode(jwt.encode({"sub": "u"}))["sub"], "u")
        passwords = PasswordHasher()
        encoded = passwords.hash("correct horse")
        self.assertTrue(passwords.verify("correct hore", encoded))
        self.assertFalse(passwords.verify("wrong", encoded))
        signer = HMACSigner(b"secret")
        signed = signer.sign(b"body", now := 1000)
        self.assertTrue(signer.verify(b"body", signed, now))
        self.assertEqual(pkce_challenge("verifier"), pkce_challenge("verifier"))
        self.assertTrue(TOTPAuthenticator(b"secret").verify(TOTPAuthenticator(b"secret").code(60), 60))
        verifier = new_pkce_verifier()
        self.assertEqual(pkce_challenge(verifier), pkce_challenge(verifier))
        validate_oauth_state("state-123", "state-123")
        with self.assertRaises(ValueError):
            validate_oauth_state("state-123", "attacker-state")

        tokens = RefreshTokenStore()
        refresh = tokens.issue("user-42")
        rotated = tokens.rotate(refresh)
        self.assertNotEqual(refresh, rotated)
        with self.assertRaises(ValueError):
            tokens.rotate(refresh)

    def test_distribution_and_probabilistic_structures(self):
        ring = ConsistentHashRing(10)
        ring.add("a")
        ring.add("b")
        self.assertIn(ring.get("key"), {"a", "b"})
        self.assertLess(Snowflake(1).next_id(1000), Snowflake(1).next_id(1001))
        bloom = BloomFilter(100)
        bloom.add("seen")
        self.assertTrue(bloom.might_contain("seen"))
        self.assertFalse(bloom.might_contain("definitely-new"))

        page = paginate_cursor([10, 20, 30, 40], limit=2)
        self.assertEqual(page.items, [10, 20])
        self.assertEqual(paginate_cursor([10, 20, 30, 40], page.next_cursor, 2).items, [30, 40])
        self.assertEqual(base62_encode(125), "21")
        self.assertIn(ShardMap(["db-a", "db-b"]).shard_for("user-42"), {"db-a", "db-b"})

    def test_circuit_breaker(self):
        breaker = CircuitBreaker(2, 10)
        def fail():
            raise ValueError
        with self.assertRaises(ValueError):
            breaker.call(fail)
        with self.assertRaises(ValueError):
            breaker.call(fail)
        with self.assertRaises(RuntimeError):
            breaker.call(lambda: "unreachable")

    def test_retry_and_idempotency(self):
        attempts = 0

        @retry(attempts=3, base_delay=0, max_delay=0)
        def eventually_succeeds():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise TimeoutError
            return "payment-authorized"

        self.assertEqual(eventually_succeeds(), "payment-authorized")
        self.assertEqual(attempts, 3)

        calls = 0

        def charge_card():
            nonlocal calls
            calls += 1
            return "charge-1001"

        store = IdempotencyStore()
        self.assertEqual(store.execute("checkout-42", charge_card), "charge-1001")
        self.assertEqual(store.execute("checkout-42", charge_card), "charge-1001")
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
