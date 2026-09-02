"""Historical Data Quality Engine for PowerFlex BD.

Provides comprehensive data quality checks, provenance tracking,
and validation for historical demand data.

Key principles:
- NEVER fabricate data
- NEVER convert estimates to REAL
- Preserve data classification at every stage
- Document limitations honestly
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("powerflex.data_quality")

# Bangladesh timezone
BST = timezone(timedelta(hours=6))


# =========================================================
# DATA QUALITY ENUMS
# =========================================================

class DataProvenance:
    """Data provenance constants — classifies data by its origin/source.

    This is distinct from ``data_classification.DataClassification`` which
    classifies data by its official source type (OFFICIAL, MEASURED, FORECAST, etc.).
    """
    REAL_LIVE = "REAL_LIVE"
    REAL_HISTORICAL = "REAL_HISTORICAL"
    USER_PROVIDED = "USER_PROVIDED"
    SYNTHETIC = "SYNTHETIC"
    SIMULATED = "SIMULATED"
    ESTIMATE = "ESTIMATE"
    UNVERIFIED = "UNVERIFIED"
    EMPTY = "EMPTY"


# Backward-compatible alias (deprecated — use DataProvenance directly)
DataClassification = DataProvenance


class QualityStatus:
    """Quality status constants."""
    VERIFIED = "VERIFIED"
    GOOD = "GOOD"
    SUSPICIOUS = "SUSPICIOUS"
    INVALID = "INVALID"
    INTERPOLATED = "INTERPOLATED"
    ESTIMATED = "ESTIMATED"
    UNVERIFIED = "UNVERIFIED"


# =========================================================
# DATA QUALITY REPORT
# =========================================================

@dataclass
class DataQualityReport:
    """Comprehensive data quality report."""
    source: str = "unknown"
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    gap_count: int = 0
    min_timestamp: Optional[str] = None
    max_timestamp: Optional[str] = None
    time_span_hours: Optional[float] = None
    avg_interval_minutes: Optional[float] = None
    issues: List[Dict[str, Any]] = field(default_factory=list)
    classifications: Dict[str, int] = field(default_factory=dict)
    quality_flags: Dict[str, int] = field(default_factory=dict)
    freshness: Optional[str] = None
    age_hours: Optional[float] = None
    completeness: float = 0.0
    accuracy_notes: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "gap_count": self.gap_count,
            "min_timestamp": self.min_timestamp,
            "max_timestamp": self.max_timestamp,
            "time_span_hours": self.time_span_hours,
            "avg_interval_minutes": self.avg_interval_minutes,
            "issues": self.issues,
            "classifications": self.classifications,
            "quality_flags": self.quality_flags,
            "freshness": self.freshness,
            "age_hours": self.age_hours,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }


# =========================================================
# BANGLADESH GRID CONSTRAINTS
# =========================================================

class BangladeshGridConstraints:
    """Known constraints for Bangladesh power grid."""
    
    # Demand bounds (MW) - based on BPDB/PGCB published data
    DEMAND_MIN_MW = 3000  # Minimum recorded demand
    DEMAND_MAX_MW = 20000  # Maximum recorded demand (peak)
    
    # Supply bounds (MW)
    SUPPLY_MIN_MW = 3000
    SUPPLY_MAX_MW = 20000
    
    # Load shedding bounds (MW)
    LOAD_SHEDDING_MIN_MW = 0
    LOAD_SHEDDING_MAX_MW = 8000
    
    # Expected hourly intervals (minutes)
    EXPECTED_INTERVAL_MINUTES = 60
    INTERVAL_TOLERANCE_MINUTES = 30  # Allow 30min tolerance
    
    # Maximum allowed spike (MW change between consecutive readings)
    MAX_DEMAND_SPIKE_MW = 5000  # No more than 5000MW change in 1 hour


# =========================================================
# DATA QUALITY VALIDATOR
# =========================================================

class DataQualityValidator:
    """Comprehensive data quality validation."""
    
    def __init__(self):
        self.constraints = BangladeshGridConstraints()
    
    def validate_demand_record(
        self,
        timestamp_utc: datetime,
        demand_mw: float,
        supply_mw: Optional[float] = None,
        load_shedding_mw: Optional[float] = None,
        data_classification: str = DataProvenance.UNVERIFIED,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate a single demand record. Returns (is_valid, issues)."""
        issues = []
        
        # Check timestamp is timezone-aware
        if timestamp_utc.tzinfo is None:
            issues.append({
                "type": "TIMESTAMP_NAIVE",
                "severity": "ERROR",
                "message": "UTC timestamp must be timezone-aware",
            })
        
        # Check timestamp is not in the future
        now = datetime.now(timezone.utc)
        if timestamp_utc > now + timedelta(hours=1):
            issues.append({
                "type": "FUTURE_TIMESTAMP",
                "severity": "ERROR",
                "message": f"Timestamp is in the future: {timestamp_utc.isoformat()}",
            })
        
        # Check demand is within valid range
        if demand_mw < 0:
            issues.append({
                "type": "NEGATIVE_DEMAND",
                "severity": "ERROR",
                "message": f"Demand cannot be negative: {demand_mw}",
            })
        
        if demand_mw < self.constraints.DEMAND_MIN_MW:
            issues.append({
                "type": "BELOW_MIN_DEMAND",
                "severity": "WARNING",
                "message": f"Demand below minimum expected: {demand_mw} < {self.constraints.DEMAND_MIN_MW}",
            })
        
        if demand_mw > self.constraints.DEMAND_MAX_MW:
            issues.append({
                "type": "ABOVE_MAX_DEMAND",
                "severity": "WARNING",
                "message": f"Demand above maximum expected: {demand_mw} > {self.constraints.DEMAND_MAX_MW}",
            })
        
        # Check supply if provided
        if supply_mw is not None:
            if supply_mw < 0:
                issues.append({
                    "type": "NEGATIVE_SUPPLY",
                    "severity": "ERROR",
                    "message": f"Supply cannot be negative: {supply_mw}",
                })
            
            if supply_mw > self.constraints.SUPPLY_MAX_MW:
                issues.append({
                    "type": "ABOVE_MAX_SUPPLY",
                    "severity": "WARNING",
                    "message": f"Supply above maximum expected: {supply_mw}",
                })
        
        # Check load shedding if provided
        if load_shedding_mw is not None:
            if load_shedding_mw < 0:
                issues.append({
                    "type": "NEGATIVE_LOAD_SHEDDING",
                    "severity": "ERROR",
                    "message": f"Load shedding cannot be negative: {load_shedding_mw}",
                })
            
            if load_shedding_mw > self.constraints.LOAD_SHEDDING_MAX_MW:
                issues.append({
                    "type": "EXCESSIVE_LOAD_SHEDDING",
                    "severity": "WARNING",
                    "message": f"Load shedding above maximum expected: {load_shedding_mw}",
                })
        
        # Check data classification
        valid_classifications = [
            DataProvenance.REAL_LIVE,
            DataProvenance.REAL_HISTORICAL,
            DataProvenance.USER_PROVIDED,
            DataProvenance.SYNTHETIC,
            DataProvenance.SIMULATED,
            DataProvenance.ESTIMATE,
            DataProvenance.UNVERIFIED,
        ]
        if data_classification not in valid_classifications:
            issues.append({
                "type": "INVALID_CLASSIFICATION",
                "severity": "WARNING",
                "message": f"Unknown data classification: {data_classification}",
            })
        
        is_valid = not any(i["severity"] == "ERROR" for i in issues)
        return is_valid, issues
    
    def validate_time_series(
        self,
        records: List[Dict[str, Any]],
        timestamp_key: str = "timestamp_utc",
        demand_key: str = "demand_mw",
    ) -> DataQualityReport:
        """Validate a time series of demand records."""
        report = DataQualityReport()
        
        if not records:
            report.warnings.append("No records to validate")
            return report
        
        report.total_records = len(records)
        
        # Sort by timestamp
        try:
            sorted_records = sorted(records, key=lambda r: r.get(timestamp_key, ""))
        except Exception as e:
            report.warnings.append(f"Could not sort records: {e}")
            sorted_records = records
        
        # Track seen timestamps for duplicates
        seen_timestamps = set()
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0
        classifications = {}
        quality_flags = {}
        
        for record in sorted_records:
            ts = record.get(timestamp_key)
            demand = record.get(demand_key)
            classification = record.get("data_classification", DataProvenance.UNVERIFIED)
            quality_flag = record.get("quality_flag", QualityStatus.UNVERIFIED)
            
            # Count classifications
            classifications[classification] = classifications.get(classification, 0) + 1
            
            # Count quality flags
            quality_flags[quality_flag] = quality_flags.get(quality_flag, 0) + 1
            
            # Check for duplicates
            if ts in seen_timestamps:
                duplicate_count += 1
                report.issues.append({
                    "type": "DUPLICATE",
                    "timestamp": ts,
                    "severity": "WARNING",
                })
                continue
            seen_timestamps.add(ts)
            
            # Validate individual record
            try:
                if isinstance(ts, str):
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    ts_dt = ts
                
                if demand is not None:
                    is_valid, issues = self.validate_demand_record(
                        timestamp_utc=ts_dt,
                        demand_mw=float(demand),
                        data_classification=classification,
                    )
                    
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        report.issues.extend(issues)
                else:
                    invalid_count += 1
                    report.issues.append({
                        "type": "MISSING_DEMAND",
                        "timestamp": ts,
                        "severity": "ERROR",
                    })
                    
            except Exception as e:
                invalid_count += 1
                report.issues.append({
                    "type": "PARSE_ERROR",
                    "timestamp": ts,
                    "severity": "ERROR",
                    "message": str(e),
                })
        
        report.valid_records = valid_count
        report.invalid_records = invalid_count
        report.duplicate_records = duplicate_count
        report.classifications = classifications
        report.quality_flags = quality_flags
        
        # Calculate time span
        if len(sorted_records) >= 2:
            try:
                first_ts = sorted_records[0].get(timestamp_key)
                last_ts = sorted_records[-1].get(timestamp_key)
                
                if isinstance(first_ts, str):
                    first_dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
                else:
                    first_dt = first_ts
                    
                if isinstance(last_ts, str):
                    last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                else:
                    last_dt = last_ts
                
                report.min_timestamp = first_ts
                report.max_timestamp = last_ts
                
                span = last_dt - first_dt
                report.time_span_hours = span.total_seconds() / 3600
                
                # Calculate average interval
                if len(sorted_records) > 1:
                    total_interval = 0
                    interval_count = 0
                    for i in range(1, len(sorted_records)):
                        try:
                            ts1 = sorted_records[i-1].get(timestamp_key)
                            ts2 = sorted_records[i].get(timestamp_key)
                            
                            if isinstance(ts1, str):
                                dt1 = datetime.fromisoformat(ts1.replace("Z", "+00:00"))
                            else:
                                dt1 = ts1
                                
                            if isinstance(ts2, str):
                                dt2 = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
                            else:
                                dt2 = ts2
                            
                            interval = (dt2 - dt1).total_seconds() / 60
                            total_interval += interval
                            interval_count += 1
                        except (ValueError, TypeError, AttributeError):
                            pass
                    
                    if interval_count > 0:
                        report.avg_interval_minutes = total_interval / interval_count
                
            except Exception as e:
                report.warnings.append(f"Could not calculate time span: {e}")
        
        # Detect gaps
        report.gap_count = self._detect_gap_count(sorted_records, timestamp_key)
        
        # Assess freshness
        self._assess_freshness(report, sorted_records, timestamp_key)
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        return report
    
    def _detect_gap_count(
        self,
        sorted_records: List[Dict[str, Any]],
        timestamp_key: str,
    ) -> int:
        """Detect number of gaps in time series."""
        if len(sorted_records) < 2:
            return 0
        
        gap_count = 0
        expected_interval = self.constraints.EXPECTED_INTERVAL_MINUTES
        tolerance = self.constraints.INTERVAL_TOLERANCE_MINUTES
        
        for i in range(1, len(sorted_records)):
            try:
                ts1 = sorted_records[i-1].get(timestamp_key)
                ts2 = sorted_records[i].get(timestamp_key)
                
                if isinstance(ts1, str):
                    dt1 = datetime.fromisoformat(ts1.replace("Z", "+00:00"))
                else:
                    dt1 = ts1
                    
                if isinstance(ts2, str):
                    dt2 = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
                else:
                    dt2 = ts2
                
                interval_minutes = (dt2 - dt1).total_seconds() / 60
                
                if interval_minutes > expected_interval + tolerance:
                    gap_count += 1
            except (ValueError, TypeError, AttributeError):
                pass
        
        return gap_count
    
    def _assess_freshness(
        self,
        report: DataQualityReport,
        sorted_records: List[Dict[str, Any]],
        timestamp_key: str,
    ) -> None:
        """Assess data freshness."""
        if not sorted_records:
            report.freshness = "UNAVAILABLE"
            return
        
        try:
            last_ts = sorted_records[-1].get(timestamp_key)
            if isinstance(last_ts, str):
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = last_ts
            
            now = datetime.now(timezone.utc)
            age = now - last_dt
            report.age_hours = age.total_seconds() / 3600
            
            if report.age_hours < 1:
                report.freshness = "FRESH"
            elif report.age_hours < 6:
                report.freshness = "RECENT"
            elif report.age_hours < 24:
                report.freshness = "STALE"
            else:
                report.freshness = "OLD"
                
        except Exception as e:
            report.freshness = "UNKNOWN"
            report.warnings.append(f"Could not assess freshness: {e}")
    
    def _generate_recommendations(self, report: DataQualityReport) -> None:
        """Generate recommendations based on quality report."""
        
        # Check for insufficient data
        if report.total_records < 100:
            report.recommendations.append(
                f"INSUFFICIENT_DATA: Only {report.total_records} records. "
                f"Need at least 100 for basic ML training."
            )
        
        if report.total_records < 8760:  # 1 year hourly
            report.recommendations.append(
                f"LIMITED_DATA: {report.total_records} records. "
                f"Need ~8760 for one year of hourly data."
            )
        
        # Check for duplicates
        if report.duplicate_records > 0:
            report.recommendations.append(
                f"DUPLICATES: {report.duplicate_records} duplicate timestamps found. "
                f"Consider deduplication."
            )
        
        # Check for gaps
        if report.gap_count > 0:
            report.recommendations.append(
                f"GAPS: {report.gap_count} time gaps detected. "
                f"Data continuity is important for time series analysis."
            )
        
        # Check for synthetic data
        synthetic_count = report.classifications.get(DataProvenance.SYNTHETIC, 0)
        if synthetic_count > 0:
            report.warnings.append(
                f"SYNTHETIC_DATA: {synthetic_count} records are synthetic. "
                f"Synthetic data must NOT be used for production forecasting."
            )
        
        # Check freshness
        if report.freshness == "OLD":
            report.recommendations.append(
                f"STALE_DATA: Data is {report.age_hours:.1f} hours old. "
                f"Consider collecting more recent observations."
            )
        
        # Check data classification
        unverified_count = report.classifications.get(DataProvenance.UNVERIFIED, 0)
        if unverified_count > 0:
            report.recommendations.append(
                f"UNVERIFIED_DATA: {unverified_count} records are unverified. "
                f"Verify data source and classification."
            )


