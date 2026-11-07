# Run this file from PowerShell:
# .\RUN_ALGORITHMS.ps1

$Python = "C:\Users\ritsa\AppData\Local\Programs\Python\Python312\python.exe"
$Workspace = "D:\ADVCLUB SOP\Workshop Code"

if (-not (Test-Path $Python)) {
    Write-Error "Python was not found at $Python"
    exit 1
}

Set-Location $Workspace

Write-Host "`n1. Fixed Window Counter"
& $Python -c "from backend_algorithms.algorithm_01_fixed_window import FixedWindowLimiter; x=FixedWindowLimiter(2,60); print(x.allow('alice'),x.allow('alice'),x.allow('alice'))"

Write-Host "`n2. Sliding Window Log"
& $Python -c "from backend_algorithms.algorithm_02_sliding_window_log import SlidingWindowLog; x=SlidingWindowLog(2,10); print(x.allow('alice'),x.allow('alice'),x.allow('alice'))"

Write-Host "`n3. Sliding Window Counter"
& $Python -c "from backend_algorithms.algorithm_03_sliding_window_counter import SlidingWindowCounter; x=SlidingWindowCounter(3,60); print(x.allow('alice'),x.allow('alice'),x.allow('alice'),x.allow('alice'))"

Write-Host "`n4. Token Bucket"
& $Python -c "from backend_algorithms.algorithm_04_token_bucket import TokenBucket; x=TokenBucket(2,1); print(x.allow('api-key'),x.allow('api-key'),x.allow('api-key'))"

Write-Host "`n5. Leaky Bucket"
& $Python -c "from backend_algorithms.algorithm_05_leaky_bucket import LeakyBucket; x=LeakyBucket(2,1); print(x.enqueue('orders','order-1'),x.enqueue('orders','order-2'),x.enqueue('orders','order-3'))"

Write-Host "`n6. Rate-Limit Headers"
& $Python -c "from backend_algorithms.algorithm_06_rate_limit_headers import rate_limit_headers; print(rate_limit_headers(100,25,1700000060))"

Write-Host "`n7. JWT Access Token"
& $Python -c "from backend_algorithms.algorithm_07_jwt import JWT; x=JWT(b'secret'); token=x.encode({'sub':'user-42'}); print(x.decode(token))"

Write-Host "`n8. Refresh Token Rotation"
& $Python -c "from backend_algorithms.algorithm_08_refresh_tokens import RefreshTokenStore; x=RefreshTokenStore(); old=x.issue('user-42'); new=x.rotate(old); print('Rotated:',old != new)"

Write-Host "`n9. Password Hashing"
& $Python -c "from backend_algorithms.algorithm_09_password_hashing import PasswordHasher; x=PasswordHasher(); h=x.hash('hello'); print(x.verify('hello',h),x.verify('wrong',h))"

Write-Host "`n10. OAuth PKCE"
& $Python -c "from backend_algorithms.algorithm_10_pkce import pkce_challenge; print(pkce_challenge('client-secret-verifier'))"

Write-Host "`n11. HMAC Signing"
& $Python -c "from backend_algorithms.algorithm_11_hmac_signing import HMACSigner; x=HMACSigner(b'secret'); s=x.sign(b'body',1000); print(x.verify(b'body',s,1000),x.verify(b'changed',s,1000))"

Write-Host "`n12. TOTP"
& $Python -c "from backend_algorithms.algorithm_12_totp import TOTPAuthenticator; x=TOTPAuthenticator(b'shared-secret'); code=x.code(60); print(code,x.verify(code,60))"

Write-Host "`n13. LRU Cache"
& $Python -c "from backend_algorithms.algorithm_13_lru_cache import LRUCache; x=LRUCache(2); x.put('a',1); x.put('b',2); x.get('a'); x.put('c',3); print(x.get('b'))"

Write-Host "`n14. LFU Cache"
& $Python -c "from backend_algorithms.algorithm_14_lfu_ttl import LFUCache; x=LFUCache(2); x.put('hot','A'); x.get('hot'); x.put('cold','B'); x.put('new','C'); print(x.get('hot'),x.get('cold'),x.get('new'))"

Write-Host "`n15. Caching Strategy"
& $Python -c "from backend_algorithms.algorithm_15_caching_strategies import LRUCache; cache=LRUCache(1); value=cache.get('user:42'); print('Cache miss:',value is None); cache.put('user:42','Alice'); print('Cache hit:',cache.get('user:42'))"

Write-Host "`n16. Cache Stampede Prevention"
& $Python -c "from backend_algorithms.algorithm_16_stampede_prevention import SingleFlight; x=SingleFlight(); print(x.get_or_set('homepage',lambda:'fresh page')); print(x.get_or_set('homepage',lambda:'database reload'))"

Write-Host "`n17. Load Balancing"
& $Python -c "from backend_algorithms.algorithm_17_load_balancing import LoadBalancer; x=LoadBalancer(['api-1','api-2']); print(x.round_robin(),x.round_robin(),x.round_robin())"

Write-Host "`n18. Consistent Hashing"
& $Python -c "from backend_algorithms.algorithm_18_consistent_hashing import ConsistentHashRing; x=ConsistentHashRing(); x.add('server-a'); x.add('server-b'); print(x.get('user-42'))"

Write-Host "`n19. Bloom Filter"
& $Python -c "from backend_algorithms.algorithm_19_bloom_filter import BloomFilter; x=BloomFilter(100); x.add('alice'); print(x.might_contain('alice'),x.might_contain('bob'))"

Write-Host "`n20. Sharding"
& $Python -c "from backend_algorithms.algorithm_20_sharding import ShardMap; x=ShardMap(['database-a','database-b']); print(x.shard_for('user-42'))"

Write-Host "`n21. Cursor Pagination"
& $Python -c "from backend_algorithms.algorithm_21_pagination import paginate_cursor; x=paginate_cursor([10,20,30,40],limit=2); print(x); print(paginate_cursor([10,20,30,40],x.next_cursor,2))"

Write-Host "`n22. Unique IDs"
& $Python -c "from backend_algorithms.algorithm_22_unique_ids import Snowflake,base62_encode; print(Snowflake(1).next_id(),base62_encode(125))"

Write-Host "`n23. Retries and Idempotency"
& $Python -c "from backend_algorithms.algorithm_23_retries_idempotency import IdempotencyStore; x=IdempotencyStore(); calls=[0]; f=lambda:(calls.__setitem__(0,calls[0]+1) or 'charge-1001'); print(x.execute('payment-42',f),x.execute('payment-42',f),'calls:',calls[0])"

Write-Host "`n24. Circuit Breaker"
& $Python -c "from backend_algorithms.algorithm_24_circuit_breaker import CircuitBreaker; x=CircuitBreaker(2,10); f=lambda:(_ for _ in ()).throw(ValueError('service unavailable')); exec('for _ in range(2):\n    try: x.call(f)\n    except ValueError: pass'); print('Failures recorded:',x.failures,'State:',x.state.value)"

Write-Host "`nAll unit tests"
& $Python -m unittest -v test_backend_algorithms.py
