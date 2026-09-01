"""Shared utility functions.

Single source of truth for type coercion, validation, and
string-processing helpers used across the backend.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# =========================================================
# BANGLA DIGIT TRANSLATION
# =========================================================

_BANGLA_DIGIT_MAP = str.maketrans(
    "০১২৩৪৫৬৭৮৯",
    "0123456789",
)


def translate_bangla_digits(value: str) -> str:
    """Replace Bangla numeral characters with ASCII digits."""
    if not isinstance(value, str):
        return value
    return value.translate(_BANGLA_DIGIT_MAP)


# =========================================================
# SAFE FLOAT CONVERSION
# =========================================================


def safe_float(value, default: Optional[float] = None) -> Optional[float]:
    """Convert *value* to float, returning *default* on failure.

    Handles None, empty strings, Bangla digits, commas, and
    arbitrary whitespace.
    """
    if value is None:
        return default

    try:
        cleaned = str(value).strip()
        cleaned = translate_bangla_digits(cleaned)
        cleaned = cleaned.replace(",", "")
        return float(cleaned)
    except (TypeError, ValueError):
        return default


# =========================================================
# CLAMP
# =========================================================


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp *value* between *min_val* and *max_val*."""
    return max(min_val, min(value, max_val))


# =========================================================
# TIMESTAMP FORMATTING
# =========================================================

_TIMESTAMP_PATTERNS = (
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
)


def format_timestamp(ts: str) -> Optional[str]:
    """Normalise a timestamp string to ISO-8601 (UTC).

    Returns None if parsing fails.
    """
    if not ts:
        return None

    cleaned = translate_bangla_digits(str(ts)).strip()

    for fmt in _TIMESTAMP_PATTERNS:
        try:
            from datetime import datetime, timezone

            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue

    logger.debug("Unable to parse timestamp: %s", ts)
    return None


# =========================================================
# MW VALIDATION
# =========================================================


def validate_mw(value) -> Optional[float]:
    """Validate a MW value.

    Returns the float if valid and non-negative, else None.
    """
    result = safe_float(value)
    if result is None:
        return None
    if result < 0:
        logger.warning("Negative MW value rejected: %s", value)
        return None
    return result
