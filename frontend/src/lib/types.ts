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

export interface GridRiskComponent {
  name: string;
  score: number;
  weight: number;
  detail: string;
  raw_value: number;
  unit: string;
}

export interface GridRiskScenario {
  label: string;
  risk_score: number;
  risk_level: string;
  demand_mw: number;
  supply_mw: number;
  gap_mw: number;
}

export interface GridRiskResponse {
  composite_score: number;
  risk_level: string;
  components: GridRiskComponent[];
  scenarios: Record<string, GridRiskScenario>;
  timestamp: string;
  data_sources: Record<string, string>;
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
  grid_risk: GridRiskResponse | null;
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

export interface ForecastMetadata {
  forecast_available: boolean;
  production_ready: boolean;
  forecast_type: string;
  forecast_classification: string;
  observation_count: number;
  minimum_required_observations: number;
  data_coverage_hours: number;
  training_data_synthetic: boolean;
  model_trained_on_synthetic: boolean;
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
  forecast_metadata?: ForecastMetadata;
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

// =========================================================
// HISTORY API RESPONSES
// =========================================================

export interface GridHistoryItem {
  id: number;
  timestamp: string | null;
  demand_mw: number | null;
  supply_mw: number | null;
  load_shedding_mw: number | null;
  deficit_mw: number | null;
  gas_mw: number | null;
  liquid_fuel_mw: number | null;
  coal_mw: number | null;
  hydro_mw: number | null;
  solar_mw: number | null;
  wind_mw: number | null;
  hvdc_mw: number | null;
  import_mw: number | null;
  grid_status: string | null;
  risk_level: string | null;
}

export interface GridHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  data: GridHistoryItem[];
}

export interface PredictionHistoryItem {
  id: number;
  timestamp: string | null;
  model_type: string;
  zone: string | null;
  predicted_mw: number | null;
  actual_mw: number | null;
  model_version: string | null;
}

export interface PredictionsHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  data: PredictionHistoryItem[];
}

export interface LoadShieldHistoryItem {
  id: number;
  timestamp: string | null;
  demand_mw: number | null;
  supply_mw: number | null;
  deficit_mw: number | null;
  solar_mw: number | null;
  wind_mw: number | null;
  hydro_mw: number | null;
  biomass_mw: number | null;
  waste_mw: number | null;
  battery_mw: number | null;
  flexible_mw: number | null;
  remaining_gap: number | null;
  status: string | null;
  risk_level: string | null;
  zone_breakdown: unknown[] | null;
}

export interface LoadShieldHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  data: LoadShieldHistoryItem[];
}

export interface ModelRegistryItem {
  id: number;
  model_type: string;
  model_path: string | null;
  trained_at: string | null;
  training_samples: number | null;
  mae: number | null;
  rmse: number | null;
  r2: number | null;
  features: string[] | null;
  is_active: boolean;
}

export interface ModelRegistryResponse {
  total: number;
  limit: number;
  offset: number;
  data: ModelRegistryItem[];
}

// =========================================================
// V3 API RESPONSES
// =========================================================

export interface WeatherDataPoint {
  latitude: number;
  longitude: number;
  timestamp: string;
  temperature_c: number | null;
  humidity_percent: number | null;
  wind_speed_kmh: number | null;
  wind_direction_degree: number | null;
  cloud_cover_percent: number | null;
  precipitation_mm: number | null;
  pressure_hpa: number | null;
  solar_radiation_wm2: number | null;
  source: string;
  quality: string;
}

export interface WeatherResponse {
  status: string;
  data: WeatherDataPoint;
  classification: string;
  source: string;
  retrieved_at: string;
}

export interface WeatherForecastResponse {
  status: string;
  data: {
    latitude: number;
    longitude: number;
    timezone: string;
    hourly: WeatherDataPoint[];
    provider: string;
    classification: string;
    quality: string;
    hour_count: number;
  };
  classification: string;
}

export interface LocationCandidate {
  name: string;
  latitude: number;
  longitude: number;
  technology: string;
  grid_information: {
    substation: string;
    distance_km: number;
    voltage_kv: number;
    grid_proximity: string;
  };
}

export interface LocationSearchResponse {
  status: string;
  search_center: { latitude: number; longitude: number } | null;
  radius_km: number;
  technology_filter: string | null;
  candidate_count: number;
  candidates: LocationCandidate[];
  timestamp: string;
}

export interface SiteScore {
  solar_score: number;
  wind_score: number;
  generation_score: number;
  grid_score: number;
  reliability_score: number;
  overall_score: number;
  components: Record<string, number>;
  warnings: string[];
}

export interface LocationAnalysisResponse {
  status: string;
  location: { latitude: number; longitude: number };
  technology: string;
  capacity_mw: number;
  grid_information: {
    substation: string;
    distance_km: number;
    voltage_kv: number;
    grid_proximity: string;
  };
  weather: WeatherDataPoint | null;
  site_score: SiteScore;
  expected_generation_mw: number | null;
  analysis_timestamp: string;
  classification: string;
  disclaimer: string;
}

