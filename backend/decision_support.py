"""Decision Support Service for PowerFlex BD.

Unified recommendation engine that aggregates verified energy-system
signals into actionable guidance. All recommendations are:
- Rule-based (not ML predictions)
- Transparent with explicit source typing
- Confidence-scored with provenance
- Deduplicated to avoid repeated same recommendations
- Gracefully degraded when inputs fail

Data Classification:
- Recommendations use RULE_BASED, HISTORICAL_ANALYSIS, SYSTEM_STATUS source types
- Never labeled as AI/ML predictions unless backed by verified ML model
- Every recommendation includes source classification and confidence
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.data_classification import DataClassification

logger = logging.getLogger("powerflex.decision_support")


# ============================================================
# RECOMMENDATION TYPES AND ENUMS
# ============================================================

class RecommendationType(str, Enum):
    """Types of recommendations the system can generate."""
    SUPPLY_DEFICIT = "SUPPLY_DEFICIT"
    RENEWABLE_OPPORTUNITY = "RENEWABLE_OPPORTUNITY"
    IMPORT_DEPENDENCY = "IMPORT_DEPENDENCY"
    HIGH_GRID_RISK = "HIGH_GRID_RISK"
    DATA_QUALITY_DEGRADATION = "DATA_QUALITY_DEGRADATION"
    FORECAST_UNAVAILABLE = "FORECAST_UNAVAILABLE"
    DEMAND_PEAK_APPROACHING = "DEMAND_PEAK_APPROACHING"
    ZONE_ALERT = "ZONE_ALERT"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class SourceType(str, Enum):
    """Source type classification for recommendations."""
    RULE_BASED = "RULE_BASED"
    HISTORICAL_ANALYSIS = "HISTORICAL_ANALYSIS"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    FORECAST = "FORECAST"
    SIMULATION = "SIMULATION"
    MODEL_BASED = "MODEL_BASED"


class DataStatus(str, Enum):
    """Status of data used in the recommendation."""
    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"
    CACHED = "CACHED"
    ESTIMATED = "ESTIMATED"
    MODELED = "MODELED"
    SYNTHETIC = "SYNTHETIC"
    UNAVAILABLE = "UNAVAILABLE"


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class RecommendationEvidence:
    """Evidence supporting a specific recommendation."""
    trigger: str
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    source_data_classification: Optional[DataClassification] = None
    source_type: SourceType = SourceType.RULE_BASED
    data_status: DataStatus = DataStatus.LIVE
    data_freshness_seconds: Optional[float] = None
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "source_data_classification": (
                self.source_data_classification.value
                if self.source_data_classification
                else None
            ),
            "source_type": self.source_type.value,
            "data_status": self.data_status.value,
            "data_freshness_seconds": self.data_freshness_seconds,
            "explanation": self.explanation,
        }


@dataclass
class Recommendation:
    """A single recommendation with full provenance."""
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    summary: str
    detailed_explanation: str
    evidence: RecommendationEvidence
    expected_impact: str
    confidence: float = 0.0
    timestamp: str = ""
    deduplication_key: str = ""
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "summary": self.summary,
            "detailed_explanation": self.detailed_explanation,
            "evidence": self.evidence.to_dict(),
            "expected_impact": self.expected_impact,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "deduplication_key": self.deduplication_key,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }


@dataclass
class SystemInputs:
    """Collected system inputs for recommendation generation."""
    # Grid data
    grid_demand_mw: Optional[float] = None
    grid_supply_mw: Optional[float] = None
    grid_status: str = "UNKNOWN"
    grid_data_classification: DataClassification = DataClassification.DATA_UNAVAILABLE
    grid_timestamp: Optional[str] = None

    # Renewable data
    solar_generation_mw: Optional[float] = None
    wind_generation_mw: Optional[float] = None
    solar_data_classification: DataClassification = DataClassification.DATA_UNAVAILABLE
    wind_data_classification: DataClassification = DataClassification.DATA_UNAVAILABLE

    # Risk data
    risk_score: Optional[float] = None
    risk_level: str = "UNKNOWN"

    # Forecast data
    forecast_available: bool = False
    forecast_peak_mw: Optional[float] = None
    forecast_confidence: Optional[float] = None

    # Data quality
    independent_observations: int = 0
    forecast_ready: bool = False
    data_quality_issues: List[str] = field(default_factory=list)

    # Missing inputs tracking
    missing_inputs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grid_demand_mw": self.grid_demand_mw,
            "grid_supply_mw": self.grid_supply_mw,
            "grid_status": self.grid_status,
            "grid_data_classification": self.grid_data_classification.value,
            "grid_timestamp": self.grid_timestamp,
            "solar_generation_mw": self.solar_generation_mw,
            "wind_generation_mw": self.wind_generation_mw,
            "solar_data_classification": self.solar_data_classification.value,
            "wind_data_classification": self.wind_data_classification.value,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "forecast_available": self.forecast_available,
            "forecast_peak_mw": self.forecast_peak_mw,
            "forecast_confidence": self.forecast_confidence,
            "independent_observations": self.independent_observations,
            "forecast_ready": self.forecast_ready,
            "data_quality_issues": self.data_quality_issues,
            "missing_inputs": self.missing_inputs,
        }


# ============================================================
# CONFIDENCE SCORING
# ============================================================

def calculate_confidence_score(
    data_freshness_seconds: Optional[float],
    source_reliability: float,
    input_completeness: float,
    calculation_stability: float,
    forecast_available: bool,
) -> float:
    """Calculate confidence score based on multiple factors.
    
    Args:
        data_freshness_seconds: How fresh the data is (lower = better)
        source_reliability: 0-1 scale of source reliability
        input_completeness: 0-1 scale of input completeness
        calculation_stability: 0-1 scale of calculation stability
        forecast_available: Whether forecast data is available
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Freshness score (0-1, decays over time)
    if data_freshness_seconds is not None:
        if data_freshness_seconds < 300:  # < 5 minutes
            freshness_score = 1.0
        elif data_freshness_seconds < 1800:  # < 30 minutes
            freshness_score = 0.9
        elif data_freshness_seconds < 3600:  # < 1 hour
            freshness_score = 0.7
        elif data_freshness_seconds < 7200:  # < 2 hours
            freshness_score = 0.5
        else:
            freshness_score = 0.3
    else:
        freshness_score = 0.5  # Unknown freshness

    # Forecast bonus
    forecast_bonus = 0.1 if forecast_available else 0.0

    # Weighted average
    confidence = (
        freshness_score * 0.3
        + source_reliability * 0.25
        + input_completeness * 0.25
        + calculation_stability * 0.1
        + forecast_bonus
    )

    return round(min(max(confidence, 0.0), 1.0), 2)


