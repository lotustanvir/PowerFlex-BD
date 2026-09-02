"""Canonical Grid Substation Data for PowerFlex BD.

Single source of truth for Bangladesh grid substations.
All data is marked as UNVERIFIED until authoritative sources
(BPDB/PGCB official grid maps) are obtained.

Key principle: NEVER present unverified data as authoritative.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("powerflex.grid_canonical")


# =========================================================
# DATA CLASSIFICATION
# =========================================================

from backend.data_quality import DataProvenance


class VerificationStatus:
    """Verification status constants."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    ESTIMATE = "ESTIMATE"


# =========================================================
# SUBSTATION DATA MODEL
# =========================================================

@dataclass
class GridSubstation:
    """Canonical grid substation record."""
    name: str
    latitude: float
    longitude: float
    voltage_kv: float
    capacity_mva: Optional[float] = None
    region: str = ""
    
    # Provenance fields
    source: str = "UNKNOWN"
    source_url: str = ""
    verification_status: str = VerificationStatus.UNVERIFIED
    last_verified: str = ""
    data_classification: str = DataProvenance.UNVERIFIED
    
    def to_dict(self):
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "voltage_kv": self.voltage_kv,
            "capacity_mva": self.capacity_mva,
            "region": self.region,
            "source": self.source,
            "source_url": self.source_url,
            "verification_status": self.verification_status,
            "last_verified": self.last_verified,
            "data_classification": self.data_classification,
        }


# =========================================================
# CANONICAL SUBSTATION LIST
# =========================================================
# 
# PROVENANCE NOTE:
# These substations are based on publicly available information
# about Bangladesh major grid infrastructure. However, exact
# coordinates and voltage levels have NOT been verified against
# authoritative BPDB/PGCB sources.
#
# STATUS: ALL UNVERIFIED
# 
# To verify: Obtain official BPDB Grid Map or PGCB transmission
# system documentation.
# =========================================================

