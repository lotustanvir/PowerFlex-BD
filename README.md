# PowerFlex BD

Bangladesh-focused AI-powered energy management and Virtual Power Plant platform. Predicts energy demand and renewable generation, then recommends how available resources can be coordinated to reduce peak-load stress and potential load-shedding.

## Architecture

```
PowerFlex-BD/
├── backend/          # FastAPI REST API (Python)
│   ├── main.py       # App entry point, routers, health checks
│   ├── services/     # Service layer (solar, wind, grid, cache)
│   └── *.py          # Route modules (solar, wind, loadshield, etc.)
├── frontend/         # Next.js 16 + React 19 + TypeScript + Tailwind CSS
│   └── src/
│       ├── app/      # Page routes (dashboard, solar, wind, etc.)
│       ├── components/ # Dashboard widgets and UI components
│       ├── lib/      # API client, types, utilities
│       └── hooks/    # Custom React hooks
├── AI/               # Python ML scripts (training, prediction, forecasting)
├── data/             # Data storage
│   ├── processed/    # Cleaned/processed CSV data
│   └── raw/bpdb/     # Raw PGCB data and scraping scripts
├── models/           # Trained ML model files (.pkl)
├── tests/            # Integration tests
└── docs/             # Project documentation
```

## Energy Sources

Solar, Wind, Hydro, Biomass, Waste-to-Energy, Natural Gas, Coal, Nuclear

## AI Modules

| Module | Description |
|--------|-------------|
| LoadShield | Electricity demand forecasting |
| Solar Forecast | Solar generation prediction (weather-aware) |
| Wind Forecast | Wind power prediction |
| Renewable Potential | Renewable energy zone ranking |
| PowerFlex Optimizer | Resource dispatch optimization |

## Tech Stack

- **Backend**: Python 3.14, FastAPI, scikit-learn, XGBoost, Pandas, Joblib
- **Frontend**: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4
- **Data**: PGCB (Bangladesh Power Grid Company) public datasets

## Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` requests to the backend at `http://127.0.0.1:8000`.

### Environment Variables

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_URL=https://powerflexbd.com
```

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

## Running Tests

```bash
# Ensure backend is running on port 8000 first
python tests/test_validation.py
```
