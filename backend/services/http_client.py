"""Hardened HTTP client with retries, connection pooling, and timeout defaults.

All external HTTP calls should route through this module to ensure
consistent timeouts, retry behaviour, and error logging.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# =========================================================
# DEFAULTS
# =========================================================

DEFAULT_TIMEOUT = (5, 30, 60)  # connect, read, total
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_STATUS_FORCELIST = (429, 500, 502, 503, 504)


# =========================================================
# SESSION FACTORY
# =========================================================


def _build_session() -> requests.Session:
    """Create a requests.Session with connection pooling and retry."""
    session = requests.Session()

    retry_strategy = Retry(
        total=DEFAULT_MAX_RETRIES,
        backoff_factor=DEFAULT_BACKOFF_FACTOR,
        status_forcelist=DEFAULT_STATUS_FORCELIST,
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update(
        {
            "User-Agent": "PowerFlex-BD/1.0",
            "Accept": "application/json",
        }
    )

    return session


_session = _build_session()


# =========================================================
# CORE FETCH
# =========================================================


def _do_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[tuple] = None,
    retries: Optional[int] = None,
) -> Optional[requests.Response]:
    """Execute a GET request with logging and error handling.

    Returns the Response on success or None on any failure.
    """
    effective_timeout = timeout or DEFAULT_TIMEOUT
    # If caller passes a single number, treat as (connect, read, total)
    if isinstance(effective_timeout, (int, float)):
        effective_timeout = (5, effective_timeout, effective_timeout + 30)

    start = time.monotonic()

    try:
        response = _session.get(
            url,
            params=params,
            timeout=effective_timeout,
        )
        elapsed = round(time.monotonic() - start, 3)

        logger.info(
            "HTTP %s %s -> %s (%.3fs)",
            "GET",
            url,
            response.status_code,
            elapsed,
        )

        if response.status_code >= 400:
            logger.warning(
                "HTTP error %s for %s: %s",
                response.status_code,
                url,
                response.text[:500],
            )
            return None

        return response

    except requests.ConnectionError as error:
        elapsed = round(time.monotonic() - start, 3)
        logger.error(
            "HTTP connection error for %s after %.3fs: %s",
            url,
            elapsed,
            error,
        )
        return None

    except requests.Timeout as error:
        elapsed = round(time.monotonic() - start, 3)
        logger.error(
            "HTTP timeout for %s after %.3fs: %s",
            url,
            elapsed,
            error,
        )
        return None

    except requests.RequestException as error:
        elapsed = round(time.monotonic() - start, 3)
        logger.error(
            "HTTP request error for %s after %.3fs: %s",
            url,
            elapsed,
            error,
        )
        return None


# =========================================================
# PUBLIC API
# =========================================================


def fetch_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[tuple] = None,
    retries: Optional[int] = None,
) -> Optional[Any]:
    """Fetch a URL and return parsed JSON, or None on failure."""
    response = _do_request(
        url,
        params=params,
        timeout=timeout,
        retries=retries,
    )

    if response is None:
        return None

    content_type = response.headers.get("Content-Type", "")

    if "application/json" not in content_type and "text/json" not in content_type:
        logger.warning(
            "Non-JSON content-type '%s' from %s",
            content_type,
            url,
        )
        # Attempt JSON parse anyway — some servers omit the header

    try:
        return response.json()
    except ValueError as error:
        logger.error(
            "JSON decode error from %s: %s",
            url,
            error,
        )
        return None


def fetch_html(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[tuple] = None,
    retries: Optional[int] = None,
) -> Optional[str]:
    """Fetch a URL and return HTML text, or None on failure."""
    response = _do_request(
        url,
        params=params,
        timeout=timeout,
        retries=retries,
    )

    if response is None:
        return None

    content_type = response.headers.get("Content-Type", "")

    if "text/html" not in content_type and "text/plain" not in content_type:
        logger.warning(
            "Non-HTML content-type '%s' from %s",
            content_type,
            url,
        )

    return response.text
