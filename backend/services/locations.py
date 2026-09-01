"""Shared Bangladesh locations and zone mappings.

Single source of truth for geographic coordinates used by solar,
wind, and zone analysis modules.  Every coordinate pair is
``(latitude, longitude)``.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# =========================================================
# BANGLADESH LOCATIONS (9 zones)
# =========================================================

BANGLADESH_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "Dhaka": (23.8103, 90.4125),
    "Chittagong": (22.3569, 91.7832),
    "Khulna": (22.8456, 89.5403),
    "Rajshahi": (24.3745, 88.6042),
    "Comilla": (23.4607, 91.1809),
    "Mymensingh": (24.7471, 90.4203),
    "Sylhet": (24.8949, 91.8687),
    "Barishal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
}

# =========================================================
# ZONE NAMES (ordered list)
# =========================================================

BANGLADESH_ZONES: List[str] = list(BANGLADESH_LOCATIONS.keys())

# =========================================================
# DIVISION → ZONE MAPPING
# =========================================================
#
# Bangladesh has 8 administrative divisions.  Each maps to
# the weather-analysis zone used by solar/wind forecasts.
# The "Mymensingh" zone covers Mymensingh Division.
# =========================================================

DIVISION_TO_ZONE: Dict[str, str] = {
    "Dhaka": "Dhaka",
    "Chittagong": "Chittagong",
    "Khulna": "Khulna",
    "Rajshahi": "Rajshahi",
    "Barishal": "Barishal",
    "Sylhet": "Sylhet",
    "Rangpur": "Rangpur",
    "Mymensingh": "Mymensingh",
}
