import time
import threading
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware.rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    _TokenBucket,
)
from backend.grid import validate_pgcb_response, detect_stale_data


# =========================================================
# RATE LIMITER TESTS
# =========================================================

class TestTokenBucket:

    def test_allows_first_request(self):
        bucket = _TokenBucket(rate=1.0, capacity=3)
        allowed, retry_after = bucket.consume()
        assert allowed is True
        assert retry_after == 0

    def test_allows_up_to_capacity(self):
        bucket = _TokenBucket(rate=1.0, capacity=2)
        assert bucket.consume()[0] is True
        assert bucket.consume()[0] is True

    def test_blocks_when_exhausted(self):
        bucket = _TokenBucket(rate=1.0, capacity=1)
        assert bucket.consume()[0] is True
        allowed, retry_after = bucket.consume()
        assert allowed is False
        assert retry_after > 0

    def test_refills_over_time(self):
        bucket = _TokenBucket(rate=10.0, capacity=2)
        assert bucket.consume()[0] is True
        assert bucket.consume()[0] is True
        assert bucket.consume()[0] is False
        time.sleep(0.3)
        allowed, _ = bucket.consume()
        assert allowed is True


class TestRateLimiter:

    def test_allows_within_limit(self):
        limiter = RateLimiter(requests_per_minute=10)
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "1.2.3.4"

        for _ in range(5):
            allowed, _ = limiter.allow(mock_request)
            assert allowed is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(requests_per_minute=3)
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "1.2.3.4"

        assert limiter.allow(mock_request)[0] is True
        assert limiter.allow(mock_request)[0] is True
        assert limiter.allow(mock_request)[0] is True
        assert limiter.allow(mock_request)[0] is False

    def test_per_ip_isolation(self):
        limiter = RateLimiter(requests_per_minute=2)

        req1 = MagicMock()
        req1.headers = {}
        req1.client = MagicMock()
        req1.client.host = "10.0.0.1"

        req2 = MagicMock()
        req2.headers = {}
        req2.client = MagicMock()
        req2.client.host = "10.0.0.2"

        assert limiter.allow(req1)[0] is True
        assert limiter.allow(req1)[0] is True
        assert limiter.allow(req1)[0] is False

        assert limiter.allow(req2)[0] is True
        assert limiter.allow(req2)[0] is True

    def test_forwarded_for_header(self):
        limiter = RateLimiter(requests_per_minute=1)
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        assert limiter.allow(mock_request)[0] is True
        assert limiter.allow(mock_request)[0] is False


# =========================================================
# RATE LIMIT MIDDLEWARE INTEGRATION TESTS
# =========================================================

def _make_app(rpm: int = 3) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rpm)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    return app


class TestRateLimitMiddleware:

    def test_allows_requests_within_limit(self):
        app = _make_app(rpm=5)
        client = TestClient(app)

        for _ in range(3):
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_blocks_requests_over_limit(self):
        app = _make_app(rpm=2)
        client = TestClient(app)

        assert client.get("/test").status_code == 200
        assert client.get("/test").status_code == 200

        resp = client.get("/test")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) >= 1

    def test_response_body_on_429(self):
        app = _make_app(rpm=1)
        client = TestClient(app)

        client.get("/test")
        resp = client.get("/test")
        assert resp.status_code == 429
        assert resp.json() == {"detail": "Rate limit exceeded"}


# =========================================================
# PGCB RESPONSE VALIDATION TESTS
# =========================================================

class TestValidatePgcbResponse:

    def test_valid_html_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_resp.text = "<html><body><table><tr><td>data</td></tr></table></body></html>"
        mock_resp.content = b"<html><body><table><tr><td>data</td></tr></table></body></html>"

        assert validate_pgcb_response(mock_resp) is None

    def test_non_200_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.headers = {"Content-Type": "text/html"}

        result = validate_pgcb_response(mock_resp)
        assert "500" in result

    def test_non_html_content_type(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}

        result = validate_pgcb_response(mock_resp)
        assert "Content-Type" in result

    def test_no_table_in_html(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.text = "<html><body><p>No tables here</p></body></html>"
        mock_resp.content = b"<html><body><p>No tables here</p></body></html>"

        result = validate_pgcb_response(mock_resp)
        assert "table" in result.lower()

    def test_response_too_large_by_content_length(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {
            "Content-Type": "text/html",
            "Content-Length": str(6 * 1024 * 1024),
        }
        mock_resp.text = "<html><body><table></table></body></html>"
        mock_resp.content = b"x" * 100

        result = validate_pgcb_response(mock_resp)
        assert "large" in result.lower()


# =========================================================
# STALE DATA DETECTION TESTS
# =========================================================

class TestDetectStaleData:

    def test_fresh_data_returns_false(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        assert detect_stale_data(now) is False

    def test_old_data_returns_true(self):
        from datetime import datetime, timedelta, timezone
        old = datetime.now(timezone.utc) - timedelta(hours=5)
        assert detect_stale_data(old.strftime("%Y-%m-%d %H:%M:%S")) is True

    def test_empty_string_returns_false(self):
        assert detect_stale_data("") is False

    def test_unparseable_string_returns_false(self):
        assert detect_stale_data("not-a-date") is False

    def test_borderline_2_hours(self):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        just_under = (now - timedelta(hours=1, minutes=59)).strftime("%Y-%m-%d %H:%M:%S")
        assert detect_stale_data(just_under) is False

        just_over = (now - timedelta(hours=2, minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        assert detect_stale_data(just_over) is True
