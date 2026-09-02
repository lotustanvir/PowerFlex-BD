"""Authentication & Security Middleware for PowerFlex BD.

Provides API key validation, rate limiting, security headers,
and request logging for production deployment.
"""

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("powerflex.security")


# =========================================================
# API KEY MANAGEMENT
# =========================================================

def get_api_keys() -> Dict[str, str]:
    """Load API keys from environment variables.
    
    Format: POWERFLEX_API_KEYS="key1:name1,key2:name2"
    """
    raw = os.getenv("POWERFLEX_API_KEYS", "")
    if not raw:
        return {}

    keys = {}
    for pair in raw.split(","):
        parts = pair.strip().split(":")
        if len(parts) == 2:
            keys[parts[0]] = parts[1]
    return keys


def validate_api_key(api_key: str) -> Optional[str]:
    """Validate an API key using constant-time comparison.

    Returns key name if valid, None otherwise.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    valid_keys = get_api_keys()
    for key, name in valid_keys.items():
        if hmac.compare_digest(api_key, key):
            return name
    return None


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# =========================================================
# RATE LIMITER
# =========================================================

class RateLimiter:
    """Token bucket rate limiter per API key or IP."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.rpm = requests_per_minute
        self.burst = burst_size
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"tokens": burst_size, "last_refill": time.time()}
        )

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed under the rate limit."""
        bucket = self._buckets[key]
        now = time.time()
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (self.rpm / 60)
        bucket["tokens"] = min(self.burst, bucket["tokens"] + refill)
        bucket["last_refill"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        bucket = self._buckets[key]
        return int(bucket["tokens"])


# =========================================================
# SECURITY MIDDLEWARE
# =========================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """Adds security headers and rate limiting."""

    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        require_api_key: bool = False,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.require_api_key = require_api_key
        self._request_log: list = []

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Rate limiting
        rate_key = client_ip
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            rate_key = f"apikey:{api_key}"

        if not self.rate_limiter.is_allowed(rate_key):
            logger.warning("Rate limit exceeded for %s", rate_key)
            return Response(
                content='{"error": "Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
            )

        # API key validation
        if self.require_api_key and api_key:
            key_name = validate_api_key(api_key)
            if not key_name:
                logger.warning("Invalid API key from %s", client_ip)
                return Response(
                    content='{"error": "Invalid API key"}',
                    status_code=401,
                    media_type="application/json",
                )
            request.state.key_name = key_name

        # Process request
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Request logging
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "remaining_rate": self.rate_limiter.get_remaining(rate_key),
        }
        self._request_log.append(log_entry)
        if len(self._request_log) > 1000:
            self._request_log = self._request_log[-500:]

        if duration_ms > 5000:
            logger.warning("Slow request: %s %s took %.0fms", request.method, request.url.path, duration_ms)

        return response

    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        if not self._request_log:
            return {"total_requests": 0, "avg_duration_ms": 0}

        durations = [r["duration_ms"] for r in self._request_log]
        status_counts = defaultdict(int)
        for r in self._request_log:
            status_counts[str(r["status"])] += 1

        return {
            "total_requests": len(self._request_log),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "status_distribution": dict(status_counts),
            "last_10": self._request_log[-10:],
        }


# =========================================================
# CORS CONFIGURATION
# =========================================================

def get_cors_origins() -> list:
    """Get allowed CORS origins from environment."""
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


# =========================================================
# TRUSTED HOSTS
# =========================================================

def get_trusted_hosts() -> list:
    """Get trusted host names from environment."""
    raw = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
    return [h.strip() for h in raw.split(",") if h.strip()]
