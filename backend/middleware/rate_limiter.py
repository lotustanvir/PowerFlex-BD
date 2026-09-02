import logging
import time
import threading
from collections import defaultdict
from typing import Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("powerflex.middleware.rate_limiter")


class _TokenBucket:
    """Simple in-memory token bucket for a single IP."""

    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self) -> tuple:
        """Try to consume a token. Returns (allowed, retry_after_seconds)."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True, 0

            wait_time = (1.0 - self.tokens) / self.rate
            return False, wait_time


class RateLimiter:
    """Per-IP token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self._rate = requests_per_minute / 60.0
        self._capacity = float(requests_per_minute)
        self._buckets: Dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(self._rate, self._capacity)
        )
        self._lock = threading.Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def allow(self, request: Request) -> tuple:
        """Check if request is allowed. Returns (allowed, retry_after)."""
        ip = self._get_client_ip(request)
        with self._lock:
            bucket = self._buckets[ip]
        return bucket.consume()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that applies rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next):
        allowed, retry_after = self.limiter.allow(request)
        if not allowed:
            retry_after_ceil = int(retry_after) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after_ceil)},
            )
        response = await call_next(request)
        return response
