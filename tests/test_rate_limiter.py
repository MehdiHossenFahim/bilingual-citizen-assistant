"""
tests/test_rate_limiter.py — Test in-memory rate limiter logic.
"""

import time
import pytest
from app.api.rate_limiter import SlidingWindowRateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=10)
    for _ in range(5):
        allowed, retry_after = limiter.is_allowed("127.0.0.1")
        assert allowed is True
        assert retry_after == 0


def test_rate_limiter_blocks_over_limit():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=5)
    for _ in range(3):
        allowed, _ = limiter.is_allowed("192.168.1.1")
        assert allowed is True

    # 4th request must be blocked
    allowed, retry_after = limiter.is_allowed("192.168.1.1")
    assert allowed is False
    assert retry_after > 0


def test_rate_limiter_isolates_different_ips():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=5)
    limiter.is_allowed("10.0.0.1")
    limiter.is_allowed("10.0.0.1")
    blocked, _ = limiter.is_allowed("10.0.0.1")
    assert blocked is False

    # Different IP should still be allowed
    allowed, _ = limiter.is_allowed("10.0.0.2")
    assert allowed is True

