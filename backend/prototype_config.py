"""Centralized PROTOTYPE assumptions for PowerFlex BD.

All values in this module are PLACEHOLDER assumptions for development
and planning purposes. They do NOT represent verified Bangladesh
energy capacity data.

NEVER present these values as official or measured data.
Every consumer must tag outputs with DataProvenance.PROTOTYPE or
DataClassification.PROTOTYPE as appropriate.
"""

# =========================================================
# INSTALLED CAPACITY ASSUMPTIONS (MW)
# =========================================================
# These are rough order-of-magnitude estimates used only for
# optimizer scenario modeling and resource availability defaults.

SOLAR_INSTALLED_MW = 1000.0
"""Prototype solar installed capacity (MW).
Actual Bangladesh utility-scale solar is ~757 MW (as of 2024).
Source: PROTOTYPE — not from verified PGCB/BPDB data."""

WIND_INSTALLED_MW = 500.0
"""Prototype wind installed capacity (MW).
Actual Bangladesh wind capacity is ~62 MW.
Source: PROTOTYPE — not from verified PGCB/BPDB data."""

BATTERY_POWER_MW = 500.0
"""Prototype battery storage power capacity (MW).
Bangladesh has no utility-scale battery storage.
Source: PROTOTYPE — theoretical assumption."""

FLEXIBLE_DEMAND_MW = 500.0
"""Prototype flexible/demand-response capacity (MW).
Bangladesh has no formal demand response program.
Source: PROTOTYPE — theoretical assumption."""

# =========================================================
# OPTIMIZER DEFAULTS
# =========================================================

OPTIMIZER_NUM_ZONES = 9
"""Number of Bangladesh grid zones for optimization."""

# =========================================================
# FORECAST BASE DEMAND (MW)
# =========================================================

BASE_DEMAND_MW = 5500.0
"""Base demand assumption for forecast v2 statistical models.
Used as a fallback when no real demand data is available.
Source: PROTOTYPE — derived from published Bangladesh demand patterns."""

# =========================================================
# CANDIDATE SITE DEFAULTS
# =========================================================

DEFAULT_CANDIDATE_MAX_CAPACITY_MW = 500.0
"""Default maximum capacity for candidate site generation."""
