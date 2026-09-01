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