# ============================================================
# DEDUPLICATION
# ============================================================

class RecommendationDeduplicator:
    """Track recommendations to avoid repeating the same ones."""
    
    def __init__(self, cooldown_seconds: int = 1800):
        """Initialize with cooldown period.
        
        Args:
            cooldown_seconds: How long to suppress duplicate recommendations
        """
        self.cooldown_seconds = cooldown_seconds
        self._recent: Dict[str, datetime] = {}
    
    def _make_fingerprint(self, rec: Recommendation) -> str:
        """Create a fingerprint for deduplication.
        
        Fingerprint based on: recommendation type + key conditions.
        """
        # Extract key conditions from evidence
        evidence_key = f"{rec.type.value}:{rec.evidence.trigger}"
        return hashlib.sha256(evidence_key.encode()).hexdigest()[:16]
    
    def is_duplicate(self, rec: Recommendation) -> bool:
        """Check if this recommendation is a duplicate within cooldown."""
        fingerprint = self._make_fingerprint(rec)
        rec.deduplication_key = fingerprint
        
        if fingerprint in self._recent:
            last_seen = self._recent[fingerprint]
            now = datetime.now(timezone.utc)
            if (now - last_seen).total_seconds() < self.cooldown_seconds:
                return True
        
        return False
    
    def register(self, rec: Recommendation) -> None:
        """Register a recommendation as seen."""
        fingerprint = self._make_fingerprint(rec)
        self._recent[fingerprint] = datetime.now(timezone.utc)
    
    def cleanup(self) -> int:
        """Remove expired entries. Returns count removed."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.cooldown_seconds)
        expired = [
            k for k, v in self._recent.items()
            if v < cutoff
        ]
        for k in expired:
            del self._recent[k]
        return len(expired)


# Global deduplicator instance
_deduplicator = RecommendationDeduplicator()


# ============================================================
# RULE EVALUATION ENGINE
# ============================================================

def evaluate_supply_deficit(inputs: SystemInputs) -> Optional[Recommendation]:
    """Evaluate supply deficit rule."""
    if inputs.grid_demand_mw is None or inputs.grid_supply_mw is None:
        return None

    deficit_mw = inputs.grid_demand_mw - inputs.grid_supply_mw
    if deficit_mw <= 0:
        return None

    # Calculate severity
    deficit_ratio = deficit_mw / inputs.grid_demand_mw if inputs.grid_demand_mw > 0 else 0

    if deficit_ratio > 0.15:
        priority = RecommendationPriority.CRITICAL
        title = "Critical Supply Deficit Detected"
        summary = f"Grid supply shortfall of {deficit_mw:.0f} MW ({deficit_ratio:.1%} of demand)"
    elif deficit_ratio > 0.10:
        priority = RecommendationPriority.HIGH
        title = "Significant Supply Deficit"
        summary = f"Grid supply shortfall of {deficit_mw:.0f} MW ({deficit_ratio:.1%} of demand)"
    elif deficit_ratio > 0.05:
        priority = RecommendationPriority.MEDIUM
        title = "Moderate Supply Deficit"
        summary = f"Grid supply shortfall of {deficit_mw:.0f} MW ({deficit_ratio:.1%} of demand)"
    else:
        priority = RecommendationPriority.LOW
        title = "Minor Supply Deficit"
        summary = f"Grid supply shortfall of {deficit_mw:.0f} MW ({deficit_ratio:.1%} of demand)"

    # Calculate confidence
    confidence = calculate_confidence_score(
        data_freshness_seconds=None,
        source_reliability=0.9 if inputs.grid_data_classification == DataClassification.OFFICIAL else 0.7,
        input_completeness=1.0,
        calculation_stability=0.95,
        forecast_available=inputs.forecast_available,
    )

    return Recommendation(
        type=RecommendationType.SUPPLY_DEFICIT,
        priority=priority,
        title=title,
        summary=summary,
        detailed_explanation=(
            f"Current grid demand ({inputs.grid_demand_mw:.0f} MW) exceeds "
            f"supply ({inputs.grid_supply_mw:.0f} MW) by {deficit_mw:.0f} MW. "
            f"This indicates potential load-shedding risk if not addressed."
        ),
        evidence=RecommendationEvidence(
            trigger="supply_deficit",
            current_value=deficit_mw,
            threshold=0.0,
            source_data_classification=inputs.grid_data_classification,
            source_type=SourceType.SYSTEM_STATUS,
            data_status=DataStatus.LIVE if inputs.grid_data_classification == DataClassification.OFFICIAL else DataStatus.ESTIMATED,
            explanation=(
                f"Deficit calculated from grid demand ({inputs.grid_demand_mw:.0f} MW) "
                f"minus supply ({inputs.grid_supply_mw:.0f} MW)."
            ),
        ),
        expected_impact=(
            f"If unaddressed, potential for {deficit_mw:.0f} MW load-shedding. "
            f"Recommend activating load-shedding mitigation protocols."
        ),
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_renewable_opportunity(inputs: SystemInputs) -> Optional[Recommendation]:
    """Evaluate renewable energy opportunity rule."""
    total_renewable = 0.0
    renewable_sources = []

    if inputs.solar_generation_mw is not None and inputs.solar_generation_mw > 0:
        total_renewable += inputs.solar_generation_mw
        renewable_sources.append(f"solar ({inputs.solar_generation_mw:.0f} MW)")

    if inputs.wind_generation_mw is not None and inputs.wind_generation_mw > 0:
        total_renewable += inputs.wind_generation_mw
        renewable_sources.append(f"wind ({inputs.wind_generation_mw:.0f} MW)")

    if total_renewable <= 0:
        return None

    # Check if renewable opportunity exists
    if inputs.grid_demand_mw and inputs.grid_demand_mw > 0:
        renewable_ratio = total_renewable / inputs.grid_demand_mw
        if renewable_ratio < 0.05:  # Less than 5% renewable
            priority = RecommendationPriority.HIGH
            title = "Low Renewable Utilization"
            summary = f"Renewable generation at {renewable_ratio:.1%} of demand ({total_renewable:.0f} MW)"
        elif renewable_ratio < 0.15:
            priority = RecommendationPriority.MEDIUM
            title = "Moderate Renewable Opportunity"
            summary = f"Renewable generation at {renewable_ratio:.1%} of demand ({total_renewable:.0f} MW)"
        else:
            priority = RecommendationPriority.LOW
            title = "Good Renewable Utilization"
            summary = f"Renewable generation at {renewable_ratio:.1%} of demand ({total_renewable:.0f} MW)"
    else:
        priority = RecommendationPriority.MEDIUM
        title = "Renewable Generation Active"
        summary = f"Total renewable generation: {total_renewable:.0f} MW from {', '.join(renewable_sources)}"

    # Determine source classification (worst of the inputs)
    if inputs.solar_data_classification == DataClassification.OFFICIAL and inputs.wind_data_classification == DataClassification.OFFICIAL:
        data_class = DataClassification.OFFICIAL
    elif inputs.solar_data_classification == DataClassification.DATA_UNAVAILABLE and inputs.wind_data_classification == DataClassification.DATA_UNAVAILABLE:
        data_class = DataClassification.DATA_UNAVAILABLE
    else:
        data_class = DataClassification.MIXED if hasattr(DataClassification, 'MIXED') else DataClassification.CALCULATED

    confidence = calculate_confidence_score(
        data_freshness_seconds=None,
        source_reliability=0.8,
        input_completeness=0.9,
        calculation_stability=0.85,
        forecast_available=inputs.forecast_available,
    )

    return Recommendation(
        type=RecommendationType.RENEWABLE_OPPORTUNITY,
        priority=priority,
        title=title,
        summary=summary,
        detailed_explanation=(
            f"Current renewable generation: {', '.join(renewable_sources)}. "
            f"Total: {total_renewable:.0f} MW."
        ),
        evidence=RecommendationEvidence(
            trigger="renewable_utilization",
            current_value=total_renewable,
            threshold=0.05,
            source_data_classification=data_class,
            source_type=SourceType.SYSTEM_STATUS,
            data_status=DataStatus.LIVE,
            explanation="Renewable generation calculated from solar and wind data.",
        ),
        expected_impact=(
            f"Renewable sources contributing {total_renewable:.0f} MW to grid. "
            f"Monitoring utilization ratio for optimization opportunities."
        ),
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_high_risk(inputs: SystemInputs) -> Optional[Recommendation]:
    """Evaluate high grid risk rule."""
    if inputs.risk_score is None:
        return None

    if inputs.risk_score < 60:
        return None

    if inputs.risk_score >= 80:
        priority = RecommendationPriority.CRITICAL
        title = "Critical Grid Risk Level"
        summary = f"Grid risk score at {inputs.risk_score:.0f}/100"
    elif inputs.risk_score >= 70:
        priority = RecommendationPriority.HIGH
        title = "Elevated Grid Risk"
        summary = f"Grid risk score at {inputs.risk_score:.0f}/100"
    else:
        priority = RecommendationPriority.MEDIUM
        title = "Moderate Grid Risk"
        summary = f"Grid risk score at {inputs.risk_score:.0f}/100"

    confidence = calculate_confidence_score(
        data_freshness_seconds=None,
        source_reliability=0.85,
        input_completeness=1.0,
        calculation_stability=0.9,
        forecast_available=inputs.forecast_available,
    )

    return Recommendation(
        type=RecommendationType.HIGH_GRID_RISK,
        priority=priority,
        title=title,
        summary=summary,
        detailed_explanation=(
            f"Grid risk assessment indicates elevated risk level ({inputs.risk_level}). "
            f"This may indicate stress on the power grid requiring monitoring."
        ),
        evidence=RecommendationEvidence(
            trigger="grid_risk_score",
            current_value=inputs.risk_score,
            threshold=60.0,
            source_data_classification=DataClassification.CALCULATED,
            source_type=SourceType.RULE_BASED,
            data_status=DataStatus.LIVE,
            explanation="Risk score calculated from grid stability metrics.",
        ),
        expected_impact=(
            f"Risk level {inputs.risk_level} indicates potential for "
            f"grid instability. Enhanced monitoring recommended."
        ),
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_forecast_unavailable(inputs: SystemInputs) -> Optional[Recommendation]:
    """Evaluate forecast unavailable rule."""
    if inputs.forecast_available:
        return None

    # Check if we have sufficient data
    if inputs.independent_observations >= 168:
        return None

    priority = RecommendationPriority.MEDIUM
    title = "Forecast Unavailable"
    summary = f"Forecast blocked: {inputs.independent_observations}/168 independent observations"

    confidence = calculate_confidence_score(
        data_freshness_seconds=None,
        source_reliability=0.9,
        input_completeness=0.5,
        calculation_stability=1.0,
        forecast_available=False,
    )

    return Recommendation(
        type=RecommendationType.FORECAST_UNAVAILABLE,
        priority=priority,
        title=title,
        summary=summary,
        detailed_explanation=(
            f"Forecast generation requires 168 independent observations. "
            f"Currently have {inputs.independent_observations} independent observations. "
            f"Recommendations based on verified current system conditions only."
        ),
        evidence=RecommendationEvidence(
            trigger="insufficient_observations",
            current_value=float(inputs.independent_observations),
            threshold=168.0,
            source_data_classification=DataClassification.DATA_UNAVAILABLE,
            source_type=SourceType.SYSTEM_STATUS,
            data_status=DataStatus.UNAVAILABLE,
            explanation="Forecast gate blocked due to insufficient independent observations.",
        ),
        expected_impact=(
            "Recommendations limited to current system state analysis. "
            "No forward-looking predictions available."
        ),
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_data_quality(inputs: SystemInputs) -> Optional[Recommendation]:
    """Evaluate data quality degradation rule."""
    if not inputs.data_quality_issues:
        return None

    issue_count = len(inputs.data_quality_issues)
    if issue_count == 0:
        return None

    if issue_count >= 3:
        priority = RecommendationPriority.HIGH
        title = "Multiple Data Quality Issues"
    elif issue_count >= 2:
        priority = RecommendationPriority.MEDIUM
        title = "Data Quality Degradation"
    else:
        priority = RecommendationPriority.LOW
        title = "Minor Data Quality Issue"

    summary = f"{issue_count} data quality issue(s) detected"
    issues_text = "; ".join(inputs.data_quality_issues[:5])

    confidence = calculate_confidence_score(
        data_freshness_seconds=None,
        source_reliability=0.8,
        input_completeness=0.7,
        calculation_stability=0.7,
        forecast_available=inputs.forecast_available,
    )

    return Recommendation(
        type=RecommendationType.DATA_QUALITY_DEGRADATION,
        priority=priority,
        title=title,
        summary=summary,
        detailed_explanation=(
            f"Data quality issues detected: {issues_text}. "
            f"These issues may affect recommendation accuracy."
        ),
        evidence=RecommendationEvidence(
            trigger="data_quality_issues",
            current_value=float(issue_count),
            threshold=1.0,
            source_data_classification=DataClassification.DATA_UNAVAILABLE,
            source_type=SourceType.SYSTEM_STATUS,
            data_status=DataStatus.UNAVAILABLE,
            explanation=f"Issues: {issues_text}",
        ),
        expected_impact=(
            f"Data quality issues ({issue_count}) may reduce recommendation "
            f"accuracy. Monitoring data sources recommended."
        ),
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================
# MAIN DECISION SUPPORT SERVICE
# ============================================================

class DecisionSupportService:
    """Unified recommendation engine for PowerFlex BD."""
    
    def __init__(self):
        """Initialize the decision support service."""
        self._deduplicator = RecommendationDeduplicator()
    
    def _collect_inputs(self) -> SystemInputs:
        """Collect inputs from all available sources."""
        inputs = SystemInputs()
        
        # Collect grid data
        try:
            from backend.services.grid_service import get_grid_live
            grid = get_grid_live()
            if grid and grid.get("grid_snapshot"):
                snapshot = grid["grid_snapshot"]
                inputs.grid_demand_mw = snapshot.get("current_demand_mw")
                inputs.grid_supply_mw = snapshot.get("supply_mw") or snapshot.get("current_generation_mw")
                inputs.grid_status = grid.get("grid_status", "UNKNOWN")
                inputs.grid_data_classification = DataClassification.OFFICIAL
                inputs.grid_timestamp = snapshot.get("timestamp")
            else:
                inputs.missing_inputs.append("grid_data")
        except Exception as e:
            logger.warning("Failed to collect grid data: %s", e)
            inputs.missing_inputs.append("grid_data")
        
        # Collect renewable data
        try:
            from backend.services.solar_service import get_solar_live
            solar = get_solar_live()
            if solar and solar.get("forecasts"):
                # Get latest forecast
                forecasts = solar["forecasts"]
                if forecasts:
                    latest = forecasts[-1]
                    inputs.solar_generation_mw = latest.get("generation_mw") or latest.get("power_output_mw")
                    inputs.solar_data_classification = DataClassification.FORECAST
            else:
                inputs.missing_inputs.append("solar_data")
        except Exception as e:
            logger.warning("Failed to collect solar data: %s", e)
            inputs.missing_inputs.append("solar_data")
        
        try:
            from backend.services.wind_service import get_wind_live
            wind = get_wind_live()
            if wind and wind.get("forecasts"):
                forecasts = wind["forecasts"]
                if forecasts:
                    latest = forecasts[-1]
                    inputs.wind_generation_mw = latest.get("generation_mw") or latest.get("power_output_mw")
                    inputs.wind_data_classification = DataClassification.FORECAST
            else:
                inputs.missing_inputs.append("wind_data")
        except Exception as e:
            logger.warning("Failed to collect wind data: %s", e)
            inputs.missing_inputs.append("wind_data")
        
        # Collect risk data
        try:
            from backend.risk_engine import compute_grid_risk
            # Build minimal inputs for risk calculation
            demand_mw = inputs.grid_demand_mw or 0.0
            supply_mw = inputs.grid_supply_mw or 0.0
            solar_data = {}
            wind_data = {}
            if inputs.solar_generation_mw is not None:
                solar_data = {"current_generation_mw": inputs.solar_generation_mw}
            if inputs.wind_generation_mw is not None:
                wind_data = {"current_generation_mw": inputs.wind_generation_mw}
            risk_result = compute_grid_risk(
                demand_mw=demand_mw,
                supply_mw=supply_mw,
                solar_data=solar_data,
                wind_data=wind_data,
                include_scenarios=False,
            )
            inputs.risk_score = risk_result.composite_score
            inputs.risk_level = risk_result.risk_level
        except Exception as e:
            logger.warning("Failed to collect risk data: %s", e)
        
        # Collect data quality info
        try:
            from backend.demand_history import count_unique_observations
            count = count_unique_observations()
            inputs.independent_observations = count
            
            # Check forecast readiness
            if count >= 168:
                inputs.forecast_ready = True
                inputs.forecast_available = True
            else:
                inputs.forecast_ready = False
                inputs.forecast_available = False
        except Exception as e:
            logger.warning("Failed to collect data quality info: %s", e)
            inputs.missing_inputs.append("data_quality")
        
        # Check for data quality issues
        issues = []
        if not inputs.grid_demand_mw:
            issues.append("grid_demand_unavailable")
        if not inputs.grid_supply_mw:
            issues.append("grid_supply_unavailable")
        if inputs.risk_score and inputs.risk_score > 70:
            issues.append("high_grid_risk")
        inputs.data_quality_issues = issues
        
        return inputs
    
    def generate_recommendations(self) -> Dict[str, Any]:
        """Generate all recommendations from current system state.
        
        Returns:
            Dictionary with recommendations and metadata
        """
        inputs = self._collect_inputs()
        
        recommendations = []
        
        # Evaluate all rules
        rule_results = [
            evaluate_supply_deficit(inputs),
            evaluate_renewable_opportunity(inputs),
            evaluate_high_risk(inputs),
            evaluate_forecast_unavailable(inputs),
            evaluate_data_quality(inputs),
        ]
        
        # Filter and deduplicate
        for rec in rule_results:
            if rec is None:
                continue
            
            if not self._deduplicator.is_duplicate(rec):
                self._deduplicator.register(rec)
                recommendations.append(rec)
        
        # Sort by priority
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
            RecommendationPriority.INFORMATIONAL: 4,
        }
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 5))
        
        # Build response
        now = datetime.now(timezone.utc).isoformat()
        
        return {
            "status": "OK",
            "timestamp": now,
            "system_inputs": inputs.to_dict(),
            "recommendations": [r.to_dict() for r in recommendations],
            "total_recommendations": len(recommendations),
            "missing_inputs": inputs.missing_inputs,
            "metadata": {
                "source_type": SourceType.RULE_BASED.value,
                "data_status": DataStatus.LIVE.value if not inputs.missing_inputs else DataStatus.ESTIMATED.value,
                "confidence_average": (
                    sum(r.confidence for r in recommendations) / len(recommendations)
                    if recommendations
                    else 0.0
                ),
                "forecast_available": inputs.forecast_available,
                "independent_observations": inputs.independent_observations,
            },
        }


# ============================================================
# PUBLIC API
# ============================================================

def get_decision_support() -> Dict[str, Any]:
    """Get decision support recommendations.
    
    This is the main entry point for the decision support system.
    Returns recommendations with full provenance and confidence scoring.
    """
    service = DecisionSupportService()
    return service.generate_recommendations()


def get_recommendation_by_type(rec_type: RecommendationType) -> Optional[Dict[str, Any]]:
    """Get a specific recommendation type if active."""
    service = DecisionSupportService()
    result = service.generate_recommendations()
    
    for rec in result.get("recommendations", []):
        if rec.get("type") == rec_type.value:
            return rec
    
    return None


def get_system_health() -> Dict[str, Any]:
    """Get system health for decision support."""
    inputs = SystemInputs()
    
    try:
        from backend.demand_history import count_unique_observations
        inputs.independent_observations = count_unique_observations()
    except Exception:
        pass
    
    try:
        from backend.services.grid_service import get_grid_live
        grid = get_grid_live()
        if grid:
            inputs.grid_status = grid.get("grid_status", "UNKNOWN")
    except Exception:
        pass
    
    return {
        "independent_observations": inputs.independent_observations,
        "grid_status": inputs.grid_status,
        "forecast_ready": inputs.independent_observations >= 168,
        "data_quality_score": max(0, 1.0 - (len(inputs.data_quality_issues) * 0.1)),
    }
