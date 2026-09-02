# PowerFlex BD - Repository Guide

## Project Overview

PowerFlex BD is a Bangladesh-focused AI-powered energy management and Virtual Power Plant platform. It predicts energy demand and renewable generation, then recommends how available resources can be coordinated to reduce peak-load stress and potential load-shedding.

## Architecture

```
PowerFlex-BD/
├── backend/          # FastAPI REST API (Python)
│   ├── main.py       # App entry point, routers, health checks
│   ├── services/     # Service layer (solar, wind, grid, cache)
│   ├── collectors/   # Data collection modules
│   ├── middleware/    # Rate limiting, security
│   ├── observability/ # Structured logging, metrics
│   └── *.py          # Route modules (solar, wind, loadshield, etc.)
├── frontend/         # Next.js 16 + React 19 + TypeScript + Tailwind CSS
│   └── src/
│       ├── app/      # Page routes (dashboard, solar, wind, etc.)
│       ├── components/ # Dashboard widgets and UI components
│       ├── lib/      # API client, types, utilities
│       └── hooks/    # Custom React hooks
├── AI/               # Python ML scripts (training, prediction, forecasting)
├── database/         # SQLAlchemy models and connection
├── data/             # Data storage
│   ├── processed/    # Cleaned/processed CSV data
│   └── raw/bpdb/     # Raw PGCB data and scraping scripts
├── models/           # Trained ML model files (.pkl)
├── tests/            # Integration tests
└── docs/             # Project documentation
```

## How to Run the Backend

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn backend.main:app --reload --port 8000
```

## How to Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` requests to the backend at `http://127.0.0.1:8000`.

## How to Run Tests

```bash
# Ensure backend is running on port 8000 first
python tests/test_validation.py
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/powerflex` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000,http://127.0.0.1:3000` |
| `BACKEND_PORT` | Backend server port | `8000` |
| `CACHE_BACKEND` | Cache backend (`memory` or `redis`) | `memory` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `RATE_LIMIT_RPM` | Rate limit (requests per minute) | `60` |
| `TRUSTED_HOSTS` | Allowed host headers | `localhost,127.0.0.1` |
| `APP_ENV` | Environment mode | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Data Classification System

PowerFlex BD uses a standardized data classification system:

| Classification | Description |
|---------------|-------------|
| `OFFICIAL` | Verified data from government/institutional sources |
| `MEASURED` | Physical telemetry from operational sensors |
| `LIVE_FEED` | Near-real-time data from external feeds |
| `DELAYED` | Official data with significant time lag |
| `FORECAST` | Weather-driven or ML-driven predictions |
| `CALCULATED` | Engineering/physics-based calculations |
| `POTENTIAL` | Theoretical/geographic potential |
| `SCENARIO` | Explicit scenario assumptions |
| `PROJECT` | Planned/announced projects |
| `UNDER_CONSTRUCTION` | Physically under construction |
| `UNDER_COMMISSIONING` | Under commissioning/testing |
| `EXPERIMENTAL` | Research/prototype models not validated for production |
| `PROTOTYPE` | Placeholder values awaiting real data |
| `DATA_UNAVAILABLE` | Data source unavailable or failed |

## Key Files

| File | Description |
|------|-------------|
| `backend/main.py` | FastAPI app entry point, router registration, middleware |
| `backend/loadshield.py` | Core LoadShield optimization engine |
| `backend/optimizer.py` | Multi-resource deficit optimization |
| `backend/optimizer_math.py` | Mathematical (LP) optimization using scipy |
| `backend/solar.py` | Solar AI forecast endpoint |
| `backend/wind.py` | Wind power curve model endpoint |
| `backend/grid.py` | PGCB ERP scraper for grid data |
| `backend/demand_forecast.py` | Demand forecasting with XGBoost |
| `backend/data_classification.py` | Data classification enum and helpers |
| `backend/services/cache.py` | In-memory TTL cache |
| `backend/services/cache_v2.py` | Cache with Redis support |
| `backend/middleware/rate_limiter.py` | Per-IP rate limiting middleware |

## Energy Sources

Solar, Wind, Hydro, Biomass, Waste-to-Energy, Natural Gas, Coal, Nuclear

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Project info |
| `GET /health` | Health check (all services) |
| `GET /api/solar/live` | Live solar generation data |
| `GET /api/wind/live` | Live wind generation data |
| `GET /api/grid/status` | Grid status from PGCB |
| `GET /api/loadshield` | Load shield analysis |
| `GET /api/demand/forecast` | Demand forecast |
| `GET /api/demand/history` | Historical demand data |
| `GET /api/resources` | All energy resources |
| `GET /api/biomass` | Biomass data |
| `GET /api/waste` | Waste-to-energy data |
| `GET /api/renewable/live` | Combined solar + wind |
