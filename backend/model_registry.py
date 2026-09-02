from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum


class ModelStatus(Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    PRODUCTION = "PRODUCTION"
    RETIRED = "RETIRED"


@dataclass
class ModelEntry:
    model_id: str
    name: str
    version: str
    algorithm: str
    status: ModelStatus
    created_at: str
    trained_at: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    artifact_path: Optional[str] = None
    training_data_source: str = "synthetic"
    feature_names: list = field(default_factory=list)
    description: str = ""
    data_classification: str = "EXPERIMENTAL"


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(ModelEntry(
            model_id="solar_weather_v1",
            name="Solar Weather-Only Model",
            version="1.0",
            algorithm="XGBoost",
            status=ModelStatus.EXPERIMENTAL,
            created_at="2025-01-01T00:00:00Z",
            artifact_path="models/weather_only_solar_model.pkl",
            training_data_source="synthetic irradiance targets",
            feature_names=[
                "temperature_c", "humidity_percent", "precipitation_mm",
                "cloud_cover_percent", "wind_speed_kmh", "wind_direction_degree",
                "solar_radiation_wm2", "hour", "day", "month", "day_of_week",
                "is_daytime",
            ],
            description=(
                "Solar generation forecast model trained on synthetic targets "
                "derived from irradiance formulas. NOT validated against real "
                "Bangladesh solar farm output."
            ),
        ))

        self.register(ModelEntry(
            model_id="demand_forecast_v1",
            name="Demand Forecast Model",
            version="1.0",
            algorithm="XGBoost",
            status=ModelStatus.EXPERIMENTAL,
            created_at="2025-01-01T00:00:00Z",
            artifact_path="models/demand_forecast_model.pkl",
            training_data_source="synthetic demand profiles",
            feature_names=[
                "hour", "day", "month", "day_of_week", "is_weekend",
                "temperature_c", "humidity_percent",
            ],
            description=(
                "Demand forecast model trained on SYNTHETIC demand profiles "
                "based on published Bangladesh load research patterns. "
                "NOT production-validated."
            ),
        ))

        self.register(ModelEntry(
            model_id="wind_power_v1",
            name="Wind Power Curve Model",
            version="1.0",
            algorithm="Power Curve (engineering)",
            status=ModelStatus.EXPERIMENTAL,
            created_at="2025-01-01T00:00:00Z",
            training_data_source="engineering power curve",
            feature_names=[
                "wind_speed_ms", "wind_direction_degree",
                "air_density_kgm3", "hub_height_m",
            ],
            description=(
                "Engineering power curve model applied to Open-Meteo 100m "
                "wind speed data. Uses simplified prototype turbine parameters. "
                "NOT validated against real wind turbine telemetry."
            ),
        ))

    def register(self, entry: ModelEntry) -> None:
        self._models[entry.model_id] = entry

    def get(self, model_id: str) -> Optional[ModelEntry]:
        return self._models.get(model_id)

    def list_all(self) -> List[ModelEntry]:
        return list(self._models.values())

    def list_by_status(self, status: ModelStatus) -> List[ModelEntry]:
        return [m for m in self._models.values() if m.status == status]

    def to_dict(self) -> dict:
        return {
            model_id: {
                "model_id": entry.model_id,
                "name": entry.name,
                "version": entry.version,
                "algorithm": entry.algorithm,
                "status": entry.status.value,
                "created_at": entry.created_at,
                "trained_at": entry.trained_at,
                "metrics": entry.metrics,
                "artifact_path": entry.artifact_path,
                "training_data_source": entry.training_data_source,
                "feature_names": entry.feature_names,
                "description": entry.description,
                "data_classification": entry.data_classification,
            }
            for model_id, entry in self._models.items()
        }


_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
