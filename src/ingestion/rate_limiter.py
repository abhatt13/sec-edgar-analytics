"""Rate limiter for SEC API requests."""

import time
from collections import deque
from typing import Deque


class RateLimiter:
    """Token bucket rate limiter for SEC API compliance.

    SEC requires no more than 10 requests per second.
    """

    def __init__(self, requests_per_second: int = 10) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum number of requests allowed per second
        """
        self.requests_per_second = requests_per_second
        self.time_window = 1.0  # 1 second window
        self.request_times: Deque[float] = deque()

    def acquire(self) -> None:
        """Acquire permission to make a request.

        Blocks until a request slot is available within the rate limit.
        """
        current_time = time.time()

        # Remove requests outside the time window
        while self.request_times and current_time - self.request_times[0] >= self.time_window:
            self.request_times.popleft()

        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_second:
            sleep_time = self.time_window - (current_time - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            # Remove the oldest request after sleeping
            self.request_times.popleft()

        # Record this request
        self.request_times.append(time.time())

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.request_times.clear()

    def get_current_rate(self) -> float:
        """Get current request rate (requests per second).

        Returns:
            Current request rate
        """
        current_time = time.time()

        # Remove requests outside the time window
        while self.request_times and current_time - self.request_times[0] >= self.time_window:
            self.request_times.popleft()

        return len(self.request_times) / self.time_window if self.request_times else 0.0
