import time
from collections import defaultdict, deque
from threading import Lock


class SlidingRateLimiter:
    """Simple in-memory rate limiter for per-key request throttling."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            bucket = self._history[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.time()
        with self._lock:
            bucket = self._history[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            return max(0, self.max_requests - len(bucket))
