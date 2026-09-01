export interface GridSnapshot {
  timestamp: string | null;
  current_demand_mw: number | null;
  current_generation_mw: number | null;
  supply_mw: number | null;
  demand_supply_gap_mw: number | null;
  load_shedding_mw: number | null;
  frequency_hz: number | null;
  generation_breakdown: Record<string, number | null>;
  imports: Record<string, number | null>;
  remarks: string;
  data_availability: Record<string, string>;
  data_classification: string;
  source_urls: Record<string, string>;
}

export interface GridLiveResponse {
  project: string;
  resource: string;
  status: string;
  data_source: string;
  live: boolean;
  grid_status: string;
  risk_level: string;
  data_classification: string;
  grid_snapshot: GridSnapshot | null;
  adapter: Record<string, unknown>;
}

export interface GridOfficialResponse {
  project: string;
  status: string;
  live: boolean;
  data_source: string;
  data_classification: string;
  source_url: string;
  data: {
    timestamp: string | null;
    demand_mw: number | null;
    supply_mw: number | null;
    deficit_mw: number | null;
    load_shedding_mw: number | null;
    remarks: string;
  } | null;
}

export interface GridStatusResponse {
  project: string;
  provider: string;
  adapter: string;
  configured_provider: string | null;
  api_configured: boolean;
  supported_providers: string[];
  pgcb_sources: Record<string, unknown>;
  message: string;
}

export interface LoadShieldResponse {
  project: string;
  module: string;
  status: string;
  current_situation: {
    grid: {
      demand_mw: number | null;
      supply_mw: number | null;
      deficit_mw: number | null;
      load_shedding_mw: number | null;
      source: string;
      data_classification: string;
    };
    risk_level?: string;
    system_status?: string;
  };
  forecast_situation: Record<string, unknown> | null;
  resource_analysis: Record<string, unknown> | null;
  zone_analysis: ZoneAnalysis[];
  current_recommendation: {
    status: string;
    initial_deficit_mw: number;
    total_support_mw: number;
    remaining_gap_mw: number;
    risk_level?: string;
    system_status?: string;
    recommended_deployment: Deployment[];
  } | null;
  forecast_preparation: Record<string, unknown> | null;
  message: string;
  data_source: Record<string, string>;
}

export interface ZoneAnalysis {
  zone: string;
  solar_available_mwh_per_1mw_24h: number;
  wind_available_mwh_per_1mw_24h: number;
  combined_renewable_score: number;
  hydro_available_mw: number;
  biomass_available_mw: number;
  biomass_electricity_potential_mwh_year: number;
  waste_available_mw: number;
  waste_electricity_potential_mwh_year: number;
  resource_source: Record<string, string>;
  rank: number;
}

export interface Deployment {
  rank: number;
  zone: string;
  resource: string;
  support_mw: number;
  recommended_installed_capacity_mw: number;
  reason: string;
}

export interface SolarLiveResponse {
  project: string;
  resource: string;
  status?: string;
  forecast_basis: string;
  data_source: string;
  forecast_hours: number;
  best_opportunity: {
    zone: string;
    timestamp: string;
    solar_radiation_wm2: number;
    predicted_generation_mw_per_1mw: number;
  };
  best_forecast_zone: {
    zone: string;
    expected_energy_mwh_per_1mw_24h: number;
  };
  zone_ranking: SolarZoneRanking[];
}

export interface SolarZoneRanking {
  rank: number;
  zone: string;
  expected_energy_mwh_per_1mw_24h: number;
}

export interface WindLiveResponse {
  project: string;
  resource: string;
  status?: string;
  forecast_basis: string;
  data_source: string;
  forecast_hours: number;
  turbine_assumption: Record<string, unknown>;
  best_opportunity: {
    zone: string;
    timestamp: string;
    wind_speed_100m_kmh: number;
    predicted_generation_mw_per_1mw: number;
  };
  best_forecast_zone: {
    zone: string;
    expected_energy_mwh_per_1mw_24h: number;
    modeled_capacity_factor_pct: number;
  };
  zone_ranking: WindZoneRanking[];
}

export interface WindZoneRanking {
  zone: string;
  expected_energy_mwh_per_1mw_24h: number;
  modeled_capacity_factor_pct: number;
  rank: number;
}

export interface ResourceItem {
  resource: string;
  generation_mw: number | null;
  available_mw: number | null;
  installed_capacity_mw: number | null;
  timestamp: string | null;
  source_metadata: {
    source: string;
    source_type: string;
    url: string;
    timestamp: string | null;
    data_classification: string;
  };
  resource_status: string;
  is_bangladesh_data: boolean;
  is_current: boolean;
  note: string;
}

export interface ResourcesLiveResponse {
  project: string;
  module: string;
  resource_count: number;
  pgcb_resources_available: number;
  timestamp: string;
  data_classification_summary: Record<string, number>;
  resources: Record<string, ResourceItem>;
}

export interface BiomassLiveResponse {
  project: string;
  resource: string;
  data_classification: string;
  resource_status: string;
  is_live: boolean;
  explanation: string;
  retrieved_at: string;
  sources: Array<Record<string, unknown>>;
  national_summary: Record<string, number>;
  divisions: BiomassDivision[];
}

export interface BiomassDivision {
  division: string;
  powerflex_zone: string;
  crop_residue_tonnes_year: number;
  animal_manure_tonnes_year: number;
  organic_waste_tonnes_year: number;
  biogas_m3_year: number;
  electricity_potential_mwh_year: number;
  average_potential_mw: number;
  dispatchable_mw: number;
}

export interface WasteLiveResponse {
  project: string;
  resource: string;
  data_classification: string;
  resource_status: string;
  is_live: boolean;
  explanation: string;
  national_summary: {
    total_operational_mw: number;
    total_planned_mw: number;
    calculated_potential_mw: number;
    calculated_dispatchable_mw: number;
    total_daily_waste_tonnes: number;
  };
  projects: WasteProject[];
  city_potentials: Record<string, unknown>;
  zone_allocation: Record<string, unknown>;
}

export interface WasteProject {
  project_name: string;
  project_id: string;
  location: {
    site: string;
    upazila: string;
    district: string;
    division: string;
    coordinates: { latitude: number; longitude: number };
    zone: string;
  };
  installed_capacity_mw: number;
  waste_input_tonnes_day: number;
  status: string;
  operational: boolean;
  generating: boolean;
  expected_cod: string | null;
  technology: string;
  data_classification: string;
  source: string;
}

export interface DemandForecastResponse {
  current_pgcb_demand_mw: number;
  forecast_peak_mw: number;
  peak_timestamp: string;
  hourly_forecast: HourlyForecast[];
  weather_data_status: string;
  model: string;
  data_source: string;
  data_classification: string;
  generated_at_utc: string;
  pgcb_source: {
    supply_mw: number;
    load_shedding_mw: number;
    pgcb_timestamp: string;
    data_classification: string;
  };
  training_metadata: Record<string, unknown>;
}

export interface HourlyForecast {
  hour_offset: number;
  timestamp_utc: string;
  timestamp_bst: string;
  hour_bst: number;
  predicted_demand_mw: number;
  temperature_c: number;
  data_classification: string;
}

export type DataClassification =
  | "OFFICIAL_PGCB"
  | "LIVE"
  | "MODEL_FORECAST"
  | "CALCULATED_FROM_OFFICIAL_DATA"
  | "STATIC_DOCUMENTED_DATA"
  | "DATA_UNAVAILABLE"
  | "PROTOTYPE";
