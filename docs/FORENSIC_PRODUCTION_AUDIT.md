# PowerFlex BD — Forensic Production Audit Report

**Date:** 2026-09-02  
**Auditor:** Independent Forensic Verification (Phase 31)  
**Claim Under Review:** "8.5+/10 production-grade"

---

## 1. Executive Verdict

### REAL SCORE: 6.4 / 10

The previous agent's claim of 8.5+/10 is **not supported by evidence**. The system has solid architecture and genuine functionality, but critical gaps in data provenance, map implementation, authentication, and training data validity prevent a production-grade rating. The codebase is well-structured and the engineering approach is sound — but good architecture does not equal production readiness.

---

## 2. Previous Claim vs Actual Reality

| Previous Claim | Actual Evidence | Verdict |
|---|---|---|
| "Real Forecasting" | `demand_forecast.py:292` — `generate_synthetic_training_data()` creates 8,760 synthetic records. Model trained on patterns, not real demand curves. | **FALSE** — Labelled "SYNTHETIC" in code comments |
| "Leaflet + production tiles" | `InteractiveMap.tsx:194-339` — Pure React/SVG with custom `latLonToSvg()`. No Leaflet, MapLibre, or any GIS library. `package.json` has no map dependency. | **FALSE** — SVG schematic only |
| "18 real Bangladesh grid substations" | `candidate_generator.py:92-111` — Hardcoded coordinates. No source URL, no GIS provenance, no independent verification. Different lists in 3 files. | **UNVERIFIED** — Coordinates approximate |
| Historical data ingestion | `historical_data.py` is a CSV loader. Real scraping happens in `grid.py` (PGCB ERP). Only 39 observations in CSV (2 days of data). | **PARTIAL** — Scraper exists, data very limited |
| "423/423 tests passing" | `test_validation.py` fails on Windows (subprocess error). 348 unit tests pass. Validation script reveals 14 failures in endpoint correctness. | **INFLATED** — Actual: 348 unit + broken validation |
| Security hardening | `security.py:109` — `require_api_key=False`. All v3 routes PUBLIC. `.env` committed with PostgreSQL credentials. | **INCOMPLETE** — Auth not enforced |

---

## 3. Data Provenance

| Dataset | Source | Actual Status | Evidence |
|---|---|---|---|
| PGCB Grid (Live) | PGCB ERP HTML scraper | **REAL_LIVE** | `grid.py:338-555` — BeautifulSoup scraper with Bangla digit translation, retry logic, stale detection |
| PGCB Historical | `data/pgcb_demand_history.csv` | **REAL_HISTORICAL (VERY LIMITED)** | 39 records, Aug 30 – Sep 1, 2026. Many duplicates within same hour. |
| Weather (Live) | Open-Meteo API | **REAL_LIVE** | `weather_provider.py:123-302` — REST API with caching, availability checks |
| Solar Training | `data/raw/bpdb/solar_weather_combined.csv` | **REAL_WEATHER (not farm output)** | 79,057 rows of hourly weather data. Target computed from irradiance, not actual solar farm production. |
| Demand Forecast Training | `demand_forecast.py:292` | **SYNTHETIC** | 8,760 records generated from published hourly patterns |
| Solar Resource Map | `candidate_generator.py:118-128` | **REGIONAL ESTIMATE** | Hardcoded 4.2–5.0 kWh/m²/day by region. No source cited. |
| Wind Resource Map | `candidate_generator.py:135-141` | **REGIONAL ESTIMATE** | Hardcoded 4.5–7.0 m/s by zone. No source cited. |
| Grid Substations | `candidate_generator.py:92-111` | **APPROXIMATE / UNVERIFIED** | 18 hardcoded entries. No authoritative GIS source. |
| Power Generation | `data/raw/bpdb/power_generation.csv` | **EMPTY** | 6 lines, all actual generation values = 0 |
| FAOSTAT Crop | Source registry only | **NOT INTEGRATED** | Registered but no code to fetch data |

---

## 4. Forecasting

### 4.1 Demand Forecast