BANGLADESH_SUBSTATIONS: List[GridSubstation] = [
    # 400 kV substations
    GridSubstation(
        name="Ghorashal",
        latitude=24.0167,
        longitude=90.9833,
        voltage_kv=400,
        capacity_mva=1200,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Haripur",
        latitude=24.05,
        longitude=90.95,
        voltage_kv=400,
        capacity_mva=800,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Meghnaghat",
        latitude=23.4833,
        longitude=90.55,
        voltage_kv=400,
        capacity_mva=900,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    
    # 230 kV substations
    GridSubstation(
        name="Barcelona",
        latitude=23.75,
        longitude=90.45,
        voltage_kv=230,
        capacity_mva=400,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Aminbazar",
        latitude=23.78,
        longitude=90.35,
        voltage_kv=230,
        capacity_mva=300,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Comilla",
        latitude=23.45,
        longitude=91.2,
        voltage_kv=230,
        capacity_mva=250,
        region="COMILLA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Mymensingh",
        latitude=24.75,
        longitude=90.4,
        voltage_kv=230,
        capacity_mva=200,
        region="MYMENSINGH",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Rajshahi",
        latitude=24.37,
        longitude=88.6,
        voltage_kv=230,
        capacity_mva=300,
        region="RAJSHAHI",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Rangpur",
        latitude=25.75,
        longitude=89.25,
        voltage_kv=230,
        capacity_mva=200,
        region="RANGPUR",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Sylhet",
        latitude=24.9,
        longitude=91.87,
        voltage_kv=230,
        capacity_mva=200,
        region="SYLHET",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Khulna",
        latitude=22.85,
        longitude=89.55,
        voltage_kv=230,
        capacity_mva=250,
        region="KHULNA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Ishwardi",
        latitude=24.13,
        longitude=89.05,
        voltage_kv=230,
        capacity_mva=200,
        region="RAJSHAHI",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    
    # 132 kV substations
    GridSubstation(
        name="Barisal",
        latitude=22.7,
        longitude=90.37,
        voltage_kv=132,
        capacity_mva=150,
        region="BARISHAL",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Cox Bazar",
        latitude=21.45,
        longitude=92.0,
        voltage_kv=132,
        capacity_mva=100,
        region="CHATTOGRAM",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Madaripur",
        latitude=23.17,
        longitude=90.15,
        voltage_kv=132,
        capacity_mva=100,
        region="DHAKA",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Bogra",
        latitude=24.85,
        longitude=89.37,
        voltage_kv=132,
        capacity_mva=150,
        region="RAJSHAHI",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Dinajpur",
        latitude=25.63,
        longitude=88.63,
        voltage_kv=132,
        capacity_mva=100,
        region="RANGPUR",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
    GridSubstation(
        name="Jamalpur",
        latitude=24.93,
        longitude=89.95,
        voltage_kv=132,
        capacity_mva=100,
        region="MYMENSINGH",
        source="PUBLIC_INFO",
        verification_status=VerificationStatus.UNVERIFIED,
        data_classification=DataProvenance.UNVERIFIED,
    ),
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_all_substations() -> List[GridSubstation]:
    """Get all canonical substations."""
    return BANGLADESH_SUBSTATIONS


def get_substation_by_name(name: str) -> Optional[GridSubstation]:
    """Find a substation by name (case-insensitive)."""
    name_lower = name.lower()
    for sub in BANGLADESH_SUBSTATIONS:
        if sub.name.lower() == name_lower:
            return sub
    return None


def get_substations_by_voltage(voltage_kv: float) -> List[GridSubstation]:
    """Get all substations at a specific voltage level."""
    return [s for s in BANGLADESH_SUBSTATIONS if s.voltage_kv == voltage_kv]


def get_substations_by_region(region: str) -> List[GridSubstation]:
    """Get all substations in a specific region."""
    region_lower = region.lower()
    return [s for s in BANGLADESH_SUBSTATIONS if s.region.lower() == region_lower]


def get_provenance_summary() -> dict:
    """Get provenance summary for all substations."""
    total = len(BANGLADESH_SUBSTATIONS)
    verified = sum(1 for s in BANGLADESH_SUBSTATIONS 
                   if s.verification_status == VerificationStatus.VERIFIED)
    unverified = sum(1 for s in BANGLADESH_SUBSTATIONS 
                     if s.verification_status == VerificationStatus.UNVERIFIED)
    estimate = sum(1 for s in BANGLADESH_SUBSTATIONS 
                   if s.verification_status == VerificationStatus.ESTIMATE)
    
    return {
        "total_substations": total,
        "verified": verified,
        "unverified": unverified,
        "estimate": estimate,
        "source": "PUBLIC_INFO",
        "verification_status": "ALL_UNVERIFIED",
        "recommended_action": "Obtain BPDB/PGCB official grid map for verification",
        "data_classification": DataProvenance.UNVERIFIED,
    }


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

# For backward compatibility with existing code
GRID_SUBSTATIONS = [
    {
        "name": s.name,
        "lat": s.latitude,
        "lon": s.longitude,
        "voltage_kv": s.voltage_kv,
    }
    for s in BANGLADESH_SUBSTATIONS
]


if __name__ == "__main__":
    """Print substation summary."""
    print("\n=== Bangladesh Grid Substations ===\n")
    
    summary = get_provenance_summary()
    print(f"Total substations: {summary['total_substations']}")
    print(f"Verified: {summary['verified']}")
    print(f"Unverified: {summary['unverified']}")
    print(f"Estimate: {summary['estimate']}")
    print(f"\nSource: {summary['source']}")
    print(f"Status: {summary['verification_status']}")
    print(f"Action: {summary['recommended_action']}")
    
    print("\nSubstations by voltage:")
    for v in [400, 230, 132]:
        subs = get_substations_by_voltage(v)
        print(f"  {v} kV: {len(subs)} substations")