# =========================================================
# PROVENANCE TRACKER
# =========================================================

class ProvenanceTracker:
    """Track data provenance through the pipeline."""
    
    @staticmethod
    def create_provenance_record(
        source: str,
        source_url: str,
        classification: str,
        quality_status: str,
        retrieved_at: Optional[datetime] = None,
        timezone_str: str = "Asia/Dhaka",
        limitations: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a provenance record for data."""
        return {
            "source": source,
            "source_url": source_url,
            "data_classification": classification,
            "quality_status": quality_status,
            "retrieved_at": (retrieved_at or datetime.now(timezone.utc)).isoformat(),
            "timezone": timezone_str,
            "limitations": limitations,
            "verified_at": None,
            "verified_by": None,
        }
    
    @staticmethod
    def merge_provenance(
        parent_provenance: Dict[str, Any],
        child_classification: str,
        child_quality: str,
        transformation: str,
    ) -> Dict[str, Any]:
        """Merge parent provenance with child transformation."""
        return {
            "parent_source": parent_provenance.get("source"),
            "parent_classification": parent_provenance.get("data_classification"),
            "transformation": transformation,
            "child_classification": child_classification,
            "child_quality": child_quality,
            "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
        }


# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================

def assess_pgcb_data_quality() -> DataQualityReport:
    """Assess quality of PGCB demand history data."""
    from pathlib import Path
    import csv
    
    csv_path = Path(__file__).resolve().parents[1] / "data" / "pgcb_demand_history.csv"
    
    if not csv_path.exists():
        report = DataQualityReport()
        report.warnings.append("PGCB demand history file not found")
        return report
    
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    validator = DataQualityValidator()
    return validator.validate_time_series(records)


if __name__ == "__main__":
    """Run quality assessment on existing data."""
    logging.basicConfig(level=logging.INFO)
    
    report = assess_pgcb_data_quality()
    
    print("\n=== PGCB Data Quality Report ===\n")
    print(f"Total records: {report.total_records}")
    print(f"Valid records: {report.valid_records}")
    print(f"Invalid records: {report.invalid_records}")
    print(f"Duplicate records: {report.duplicate_records}")
    print(f"Time span: {report.time_span_hours:.1f} hours")
    print(f"Avg interval: {report.avg_interval_minutes:.1f} minutes")
    print(f"Freshness: {report.freshness}")
    print(f"Age: {report.age_hours:.1f} hours")
    
    print("\nClassifications:")
    for k, v in report.classifications.items():
        print(f"  {k}: {v}")
    
    print("\nQuality Flags:")
    for k, v in report.quality_flags.items():
        print(f"  {k}: {v}")
    
    if report.issues:
        print(f"\nIssues ({len(report.issues)}):")
        for issue in report.issues[:10]:
            print(f"  - {issue.get('type')}: {issue.get('message', '')}")
    
    if report.warnings:
        print(f"\nWarnings ({len(report.warnings)}):")
        for warning in report.warnings:
            print(f"  - {warning}")
    
    if report.recommendations:
        print(f"\nRecommendations ({len(report.recommendations)}):")
        for rec in report.recommendations:
            print(f"  - {rec}")


# =========================================================
# GRID QUALITY ASSESSMENT
# =========================================================

@dataclass
class SimpleQualityReport:
    """Simple quality report matching test expectations."""
    source: str = "unknown"
    freshness: str = "UNKNOWN"
    completeness: float = 0.0
    accuracy_notes: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "freshness": self.freshness,
            "completeness": self.completeness,
            "accuracy_notes": self.accuracy_notes,
            "timestamp": self.timestamp,
        }


def assess_grid_quality(data: Optional[Dict[str, Any]] = None) -> SimpleQualityReport:
    """Assess quality of grid data.
    
    Args:
        data: Grid data dictionary with timestamp, demand, supply, etc.
        
    Returns:
        SimpleQualityReport with freshness, completeness, and accuracy notes.
    """
    if data is None:
        return SimpleQualityReport(
            source="grid",
            freshness="UNKNOWN",
            completeness=0.0,
            accuracy_notes=["No data provided"],
        )
    
    report = SimpleQualityReport(source="grid")
    
    # Check freshness
    timestamp_str = data.get("timestamp")
    if timestamp_str:
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - ts).total_seconds() / 3600
            
            if age_hours < 2:
                report.freshness = "FRESH"
            elif age_hours < 6:
                report.freshness = "RECENT"
            else:
                report.freshness = "STALE"
        except (ValueError, TypeError):
            report.freshness = "UNKNOWN"
    
    # Check completeness
    required_fields = [
        "current_demand_mw",
        "supply_mw",
        "load_shedding_mw",
        "generation_breakdown",
        "imports",
    ]
    
    present_fields = sum(1 for f in required_fields if f in data)
    report.completeness = present_fields / len(required_fields)
    
    # Add accuracy notes
    missing = [f for f in required_fields if f not in data]
    if missing:
        report.accuracy_notes.append(f"Missing fields: {', '.join(missing)}")
    
    if data.get("current_demand_mw") is None:
        report.accuracy_notes.append("Missing demand data")
    
    return report


# =========================================================
# SOLAR QUALITY ASSESSMENT
# =========================================================

def assess_solar_quality(data: Optional[Dict[str, Any]] = None) -> SimpleQualityReport:
    """Assess quality of solar data.
    
    Args:
        data: Solar data dictionary with hourly_data and zones_succeeded.
        
    Returns:
        SimpleQualityReport with freshness, completeness, and accuracy notes.
    """
    if data is None:
        return SimpleQualityReport(
            source="solar",
            freshness="UNKNOWN",
            completeness=0.0,
            accuracy_notes=["No data provided"],
        )
    
    report = SimpleQualityReport(source="solar")
    
    # Check if we have hourly data
    hourly_data = data.get("hourly_data", [])
    zones_succeeded = data.get("zones_succeeded", 0)
    total_zones = 9  # Expected number of zones
    
    if hourly_data:
        report.freshness = "FRESH"
        report.completeness = 1.0
    else:
        report.freshness = "UNKNOWN"
        report.completeness = 0.0
    
    # Check zone completion
    if zones_succeeded < total_zones:
        failed_zones = total_zones - zones_succeeded
        report.accuracy_notes.append(f"{failed_zones} zones failed")
    
    return report


# =========================================================
# WIND QUALITY ASSESSMENT
# =========================================================

def assess_wind_quality(data: Optional[Dict[str, Any]] = None) -> SimpleQualityReport:
    """Assess quality of wind data.
    
    Args:
        data: Wind data dictionary with hourly_data and zones_succeeded.
        
    Returns:
        SimpleQualityReport with freshness, completeness, and accuracy notes.
    """
    if data is None:
        return SimpleQualityReport(
            source="wind",
            freshness="UNKNOWN",
            completeness=0.0,
            accuracy_notes=["No data provided"],
        )
    
    report = SimpleQualityReport(source="wind")
    
    # Check if we have hourly data
    hourly_data = data.get("hourly_data", [])
    zones_succeeded = data.get("zones_succeeded", 0)
    total_zones = 9  # Expected number of zones
    
    if hourly_data:
        report.freshness = "FRESH"
        report.completeness = 1.0
    else:
        report.freshness = "UNKNOWN"
        report.completeness = 0.0
    
    # Check zone completion
    if zones_succeeded < total_zones:
        failed_zones = total_zones - zones_succeeded
        report.accuracy_notes.append(f"{failed_zones} zones failed")
    
    return report


# =========================================================
# COMPREHENSIVE QUALITY REPORT
# =========================================================

def generate_quality_report(
    grid_data: Optional[Dict[str, Any]] = None,
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
    biomass_data: Optional[Dict[str, Any]] = None,
    waste_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a comprehensive data quality report.
    
    Args:
        grid_data: Grid data dictionary
        solar_data: Solar data dictionary
        wind_data: Wind data dictionary
        biomass_data: Biomass data dictionary
        waste_data: Waste data dictionary
        
    Returns:
        Dictionary with quality reports for all data sources.
    """
    grid_report = assess_grid_quality(grid_data)
    solar_report = assess_solar_quality(solar_data)
    wind_report = assess_wind_quality(wind_data)
    
    # Simple reports for biomass and waste
    biomass_report = SimpleQualityReport(
        source="biomass",
        freshness="FRESH" if biomass_data else "UNKNOWN",
        completeness=1.0 if biomass_data else 0.0,
    )
    
    waste_report = SimpleQualityReport(
        source="waste",
        freshness="FRESH" if waste_data else "UNKNOWN",
        completeness=1.0 if waste_data else 0.0,
    )
    
    # Calculate overall metrics
    reports = [grid_report, solar_report, wind_report, biomass_report, waste_report]
    
    freshness_values = [r.freshness for r in reports]
    if all(f == "FRESH" for f in freshness_values):
        overall_freshness = "FRESH"
    elif any(f == "FRESH" for f in freshness_values):
        overall_freshness = "PARTIAL"
    elif any(f in ["RECENT", "STALE"] for f in freshness_values):
        overall_freshness = "STALE"
    else:
        overall_freshness = "STALE"
    
    overall_completeness = sum(r.completeness for r in reports) / len(reports)
    
    return {
        "overall_freshness": overall_freshness,
        "overall_completeness": round(overall_completeness, 2),
        "sources": {
            "grid": grid_report.to_dict(),
            "solar": solar_report.to_dict(),
            "wind": wind_report.to_dict(),
            "biomass": biomass_report.to_dict(),
            "waste": waste_report.to_dict(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
