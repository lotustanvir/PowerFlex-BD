"""Forecasting Production Gate for PowerFlex BD.

Enforces production integrity by:
1. Tracking data provenance through the forecast pipeline
2. Preventing synthetic-trained models from being used in production
3. Exposing honest model status in API responses
4. Requiring minimum data quality for production forecasts

Key principle: NEVER claim production readiness when using synthetic data.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("powerflex.forecast_gate")


# =========================================================
# FORECAST STATUS CONSTANTS
# =========================================================

class ForecastStatus:
    """Forecast production status constants."""
    PRODUCTION_READY = "PRODUCTION_READY"
    INSUFFICIENT_HISTORICAL_DATA = "INSUFFICIENT_HISTORICAL_DATA"
    SYNTHETIC_TRAINED = "SYNTHETIC_TRAINED"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"


from backend.data_quality import DataProvenance


# =========================================================
# PRODUCTION REQUIREMENTS
# =========================================================

class ProductionRequirements:
    """Minimum requirements for production forecasting."""
    
    # Minimum real historical records for training
    MIN_TRAINING_RECORDS = 168  # 1 week of hourly data
    
    # Recommended records for reliable forecasting
    RECOMMENDED_TRAINING_RECORDS = 8760  # 1 year of hourly data
    
    # Maximum allowed synthetic records in training
    MAX_SYNTHETIC_TRAINING_RECORDS = 0
    
    # Minimum validation score (MAPE)
    MIN_VALIDATION_MAPE = 0.15  # 15% MAPE threshold
    
    # Required data classifications for training
    ALLOWED_TRAINING_CLASSIFICATIONS = [
        DataProvenance.REAL_HISTORICAL,
        DataProvenance.REAL_LIVE,
        DataProvenance.USER_PROVIDED,
    ]


# =========================================================
# FORECAST PROVENANCE TRACKER
# =========================================================

@dataclass
class ForecastProvenance:
    """Track complete provenance of a forecast."""
    
    # Input data
    input_source: str = "unknown"
    input_classification: str = DataProvenance.UNVERIFIED
    input_record_count: int = 0
    input_time_span_hours: float = 0.0
    
    # Training data
    training_source: str = "unknown"
    training_classification: str = DataProvenance.UNVERIFIED
    training_record_count: int = 0
    synthetic_training_records: int = 0
    real_training_records: int = 0
    
    # Model
    model_name: str = "unknown"
    model_version: str = "v1"
    model_trained_at: Optional[str] = None
    
    # Validation
    validation_status: str = "NOT_VALIDATED"
    validation_mape: Optional[float] = None
    validation_mae_mw: Optional[float] = None
    validation_rmse_mw: Optional[float] = None
    
    # Production gate
    forecast_status: str = ForecastStatus.DEVELOPMENT_ONLY
    production_ready: bool = False
    blocking_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": {
                "source": self.input_source,
                "classification": self.input_classification,
                "record_count": self.input_record_count,
                "time_span_hours": self.input_time_span_hours,
            },
            "training": {
                "source": self.training_source,
                "classification": self.training_classification,
                "record_count": self.training_record_count,
                "synthetic_records": self.synthetic_training_records,
                "real_records": self.real_training_records,
            },
            "model": {
                "name": self.model_name,
                "version": self.model_version,
                "trained_at": self.model_trained_at,
            },
            "validation": {
                "status": self.validation_status,
                "mape": self.validation_mape,
                "mae_mw": self.validation_mae_mw,
                "rmse_mw": self.validation_rmse_mw,
            },
            "production_gate": {
                "status": self.forecast_status,
                "ready": self.production_ready,
                "blocking_reasons": self.blocking_reasons,
            },
        }


# =========================================================
# PRODUCTION GATE CHECKER
# =========================================================

class ProductionGateChecker:
    """Check if a forecast meets production requirements."""
    
    def __init__(self):
        self.requirements = ProductionRequirements()
    
    def check_production_readiness(
        self,
        provenance: ForecastProvenance,
    ) -> ForecastProvenance:
        """Check if forecast is ready for production use."""
        
        blocking_reasons = []
        
        # Check training data classification
        if provenance.training_classification == DataProvenance.SYNTHETIC:
            blocking_reasons.append(
                f"SYNTHETIC_TRAINING: Model trained on synthetic data. "
                f"Need {self.requirements.MIN_TRAINING_RECORDS} real historical records."
            )
        
        # Check training record count
        if provenance.real_training_records < self.requirements.MIN_TRAINING_RECORDS:
            blocking_reasons.append(
                f"INSUFFICIENT_DATA: Only {provenance.real_training_records} real training records. "
                f"Need {self.requirements.MIN_TRAINING_RECORDS} minimum."
            )
        
        # Check synthetic records
        if provenance.synthetic_training_records > self.requirements.MAX_SYNTHETIC_TRAINING_RECORDS:
            blocking_reasons.append(
                f"SYNTHETIC_DATA: {provenance.synthetic_training_records} synthetic records in training. "
                f"Production requires 0 synthetic records."
            )
        
        # Check validation status
        if provenance.validation_status != "PASSED":
            blocking_reasons.append(
                f"VALIDATION_PENDING: Model validation not passed. "
                f"Status: {provenance.validation_status}"
            )
        
        # Check MAPE if available
        if (provenance.validation_mape is not None and 
            provenance.validation_mape > self.requirements.MIN_VALIDATION_MAPE):
            blocking_reasons.append(
                f"POOR_ACCURACY: MAPE {provenance.validation_mape:.1%} exceeds "
                f"threshold {self.requirements.MIN_VALIDATION_MAPE:.1%}"
            )
        
        # Determine forecast status
        if not blocking_reasons:
            provenance.forecast_status = ForecastStatus.PRODUCTION_READY
            provenance.production_ready = True
        elif provenance.synthetic_training_records > 0:
            provenance.forecast_status = ForecastStatus.SYNTHETIC_TRAINED
        elif provenance.real_training_records < self.requirements.MIN_TRAINING_RECORDS:
            provenance.forecast_status = ForecastStatus.INSUFFICIENT_HISTORICAL_DATA
        else:
            provenance.forecast_status = ForecastStatus.VALIDATION_PENDING
        
        provenance.blocking_reasons = blocking_reasons
        
        return provenance
    
    def get_honest_status_message(
        self,
        provenance: ForecastProvenance,
    ) -> str:
        """Get an honest human-readable status message."""
        
        if provenance.production_ready:
            return (
                f"PRODUCTION READY: Model trained on {provenance.real_training_records} "
                f"real historical records with validated accuracy."
            )
        
        if provenance.synthetic_training_records > 0:
            return (
                f"DEVELOPMENT ONLY: Model trained on SYNTHETIC data "
                f"({provenance.synthetic_training_records} synthetic records, "
                f"{provenance.real_training_records} real records). "
                f"Not suitable for production forecasting."
            )
        
        if provenance.real_training_records < self.requirements.MIN_TRAINING_RECORDS:
            needed = self.requirements.MIN_TRAINING_RECORDS - provenance.real_training_records
            return (
                f"INSUFFICIENT DATA: {provenance.real_training_records} real records collected. "
                f"Need {needed} more for minimum production threshold "
                f"({self.requirements.MIN_TRAINING_RECORDS} minimum)."
            )
        
        return (
            f"VALIDATION PENDING: Model has sufficient data but "
            f"validation not yet completed."
        )


# =========================================================
# DEMAND FORECAST PROVENANCE BUILDER
# =========================================================

def build_demand_forecast_provenance(
    real_pgcb_records: int,
    synthetic_records: int = 0,
    model_name: str = "XGBoost",
    validation_mape: Optional[float] = None,
    validation_mae_mw: Optional[float] = None,
    validation_rmse_mw: Optional[float] = None,
) -> ForecastProvenance:
    """Build provenance for demand forecast."""
    
    provenance = ForecastProvenance(
        input_source="PGCB_ERP",
        input_classification=DataProvenance.REAL_LIVE,
        input_record_count=real_pgcb_records,
        training_source="SYNTHETIC" if synthetic_records > 0 else "PGCB_HISTORICAL",
        training_classification=(
            DataProvenance.SYNTHETIC if synthetic_records > 0 
            else DataProvenance.REAL_HISTORICAL
        ),
        training_record_count=real_pgcb_records + synthetic_records,
        synthetic_training_records=synthetic_records,
        real_training_records=real_pgcb_records,
        model_name=model_name,
        model_version="v1",
        model_trained_at=datetime.now(timezone.utc).isoformat(),
    )
    
    # Set validation status
    if validation_mape is not None:
        provenance.validation_mape = validation_mape
        provenance.validation_mae_mw = validation_mae_mw
        provenance.validation_rmse_mw = validation_rmse_mw
        
        if validation_mape <= ProductionRequirements.MIN_VALIDATION_MAPE:
            provenance.validation_status = "PASSED"
        else:
            provenance.validation_status = "FAILED_ACCURACY"
    else:
        provenance.validation_status = "NOT_VALIDATED"
    
    # Check production readiness
    checker = ProductionGateChecker()
    provenance = checker.check_production_readiness(provenance)
    
    return provenance


# =========================================================
# SOLAR FORECAST PROVENANCE BUILDER
# =========================================================

def build_solar_forecast_provenance(
    training_target: str = "irradiance_derived",
    training_record_count: int = 0,
) -> ForecastProvenance:
    """Build provenance for solar forecast."""
    
    provenance = ForecastProvenance(
        input_source="Open_Meteo",
        input_classification=DataProvenance.REAL_LIVE,
        input_record_count=training_record_count,
        training_source=training_target,
        training_classification=DataProvenance.SYNTHETIC,
        training_record_count=training_record_count,
        synthetic_training_records=training_record_count,
        real_training_records=0,
        model_name="XGBoost_Solar",
        model_version="v1",
    )
    
    provenance.forecast_status = ForecastStatus.SYNTHETIC_TRAINED
    provenance.production_ready = False
    provenance.blocking_reasons = [
        f"SYNTHETIC_TARGET: Solar model trained on {training_target}, "
        f"not actual solar farm output measurements."
    ]
    
    return provenance


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def get_forecast_status_summary() -> Dict[str, Any]:
    """Get summary of forecast production status.

    Uses count_unique_observations() which applies state-change
    detection: consecutive records with identical values collapse
    into one independent observation. This prevents rapid-polling
    duplicates from masquerading as independent observations.
    """

    # Check demand forecast — use independent count, not raw rows
    try:
        from backend.demand_history import count_unique_observations
        real_records = count_unique_observations()
    except Exception:
        real_records = 0

    # Also get raw count for transparency
    try:
        from backend.demand_history import count_records
        raw_records = count_records()
    except Exception:
        raw_records = 0

    synthetic_records = 8760  # Current synthetic training data size

    demand_provenance = build_demand_forecast_provenance(
        real_pgcb_records=real_records,
        synthetic_records=synthetic_records if real_records < ProductionRequirements.MIN_TRAINING_RECORDS else 0,
    )
    
    # Check solar forecast
    solar_provenance = build_solar_forecast_provenance(
        training_target="irradiance_derived",
        training_record_count=79057,  # From weather data
    )
    
    return {
        "demand_forecast": demand_provenance.to_dict(),
        "solar_forecast": solar_provenance.to_dict(),
        "production_requirements": {
            "min_training_records": ProductionRequirements.MIN_TRAINING_RECORDS,
            "recommended_training_records": ProductionRequirements.RECOMMENDED_TRAINING_RECORDS,
            "max_synthetic_records": ProductionRequirements.MAX_SYNTHETIC_TRAINING_RECORDS,
            "min_validation_mape": ProductionRequirements.MIN_VALIDATION_MAPE,
        },
        "demand_history": {
            "raw_records": raw_records,
            "independent_observations": real_records,
            "duplicates_collapsed": raw_records - real_records,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    """Print forecast status summary."""
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    summary = get_forecast_status_summary()
    
    print("\n=== Forecast Production Gate Status ===\n")
    print(json.dumps(summary, indent=2))
