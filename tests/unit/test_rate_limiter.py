"""Unit tests for RateLimiter."""

import time
import pytest
from src.ingestion.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_initialization(self) -> None:
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_second=10)
        assert limiter.requests_per_second == 10
        assert limiter.time_window == 1.0
        assert len(limiter.request_times) == 0

    def test_acquire_single_request(self) -> None:
        """Test acquiring permission for a single request."""
        limiter = RateLimiter(requests_per_second=10)
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be nearly instant
        assert len(limiter.request_times) == 1

    def test_rate_limiting_enforced(self) -> None:
        """Test that rate limiting is actually enforced."""
        requests_per_second = 5
        limiter = RateLimiter(requests_per_second=requests_per_second)

        start = time.time()

        # Make more requests than allowed per second
        for _ in range(requests_per_second + 2):
            limiter.acquire()

        elapsed = time.time() - start

        # Should take at least 1 second due to rate limiting
        assert elapsed >= 1.0

    def test_get_current_rate(self) -> None:
        """Test getting current request rate."""
        limiter = RateLimiter(requests_per_second=10)

        # Initially zero
        assert limiter.get_current_rate() == 0.0

        # After some requests
        for _ in range(5):
            limiter.acquire()

        rate = limiter.get_current_rate()
        assert 0 < rate <= 10

    def test_reset(self) -> None:
        """Test resetting the rate limiter."""
        limiter = RateLimiter(requests_per_second=10)

        # Make some requests
        for _ in range(5):
            limiter.acquire()

        assert len(limiter.request_times) == 5

        # Reset
        limiter.reset()

        assert len(limiter.request_times) == 0
        assert limiter.get_current_rate() == 0.0

    def test_time_window_cleanup(self) -> None:
        """Test that old requests are removed from the window."""
        limiter = RateLimiter(requests_per_second=10)

        # Make a request
        limiter.acquire()
        assert len(limiter.request_times) == 1

        # Wait for time window to pass
        time.sleep(1.1)

        # Check rate (should trigger cleanup)
        rate = limiter.get_current_rate()
        assert rate == 0.0
        assert len(limiter.request_times) == 0

    def test_burst_handling(self) -> None:
        """Test handling of burst requests."""
        limiter = RateLimiter(requests_per_second=2)

        start = time.time()

        # Try to make 5 requests (burst)
        for _ in range(5):
            limiter.acquire()

        elapsed = time.time() - start

        # Should take at least 2 seconds (5 requests at 2 req/s)
        assert elapsed >= 2.0