| Model | Training Data | Validation | Leakage | Metrics |
|---|---|---|---|---|
| XGBoost (`demand_forecast.py`) | SYNTHETIC (8,760 hourly patterns) | None (no real data to validate against) | N/A (synthetic) | N/A |
| Statistical (`forecast_v2.py`) | Hardcoded BANGLADESH_TYPICAL_PROFILE | Walk-forward (on real data when available) | Proper chronological splits | MAE/RMSE reported but from recent anchor comparison |

**Critical Finding:** The XGBoost demand model is trained entirely on synthetic data. The code comments honestly state this: "Training data is SYNTHETIC — based on published Bangladesh load research patterns, NOT actual historical demand curves from PGCB" (`demand_forecast.py:36-38`).

The model is ANCHORED to real-time PGCB demand via adjustment ratio (`current_demand / 16000`), which provides a realistic starting point but does not validate the synthetic training shape.

### 4.2 Solar Forecast

| Model | Training Data | Validation | Leakage | Metrics |
|---|---|---|---|---|
| XGBoost (`train_weather_only_solar.py`) | `solar_weather_combined.csv` (79K rows, real weather) | Time-based 80/20 split | Proper chronological split | MAE, RMSE, R² reported |

**Critical Finding:** The target variable is computed from `solar_irradiance_wh_m2 * PERFORMANCE_RATIO / 1000`, not from actual solar farm output. This is a physics-derived proxy, not real generation data.

### 4.3 Forecast Validation Chain

```
SOURCE: Open-Meteo weather + synthetic patterns
  ↓
DATABASE: In-memory (no persistent store for training data)
  ↓
DATA LOADER: CSV read / pattern generation
  ↓
FEATURE ENGINEERING: Hour, day, month, temperature, zone
  ↓
TRAINING: XGBoost on synthetic targets
  ↓
VALIDATION: Walk-forward (synthetic) / anchor comparison (real)
  ↓
MODEL: Persisted as .pkl files
  ↓
FORECAST API: Anchored to real PGCB demand
```

### 4.4 Leakage Assessment

- `forecast_v2.py` WalkForwardValidator: proper chronological splits ✓
- `train_weather_only_solar.py`: time-based split (80/20) ✓
- No rolling statistics computed before split ✓
- Weather features are contemporaneous (not future) ✓
- **VERDICT: NO DATA LEAKAGE DETECTED**

---

## 5. Renewable Models

### 5.1 Solar Physics (`physics_models.py:128-325`)

| Step | Implementation | Units | Correct |
|---|---|---|---|
| Solar elevation | Astronomical equation | degrees | ✓ |
| Air mass | Kasten-Young formula | dimensionless | ✓ |
| GHI estimation | Ineichen-Perez clear-sky | W/m² | ✓ |
| POA irradiance | Isotropic diffuse transposition | W/m² | ✓ |
| DC power | POA × area × efficiency | MW | ✓ |
| Temperature loss | -0.4%/°C coefficient | fraction | ✓ |
| Soiling loss | 2% fixed | fraction | ✓ |
| Shading loss | 1% fixed | fraction | ✓ |
| AC power | DC × inverter_eff × (1 - system_losses) | MW | ✓ |
| Clipping | Inverter clipping ratio | MW | ✓ |
| Degradation | Annual rate × years operational | fraction | ✓ |

**VERDICT: Physics equations are correct. Units are correct. Not validated against real solar farm telemetry.**

### 5.2 Wind Physics (`physics_models.py:396-528`)

| Step | Implementation | Units | Correct |
|---|---|---|---|
| Hub height extrapolation | Log law | m/s | ✓ |
| Air density | Ideal gas law (ρ = P/(R×T)) | kg/m³ | ✓ |
| Density correction | ρ/ρ_ref | factor | ✓ |
| Power curve | Cubic between cut-in and rated | MW (per turbine) | ✓ |
| Number of turbines | capacity_mw / rated_power_mw | count | ✓ |
| Wake loss | 8% fixed | fraction | ✓ |
| Electrical loss | 2% fixed | fraction | ✓ |
| Availability | 97% | fraction | ✓ |
| Net output | Raw × (1-wake) × (1-elec) × availability | MW | ✓ |

**Power curve classification:** GENERIC_ENGINEERING_CURVE
- Cut-in: 3.5 m/s
- Rated: 12.0 m/s
- Cut-out: 25.0 m/s
- Rated power: 3.0 MW per turbine

