export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export const API_ENDPOINTS = {
  GRID_LIVE: `${API_BASE}/api/grid/live`,
  GRID_OFFICIAL: `${API_BASE}/api/grid/official`,
  GRID_STATUS: `${API_BASE}/api/grid/status`,
  LOADSHIELD_LIVE: `${API_BASE}/api/loadshield/live`,
  SOLAR_LIVE: `${API_BASE}/api/solar/live`,
  WIND_LIVE: `${API_BASE}/api/wind/live`,
  RESOURCES_LIVE: `${API_BASE}/api/resources/live`,
  BIOMASS_LIVE: `${API_BASE}/api/resources/biomass/live`,
  BIOMASS_DIVISIONS: `${API_BASE}/api/resources/biomass/divisions`,
  BIOMASS_POTENTIAL: `${API_BASE}/api/resources/biomass/potential`,
  BIOMASS_SOURCES: `${API_BASE}/api/resources/biomass/sources`,
  WASTE_LIVE: `${API_BASE}/api/resources/waste/live`,
  WASTE_PROJECTS: `${API_BASE}/api/resources/waste/projects`,
  WASTE_POTENTIAL: `${API_BASE}/api/resources/waste/potential`,
  WASTE_SOURCES: `${API_BASE}/api/resources/waste/sources`,
  DEMAND_FORECAST: `${API_BASE}/api/demand/forecast`,
  NUCLEAR: `${API_BASE}/api/resources/nuclear`,
  HEALTH: `${API_BASE}/api/health`,
  GRID_HISTORY: `${API_BASE}/api/grid/history`,
  PREDICTIONS_HISTORY: `${API_BASE}/api/predictions/history`,
  LOADSHIELD_HISTORY: `${API_BASE}/api/loadshield/history`,
  MODELS: `${API_BASE}/api/models`,
  MODELS_HISTORY: `${API_BASE}/api/models/history`,
  // v3 endpoints
  V3_WEATHER_CURRENT: `${API_BASE}/api/v3/weather/current`,
  V3_WEATHER_FORECAST: `${API_BASE}/api/v3/weather/forecast`,
  V3_WEATHER_ZONES: `${API_BASE}/api/v3/weather/zones`,
  V3_LOCATION_SEARCH: `${API_BASE}/api/v3/location/search`,
  V3_LOCATION_ANALYZE: `${API_BASE}/api/v3/location/analyze`,
  V3_LOCATION_COMPARE: `${API_BASE}/api/v3/location/compare`,
  V3_LOCATION_AREA: `${API_BASE}/api/v3/location/area-analysis`,
  V3_DEFICIT: `${API_BASE}/api/v3/recommendation/deficit`,
  V3_TECHNOLOGY: `${API_BASE}/api/v3/recommendation/technology`,
  V3_PLANT: `${API_BASE}/api/v3/recommendation/plant`,
  V3_FULL_RECOMMENDATION: `${API_BASE}/api/v3/recommendation/full`,
  V3_TECHNOLOGIES: `${API_BASE}/api/v3/recommendation/technologies`,
  V3_SOURCES: `${API_BASE}/api/v3/sources`,
  V3_SOURCES_SUMMARY: `${API_BASE}/api/v3/sources/summary`,
  V3_DECISION_SUPPORT: `${API_BASE}/api/v3/recommendation/decision-support`,
  V3_DECISION_SUPPORT_HEALTH: `${API_BASE}/api/v3/recommendation/decision-support/health`,
} as const;

export interface ApiResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export async function fetchApi<T>(
  url: string,
  signal?: AbortSignal
): Promise<{ data: T | null; error: string | null }> {
  try {
    const response = await fetch(url, {
      signal,
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return {
        data: null,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return { data: null, error: null };
    }
    return {
      data: null,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
