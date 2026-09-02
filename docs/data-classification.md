# Data Classification System

## Overview

PowerFlex BD v2.0 implements a centralized data classification system to ensure transparency and scientific accuracy. Every important energy value returned by the backend includes metadata indicating its classification, source, timestamp, and methodology.

## Classification Enum

| Classification | Description | Badge Color |
|---------------|-------------|-------------|
| `OFFICIAL` | Verified data from government/institutional sources | Green |
| `MEASURED` | Physical telemetry from operational sensors | Green |
| `LIVE_FEED` | Near-real-time data from external API feeds | Blue |
| `DELAYED` | Official data with significant time lag | Amber |
| `FORECAST` | Weather-driven or ML-driven predictions | Blue |
| `CALCULATED` | Engineering/physics-based calculations | Amber |
| `POTENTIAL` | Theoretical/geographic potential estimate | Purple |
| `SCENARIO` | Explicit scenario assumptions for analysis | Slate |
| `PROJECT` | Planned or announced projects | Red |
| `UNDER_CONSTRUCTION` | Physically under construction | Red |
| `UNDER_COMMISSIONING` | Under commissioning and testing | Orange |
| `EXPERIMENTAL` | Research/prototype models, not validated | Yellow |
| `PROTOTYPE` | Placeholder values awaiting real data | Slate |
| `DATA_UNAVAILABLE` | Data source unavailable or failed | Red |
| `UNKNOWN` | Classification cannot be determined | Gray |

## Provenance Metadata

Every classified value includes:

```json
{
  "value": 123.45,
  "unit": "MW",
  "classification": "FORECAST",
  "classification_display": "Forecast",
  "source": "Open-Meteo + PowerFlex Solar AI",
  "timestamp": "ISO-8601 timestamp",
  "last_verified": "ISO-8601 timestamp or null",
  "confidence": 0.85,
  "methodology": "Brief explanation of how this value was produced"
}
```

## Data Sources

| Source | Classification | Update Frequency |
|--------|---------------|-----------------|
| PGCB ERP Portal | OFFICIAL | On-demand HTML scrape |
| Open-Meteo Weather API | LIVE_FEED | Hourly forecast updates |
| FAOSTAT (UN FAO) | DELAYED | Annual |
| PowerFlex Solar AI | FORECAST | On-demand (300s cache) |
| PowerFlex Wind Power Curve | CALCULATED | On-demand (300s cache) |
| PowerFlex Demand Forecast | FORECAST | On-demand (300s cache) |

## Key Rules

1. **Never silently change a value's classification** simply because it is displayed on a dashboard
2. **Always include provenance metadata** in API responses
3. **Return DATA_UNAVAILABLE** instead of inventing fake values when data sources fail
4. **Clearly distinguish** between measured, forecast, calculated, and potential values
5. **Document methodology** for every important calculation