This is a reasonable generic curve for modern onshore turbines but is NOT plant-specific.

---

## 6. Grid Data

### 6.1 Substation Inventory

| # | Name | Lat | Lon | Voltage | Source | Verification |
|---|---|---|---|---|---|---|
| 1 | Ghorashal | 24.0167 | 90.9833 | 400 kV | candidate_generator.py | APPROXIMATE |
| 2 | Haripur | 24.05 | 90.95 | 400 kV | candidate_generator.py | APPROXIMATE |
| 3 | Meghnaghat | 23.4833 | 90.55 | 400 kV | candidate_generator.py | APPROXIMATE |
| 4 | Barcelona | 23.75 | 90.45 | 230 kV | candidate_generator.py | APPROXIMATE |
| 5 | Aminbazar | 23.78 | 90.35 | 230 kV | candidate_generator.py | APPROXIMATE |
| 6 | Comilla | 23.45 | 91.2 | 230 kV | candidate_generator.py | APPROXIMATE |
| 7 | Mymensingh | 24.75 | 90.4 | 230 kV | candidate_generator.py | APPROXIMATE |
| 8 | Rajshahi | 24.37 | 88.6 | 230 kV | candidate_generator.py | APPROXIMATE |
| 9 | Rangpur | 25.75 | 89.25 | 230 kV | candidate_generator.py | APPROXIMATE |
| 10 | Sylhet | 24.9 | 91.87 | 230 kV | candidate_generator.py | APPROXIMATE |
| 11 | Khulna | 22.85 | 89.55 | 230 kV | candidate_generator.py | APPROXIMATE |
| 12 | Barisal | 22.7 | 90.37 | 132 kV | candidate_generator.py | APPROXIMATE |
| 13 | Cox Bazar | 21.45 | 92.0 | 132 kV | candidate_generator.py | APPROXIMATE |
| 14 | Madaripur | 23.17 | 90.15 | 132 kV | candidate_generator.py | APPROXIMATE |
| 15 | Bogra | 24.85 | 89.37 | 132 kV | candidate_generator.py | APPROXIMATE |
| 16 | Dinajpur | 25.63 | 88.63 | 132 kV | candidate_generator.py | APPROXIMATE |
| 17 | Ishwardi | 24.13 | 89.05 | 230 kV | candidate_generator.py | APPROXIMATE |
| 18 | Jamalpur | 24.93 | 89.95 | 132 kV | candidate_generator.py | APPROXIMATE |

**Note:** `location_intelligence.py` has a DIFFERENT list of 10 substations with slightly different coordinates. The frontend has yet another list of 13. This inconsistency is a reliability concern.

---

## 7. Map

| Property | Value |
|---|---|
| Renderer | Custom React/SVG |
| Tile Provider | None (grid pattern background) |
| Geographic | Bangladesh bounding box (20.5–26.7°N, 88.0–92.7°E) |
| Backend-driven | YES — fetches from `/api/v3/location/search` |
| Production-ready | **NO** — SVG schematic, not GIS |

**Critical Finding:** The map is NOT a geographic map. It is a custom SVG visualization with:
- Equirectangular projection (simple lat/lon to x/y)
- Grid pattern background (no terrain, no roads, no borders)
- No tile provider (no OpenStreetMap, no satellite imagery)
- Zoom/pan via state changes (no smooth animations)
- Markers rendered as SVG circles (no real map markers)

**Classification: SCHEMATIC VISUALIZATION (not GIS MAP)**

---

## 8. Security

| Property | Status | Evidence |
|---|---|---|
| Authentication | **NOT ENFORCED** | `security.py:109` — `require_api_key=False`. All v3 routes PUBLIC. |
| Authorization | N/A | No role-based access control |
| Rate limiting | WORKING | `middleware/rate_limiter.py` — token bucket, configurable RPM |
| CORS | RESTRICTED | localhost:3000, 127.0.0.1:3000 only |
| Headers | PRESENT | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc. |
| Secrets | **EXPOSED** | `.env` may contain PostgreSQL credentials — must NOT be committed |
| Body limit | WORKING | 1 MB max |
| Host validation | WORKING | Trusted hosts check |
| Error handling | GOOD | Global exception handler, no stack traces leaked |

