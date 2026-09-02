# Limitations and Known Issues

## Critical Limitations

### 1. No Real Solar Generation Data
- The Solar AI model was trained on **synthetic targets** derived from the formula `(irradiance / 1000) * 0.85`
- No actual solar farm generation data from Bangladesh is available for training
- **Impact**: Solar forecasts are weather-driven estimates, not predictions of real plant output
- **Status**: EXPERIMENTAL — not validated against real data

### 2. No Real Wind Generation Data
- Wind estimates use a simplified prototype power curve applied to Open-Meteo 100m wind speed data
- No actual wind turbine telemetry is available
- **Impact**: Wind estimates are engineering calculations, not measured generation
- **Status**: EXPERIMENTAL — not validated against real data

### 3. Synthetic Demand Forecast Training
- The demand forecasting model was trained on **synthetic hourly profiles** based on published Bangladesh load research patterns
- The model is anchored to real-time PGCB demand but the forecast shape comes from synthetic data
- **Impact**: Demand forecasts may not accurately capture real demand patterns
- **Status**: EXPERIMENTAL — needs real historical data for production use

### 4. PGCB HTML Scraping Fragility
- Grid data is obtained by scraping the PGCB ERP website
- No API contract exists — liable to break on any layout change
- **Impact**: Grid data may become unavailable without notice
- **Status**: Primary data source — fragile by nature

### 5. Prototype Resource Capacities
- Solar (1000 MW), Wind (500 MW), Hydro (230 MW), Battery (500 MW), Flexible Demand (500 MW) are **PROTOTYPE values**
- These are NOT actual installed or available capacities
- **Impact**: LoadShield optimization results are scenario-based, not operational recommendations
- **Status**: Awaiting official plant-level data

### 6. Biomass and Waste-to-Energy
- All biomass values are **CALCULATED_POTENTIAL** — no operational plants exist
- Waste-to-energy values include one under-construction project (42.5 MW)
- **Impact**: These resources cannot be dispatched in reality
- **Status**: Calculated from FAOSTAT and city waste data

### 7. Nuclear (Rooppur)
- Rooppur Nuclear Power Plant (2,400 MW) is under commissioning
- Not yet generating to grid
- **Impact**: No nuclear generation available
- **Status**: UNDER_COMMISSIONING

## Data Integrity Rules

1. **Never fabricate data** — return DATA_UNAVAILABLE when sources fail
2. **Never present forecasts as measurements** — all predictions are clearly labeled FORECAST
3. **Never present potential as dispatchable capacity** — calculated potential is separate from available generation
4. **Never present scenario assumptions as real assets** — prototype values are explicitly marked SCENARIO/PROTOTYPE
5. **Always include provenance** — every important value has source, timestamp, and methodology

## What PowerFlex BD Is NOT

- **NOT** a real-time grid control system
- **NOT** an official PGCB/BPDB data source
- **NOT** a dispatch command system
- **NOT** a production-validated forecasting platform
- **NOT** a replacement for official grid data

## What PowerFlex BD IS

- An independent energy intelligence and decision-support platform
- A scenario analysis and visualization tool
- A research and prototyping platform for energy analytics
- A demonstration of how weather data and engineering models can inform energy planning
- A transparent, scientifically defensible platform that clearly distinguishes data types
