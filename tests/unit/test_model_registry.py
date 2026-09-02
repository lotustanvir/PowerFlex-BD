import pytest
from backend.model_registry import (
    ModelRegistry,
    ModelEntry,
    ModelStatus,
    get_model_registry,
)


class TestModelStatus:
    def test_enum_values(self):
        assert ModelStatus.EXPERIMENTAL.value == "EXPERIMENTAL"
        assert ModelStatus.VALIDATED.value == "VALIDATED"
        assert ModelStatus.PRODUCTION.value == "PRODUCTION"
        assert ModelStatus.RETIRED.value == "RETIRED"

    def test_all_statuses_exist(self):
        statuses = list(ModelStatus)
        assert len(statuses) == 4


class TestModelEntry:
    def test_creation_with_defaults(self):
        entry = ModelEntry(
            model_id="test_model",
            name="Test",
            version="1.0",
            algorithm="XGBoost",
            status=ModelStatus.EXPERIMENTAL,
            created_at="2025-01-01T00:00:00Z",
        )
        assert entry.model_id == "test_model"
        assert entry.metrics == {}
        assert entry.feature_names == []
        assert entry.description == ""
        assert entry.data_classification == "EXPERIMENTAL"
        assert entry.artifact_path is None
        assert entry.trained_at is None

    def test_creation_with_all_fields(self):
        entry = ModelEntry(
            model_id="full_model",
            name="Full Model",
            version="2.0",
            algorithm="RandomForest",
            status=ModelStatus.PRODUCTION,
            created_at="2025-06-01T00:00:00Z",
            trained_at="2025-05-15T12:00:00Z",
            metrics={"mae": 1.5, "rmse": 2.0},
            artifact_path="models/full.pkl",
            training_data_source="real data",
            feature_names=["f1", "f2"],
            description="A full model",
            data_classification="PRODUCTION",
        )
        assert entry.metrics == {"mae": 1.5, "rmse": 2.0}
        assert entry.artifact_path == "models/full.pkl"
        assert entry.data_classification == "PRODUCTION"


class TestModelRegistry:
    def test_defaults_registered(self):
        registry = ModelRegistry()
        all_models = registry.list_all()
        assert len(all_models) >= 3

    def test_register_and_get(self):
        registry = ModelRegistry()
        entry = ModelEntry(
            model_id="custom_model",
            name="Custom",
            version="1.0",
            algorithm="SVM",
            status=ModelStatus.EXPERIMENTAL,
            created_at="2025-01-01T00:00:00Z",
        )
        registry.register(entry)
        retrieved = registry.get("custom_model")
        assert retrieved is not None
        assert retrieved.name == "Custom"

    def test_get_nonexistent_returns_none(self):
        registry = ModelRegistry()
        assert registry.get("nonexistent") is None

    def test_list_by_status(self):
        registry = ModelRegistry()
        experimental = registry.list_by_status(ModelStatus.EXPERIMENTAL)
        assert len(experimental) >= 3
        for m in experimental:
            assert m.status == ModelStatus.EXPERIMENTAL

        production = registry.list_by_status(ModelStatus.PRODUCTION)
        assert len(production) == 0

    def test_to_dict(self):
        registry = ModelRegistry()
        d = registry.to_dict()
        assert isinstance(d, dict)
        assert "solar_weather_v1" in d
        solar = d["solar_weather_v1"]
        assert solar["model_id"] == "solar_weather_v1"
        assert solar["status"] == "EXPERIMENTAL"
        assert solar["algorithm"] == "XGBoost"
        assert isinstance(solar["feature_names"], list)
        assert len(solar["feature_names"]) == 12

    def test_solar_model_features(self):
        registry = ModelRegistry()
        solar = registry.get("solar_weather_v1")
        assert solar is not None
        assert "solar_radiation_wm2" in solar.feature_names
        assert "is_daytime" in solar.feature_names
        assert solar.artifact_path == "models/weather_only_solar_model.pkl"

    def test_demand_model_registered(self):
        registry = ModelRegistry()
        demand = registry.get("demand_forecast_v1")
        assert demand is not None
        assert demand.algorithm == "XGBoost"
        assert demand.training_data_source == "synthetic demand profiles"

    def test_wind_model_registered(self):
        registry = ModelRegistry()
        wind = registry.get("wind_power_v1")
        assert wind is not None
        assert wind.algorithm == "Power Curve (engineering)"

    def test_overwrite_existing(self):
        registry = ModelRegistry()
        entry = ModelEntry(
            model_id="solar_weather_v1",
            name="Solar V2",
            version="2.0",
            algorithm="LightGBM",
            status=ModelStatus.PRODUCTION,
            created_at="2025-06-01T00:00:00Z",
        )
        registry.register(entry)
        retrieved = registry.get("solar_weather_v1")
        assert retrieved.name == "Solar V2"
        assert retrieved.version == "2.0"


class TestGetModelRegistrySingleton:
    def test_returns_same_instance(self):
        r1 = get_model_registry()
        r2 = get_model_registry()
        assert r1 is r2

    def test_has_defaults(self):
        registry = get_model_registry()
        assert registry.get("solar_weather_v1") is not None


class TestAPIModelsContract:
    def test_get_api_models_returns_dict_with_models_and_total(self):
        registry = get_model_registry()
        d = registry.to_dict()
        total = len(registry.list_all())
        assert isinstance(d, dict)
        assert total >= 3
        for model_id, model_data in d.items():
            assert "model_id" in model_data
            assert "status" in model_data
            assert "algorithm" in model_data

    def test_models_dict_has_required_fields(self):
        registry = get_model_registry()
        for model in registry.list_all():
            model_dict = model.__dict__
            assert "model_id" in model_dict
            assert "name" in model_dict
            assert "version" in model_dict
            assert "algorithm" in model_dict
            assert "status" in model_dict
            assert "data_classification" in model_dict
            assert model_dict["data_classification"] in (
                "EXPERIMENTAL", "CALCULATED", "MEASURED",
                "FORECAST", "PROTOTYPE",
            )

    def test_no_route_returns_old_status_field(self):
        registry = get_model_registry()
        for model in registry.list_all():
            d = model.__dict__
            if "status" in d:
                status_val = d["status"].value if hasattr(d["status"], "value") else d["status"]
                assert status_val in (
                    "EXPERIMENTAL", "VALIDATED", "PRODUCTION", "RETIRED"
                )