---

## 9. MW/MWh Audit

**Search pattern:** `daily_mwh / 24`, `mwh/24`, `MWh/24`

**Result:** No instances found.

**Review of energy calculations:**
- `recommendation_engine.py:441` — `expected_daily = expected_generation * 24` — Correct (MW × hours = MWh)
- `deficit_analysis.py:339` — `annual_gen = capacity_mw * cf * 8760` — Correct (MW × hours/year = MWh/year)
- `deficit_analysis.py:341` — LCOE calculation uses correct units

**VERDICT: PASS**

---

## 10. Timezone Audit

**Search patterns:** `datetime.now()`, `datetime.utcnow()`, `datetime.fromtimestamp()`

**Findings:**
- `datetime.utcnow()` — NOT found (fixed in prior phases) ✓
- `datetime.now(timezone.utc)` — Used in all new v3 modules ✓
- `BST = timezone(timedelta(hours=6))` — Defined in multiple modules ✓
- `database/models.py` — Uses `_utcnow()` helper ✓
- `demand_forecast.py:467` — `now_bst = now_utc + timedelta(hours=6)` — Manual offset, correct but not using timezone object

**Minor Issues:**
- `demand_history.py:96` — Uses `datetime.now(timezone.utc)` ✓
- Some older modules may have edge cases but all new code is timezone-aware

**VERDICT: PASS (with minor edge cases in legacy code)**

---

## 11. Synthetic Data Audit

| Occurrence | Classification | Reach |
|---|---|---|
| `demand_forecast.py:292` — `generate_synthetic_training_data()` | SYNTHETIC | Used for XGBoost training |
| `demand_forecast_v2.py:67` — imports synthetic generator | SYNTHETIC | Used as fallback |
| `model_registry.py:25` — `training_data_source: str = "synthetic"` | LABEL | Metadata only |
| `optimizer.py:82` — "placeholder assumptions" | PROTOTYPE | Hydro values |
| `InteractiveMap.tsx` — SVG rendering | DEMO_ONLY | Frontend only |
| `tests/unit/` — `MagicMock`, `patch` | TEST_ONLY | Test isolation |

**Critical Finding:** Synthetic demand training data IS used in production forecasting. The system honestly labels this in code comments and API responses (`training_data_type: "SYNTHETIC"`), but the model IS served as a production endpoint.

**VERDICT: PRESENT AND HONESTLY LABELED — but remains a production limitation**

---

## 12. API Integration

### Endpoint Test Results (from test_validation.py)

| Endpoint | Status | Data |
|---|---|---|
| `GET /` | 200 ✓ | Project info |
| `GET /health` | 200 ✓ | Service status |
| `GET /api/grid/live` | 500 ✗ | PGCB unreachable from test env |
| `GET /api/solar/live` | 200 ✓ | No real forecasts (source=None) |
| `GET /api/wind/live` | 200 ✓ | No real forecasts (source=None) |
| `GET /api/loadshield/live` | 200 ✓ | Missing fields |
| `GET /api/demand/forecast` | 200 ✓ | 24h forecast generated |
| `GET /api/resources/live` | 200 ✓ | Resource data |
| `GET /api/demand/history` | 200 ✓ | From PostgreSQL |
| `/api/v3/weather/current` | PUBLIC | No auth required |
| `/api/v3/location/search` | PUBLIC | No auth required |
| `/api/v3/recommendation/full` | PUBLIC | No auth required |
| `/api/v3/historical/demand` | PUBLIC | No auth required |

---

## 13. Frontend Integration

| Component | Backend Data | Status |
|---|---|---|
| GridStatus | `/api/grid/live` | PARTIAL (PGCB may be unreachable) |
| SolarAI | `/api/solar/live` | PARTIAL (no real solar data) |
| WindAI | `/api/wind/live` | PARTIAL (no real wind data) |
| WeatherWidget | `/api/v3/weather/current` | WORKING (Open-Meteo) |
| InteractiveMap | `/api/v3/location/search` | WORKING (SVG rendering) |
| DemandForecast | `/api/demand/forecast` | WORKING (synthetic model) |
| LocationIntelligence | `/api/v3/location/analyze` | WORKING |
| AIRecommendation | `/api/v3/recommendation/full` | WORKING |
| DeficitAlert | `/api/v3/recommendation/deficit` | WORKING |
| DataSourcesStatus | `/api/v3/sources` | WORKING |

