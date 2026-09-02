# Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                         │
├─────────────────────────────────────────────────────────────────┤
│  PGCB ERP Portal (HTML scraper)      │ Official grid data       │
│  Open-Meteo Weather API              │ Weather forecasts        │
│  FAOSTAT (UN FAO)                    │ Crop/livestock data      │
│  City Corporation Data               │ Waste generation data    │
│  World Nuclear Association           │ Nuclear project status   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       DATA COLLECTORS                           │
├─────────────────────────────────────────────────────────────────┤
│  grid.py              │ PGCB HTML scraper (BeautifulSoup)       │
│  solar.py             │ Open-Meteo + Solar AI model             │
│  wind.py              │ Open-Meteo + Wind power curve           │
│  demand_forecast.py   │ Open-Meteo + Demand forecast model      │
│  biomass_fetcher.py   │ FAOSTAT API + fallback data             │
│  waste_fetcher.py     │ Static project data + calculations      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA CLASSIFICATION                         │
├─────────────────────────────────────────────────────────────────┤
│  data_classification.py │ Centralized classification system     │
│                         │ OFFICIAL, MEASURED, LIVE_FEED,        │
│                         │ FORECAST, CALCULATED, POTENTIAL,      │
│                         │ SCENARIO, PROTOTYPE, DATA_UNAVAILABLE │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        PROCESSING                               │
├─────────────────────────────────────────────────────────────────┤
│  optimizer.py           │ Scenario-based deficit optimization   │
│  biomass_calculator.py  │ Biomass potential from crop data      │
│  waste_calculator.py    │ WtE potential from city waste data    │
│  resource_data.py       │ Unified resource data service         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          STORAGE                                │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL + SQLAlchemy │ Grid snapshots, predictions,         │
│                          │ dispatches, model registry            │
│  In-memory TTL Cache     │ Grid, solar, wind data caching       │
│  CSV files               │ Historical data, raw data            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                           API                                   │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI routers         │ /api/grid/*, /api/solar/*,           │
│                          │ /api/wind/*, /api/demand/*,          │
│                          │ /api/loadshield/*, /api/resources/*, │
│                          │ /api/history/*, /api/biomass/*,      │
│                          │ /api/waste/*                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
├─────────────────────────────────────────────────────────────────┤
│  Next.js App Router       │ 11 routes (dashboard, solar, wind, │
│                           │ loadshield, zones, resources, etc.) │
│  React Components         │ Dashboard widgets, charts, badges   │
│  Tailwind CSS             │ Dark theme, responsive design       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

1. **Data Transparency**: Every value includes provenance metadata
2. **Classification First**: Data is classified before being served
3. **No Fabrication**: Return DATA_UNAVAILABLE instead of fake data
4. **Separation of Concerns**: Clear layers from data sources to frontend
5. **Backward Compatibility**: Existing APIs continue to work with enhanced metadata

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `demand_history` | Historical demand snapshots from PGCB |
| `grid_snapshots` | Grid state snapshots (generation breakdown) |
| `ai_predictions` | ML prediction log with features and metrics |
| `loadshield_dispatches` | Optimization results and recommendations |
| `model_registry` | ML model tracking and versioning |