export interface DeficitAnalysis {
  forecast_demand_mw: number | null;
  forecast_supply_mw: number | null;
  forecast_gap_mw: number | null;
  gap_type: string;
  severity: string;
  confidence: number | null;
  timestamp: string;
  notes: string;
}

export interface DeficitResponse {
  status: string;
  analysis: DeficitAnalysis;
  grid_status: string;
  data_source: string;
  classification: string;
  timestamp: string;
}

export interface TechnologyRecommendation {
  technology: string;
  capacity_factor: number | null;
  expected_generation_mw_per_mw: number | null;
  suitability_score: number;
  reasons: string[];
  warnings: string[];
}

export interface TechnologyResponse {
  status: string;
  deficit_mw: number;
  recommendation: TechnologyRecommendation;
  classification: string;
  timestamp: string;
}

export interface PlantRecommendation {
  technology: string;
  capacity_mw: number;
  expected_generation_mw: number | null;
  expected_daily_mwh: number | null;
  expected_annual_gwh: number | null;
  prediction_interval: { lower: number; upper: number } | null;
  location: {
    latitude: number;
    longitude: number;
    grid_information: Record<string, unknown>;
    score: { overall_score: number };
  };
  reasons: string[];
  warnings: string[];
}

export interface PlantResponse {
  status: string;
  recommendation: PlantRecommendation;
  deficit_mw: number;
  classification: string;
  model: string;
  timestamp: string;
  disclaimer: string;
}

export interface FullRecommendation {
  forecast_demand_mw: number | null;
  forecast_supply_mw: number | null;
  expected_deficit_mw: number | null;
  recommended_technology: TechnologyRecommendation | null;
  recommended_capacity_mw: number | null;
  recommended_location: Record<string, unknown> | null;
  expected_hourly_generation_mw: number | null;
  expected_daily_energy_mwh: number | null;
  expected_annual_energy_gwh: number | null;
  prediction_interval: { lower: number; upper: number } | null;
  site_score: number | null;
  reasons: string[];
  warnings: string[];
  data_quality: string;
  model_used: string;
  timestamp: string;
  disclaimer: string;
}

export interface FullRecommendationResponse {
  status: string;
  recommendation: FullRecommendation;
  timestamp: string;
}

export interface DataSource {
  source_id: string;
  name: string;
  organization: string;
  source_type: string;
  url: string | null;
  access_method: string;
  data_type: string;
  update_frequency: string;
  historical_coverage: string;
  reliability: string;
  license_notes: string;
  classification: string;
  status: string;
  active: boolean;
  last_success: string | null;
  last_failure: string | null;
  failure_count: number;
  success_count: number;
  description: string;
  notes: string;
}

export interface SourcesResponse {
  status: string;
  sources: Record<string, DataSource>;
  summary: {
    total_sources: number;
    active_sources: number;
    verified_sources: number;
    unverified_sources: number;
    ml_models: number;
    calculated: number;
    classification_summary: Record<string, number>;
  };
  timestamp: string;
}

export interface TechnologyProfile {
  capacity_factor: number;
  intermittency: string;
  weather_dependence: string;
  scalability: string;
  cost_trend: string;
  reasons: string[];
  warnings: string[];
}

export interface TechnologiesResponse {
  status: string;
  technologies: Record<string, TechnologyProfile>;
  classification: string;
}

// Phase 6: Decision Support Types
export interface RecommendationEvidence {
  trigger: string;
  current_value: number | null;
  threshold: number | null;
  source_data_classification: string | null;
  source_type: string;
  data_status: string;
  data_freshness_seconds: number | null;
  explanation: string;
}

export interface Recommendation {
  type: string;
  priority: string;
  title: string;
  summary: string;
  detailed_explanation: string;
  evidence: RecommendationEvidence;
  expected_impact: string;
  confidence: number;
  timestamp: string;
  deduplication_key: string;
  expires_at: string | null;
  metadata: Record<string, unknown>;
}

export interface DecisionSupportSystemInputs {
  grid_demand_mw: number | null;
  grid_supply_mw: number | null;
  grid_status: string;
  grid_data_classification: string;
  grid_timestamp: string | null;
  solar_generation_mw: number | null;
  wind_generation_mw: number | null;
  solar_data_classification: string;
  wind_data_classification: string;
  risk_score: number | null;
  risk_level: string;
  forecast_available: boolean;
  forecast_peak_mw: number | null;
  forecast_confidence: number | null;
  independent_observations: number;
  forecast_ready: boolean;
  data_quality_issues: string[];
  missing_inputs: string[];
}

export interface DecisionSupportResponse {
  status: string;
  timestamp: string;
  system_inputs: DecisionSupportSystemInputs;
  recommendations: Recommendation[];
  total_recommendations: number;
  missing_inputs: string[];
  metadata: {
    source_type: string;
    data_status: string;
    confidence_average: number;
    forecast_available: boolean;
    independent_observations: number;
  };
}

export interface DecisionSupportHealthResponse {
  independent_observations: number;
  grid_status: string;
  forecast_ready: boolean;
  data_quality_score: number;
}