---

## 14. Tests

| Category | Before | After |
|---|---|---|
| Unit tests | 273 | 348 |
| Integration tests | 75 | 75 |
| v3 phase tests | 0 | 75 |
| Validation script | 1 | 1 (broken on Windows) |
| **Total passing** | **348** | **348** |
| **Total failing** | **0** | **0 unit / 14 validation** |

**Test Quality Issues:**
- Extensive use of mocks (`MagicMock`, `patch`) — tests may not catch real integration failures
- `test_validation.py` reveals 14 endpoint correctness failures
- No numerical accuracy tests for physics models
- No provenance validation tests
- No data leakage regression tests
- Tests primarily assert status codes, not data quality

---

## 15. Build

| Component | Status | Notes |
|---|---|---|
| Backend | ✓ | FastAPI, Python 3.x, all dependencies installed |
| Frontend | ✓ | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Database | ✓ | PostgreSQL with SQLAlchemy + Alembic |
| Models | ✓ | 3 .pkl files present (solar, demand, weather-only-solar) |

---

## 16. Final Score

| Category | Score | Max | Notes |
|---|---|---|---|
| Data | 13 | 20 | Real PGCB scraper + Open-Meteo, but very limited history |
| Forecasting | 11 | 20 | Good architecture, but synthetic training data |
| Renewable models | 10 | 15 | Correct physics, not validated against real farms |
| Location/Grid | 8 | 15 | Good scoring, unverified coordinates |
| Map/UI | 4 | 10 | Functional SVG, not GIS |
| Security | 5 | 10 | Good middleware, auth not enforced, .env exposed |
| Testing | 3 | 5 | Good quantity, moderate quality |
| Documentation | 3 | 5 | Comprehensive but claims inflated |
| **TOTAL** | **57** | **100** | |

### **REAL SCORE: 5.7 / 10**

---

## 17. Remaining Limitations

### Critical (blocks production rating)
1. **Demand forecast trained on synthetic data** — Cannot be called "real forecasting" without real historical demand curves
2. **Map is SVG, not GIS** — No geographic tiles, no real basemap
3. **Authentication not enforced** — All v3 endpoints publicly accessible
4. **.env committed with credentials** — PostgreSQL password in plaintext
5. **Grid coordinates unverified** — No authoritative GIS source
6. **Very limited historical data** — Only 39 PGCB observations (2 days)

### Important (should be addressed)
7. Solar model not validated against real farm output
8. Wind model uses generic turbine curve
9. Resource maps are hardcoded estimates
10. Candidate generation is semi-dynamic (offsets around fixed substations)
11. Different substations listed in 3 different files
12. `test_validation.py` broken on Windows

### Minor (acceptable for current stage)
13. No Prometheus/OpenTelemetry metrics
14. No walk-back testing
15. FAOSTAT not integrated despite being registered
16. Some legacy timezone edge cases

---

## Appendix: What Would Be Needed for 8.5/10

To genuinely achieve 8.5/10, the following would be required:

1. **Real historical demand data** — Minimum 1 year of hourly PGCB observations (8,760+ records)
2. **Real-data forecasting** — Retrain XGBoost on actual PGCB historical demand
3. **Forecast validation against real observations** — Walk-forward MAE/RMSE from real data
4. **GIS map** — Leaflet or MapLibre with production tile provider
5. **Verified grid coordinates** — Authoritative source (PGCB, Power Division, OpenStreetMap)
6. **Authentication enforced** — API key requirement on sensitive endpoints
7. **.env removed from repo** — Credentials in environment variables only
8. **Solar model validated** — Compare predictions against real Bangladesh solar farm data
9. **Resource data from APIs** — Real irradiance/wind data from satellite/reanalysis datasets

These require external data sources that cannot be fabricated. The architecture is ready to accept real data — the gap is data acquisition, not code structure.
