"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { LocationSearchResponse, LocationCandidate } from "@/lib/types";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

// Leaflet imports — loaded client-side only via dynamic() in CommandCenter
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// =========================================================
// TYPES
// =========================================================

interface GridSubstation {
  name: string;
  lat: number;
  lon: number;
  voltage_kv: number;
  verification_status?: string;
  region?: string;
  capacity_mva?: number;
}

interface SolarZone {
  zone: string;
  lat: number;
  lon: number;
  avg_mw_per_1mw: number;
  max_mw_per_1mw: number;
}

interface WindZone {
  zone: string;
  lat: number;
  lon: number;
  avg_speed_kmh: number;
  classification: string;
}

interface LayerVisibility {
  substations: boolean;
  solarZones: boolean;
  windZones: boolean;
  candidates: boolean;
}

interface MapProps {
  className?: string;
}

// =========================================================
// CONSTANTS — Bangladesh
// =========================================================

const BANGLADESH_CENTER: [number, number] = [23.6850, 90.3563];
const BANGLADESH_BOUNDS: L.LatLngBoundsExpression = [
  [20.5, 88.0],
  [26.7, 92.7],
];

// =========================================================
// STATIC DATA — Substations (UNVERIFIED, from grid_canonical.py)
// All coordinates from PUBLIC_INFO, not authoritative BPDB/PGCB sources.
// =========================================================

const SUBSTATIONS: GridSubstation[] = [
  { name: "Ghorashal", lat: 24.0167, lon: 90.9833, voltage_kv: 400, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Haripur", lat: 24.05, lon: 90.95, voltage_kv: 400, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Meghnaghat", lat: 23.4833, lon: 90.55, voltage_kv: 400, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Barcelona", lat: 23.75, lon: 90.45, voltage_kv: 230, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Aminbazar", lat: 23.78, lon: 90.35, voltage_kv: 230, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Comilla", lat: 23.45, lon: 91.2, voltage_kv: 230, region: "COMILLA", verification_status: "UNVERIFIED" },
  { name: "Mymensingh", lat: 24.75, lon: 90.4, voltage_kv: 230, region: "MYMENSINGH", verification_status: "UNVERIFIED" },
  { name: "Rajshahi", lat: 24.37, lon: 88.6, voltage_kv: 230, region: "RAJSHAHI", verification_status: "UNVERIFIED" },
  { name: "Rangpur", lat: 25.75, lon: 89.25, voltage_kv: 230, region: "RANGPUR", verification_status: "UNVERIFIED" },
  { name: "Sylhet", lat: 24.9, lon: 91.87, voltage_kv: 230, region: "SYLHET", verification_status: "UNVERIFIED" },
  { name: "Khulna", lat: 22.85, lon: 89.55, voltage_kv: 230, region: "KHULNA", verification_status: "UNVERIFIED" },
  { name: "Ishwardi", lat: 24.13, lon: 89.05, voltage_kv: 230, region: "RAJSHAHI", verification_status: "UNVERIFIED" },
  { name: "Barisal", lat: 22.7, lon: 90.37, voltage_kv: 132, region: "BARISHAL", verification_status: "UNVERIFIED" },
  { name: "Cox Bazar", lat: 21.45, lon: 92.0, voltage_kv: 132, region: "CHATTOGRAM", verification_status: "UNVERIFIED" },
  { name: "Madaripur", lat: 23.17, lon: 90.15, voltage_kv: 132, region: "DHAKA", verification_status: "UNVERIFIED" },
  { name: "Bogra", lat: 24.85, lon: 89.37, voltage_kv: 132, region: "RAJSHAHI", verification_status: "UNVERIFIED" },
  { name: "Dinajpur", lat: 25.63, lon: 88.63, voltage_kv: 132, region: "RANGPUR", verification_status: "UNVERIFIED" },
  { name: "Jamalpur", lat: 24.93, lon: 89.95, voltage_kv: 132, region: "MYMENSINGH", verification_status: "UNVERIFIED" },
];

// =========================================================
// STATIC DATA — Solar Zones (MODELED, from solar_zone_summary.csv)
// Avg generation per 1MW installed, from Open-Meteo weather data
// combined with synthetic XGBoost model. NOT measured plant output.
// =========================================================

const SOLAR_ZONES: SolarZone[] = [
  { zone: "Chittagong", lat: 22.3569, lon: 91.7832, avg_mw_per_1mw: 0.167, max_mw_per_1mw: 0.836 },
  { zone: "Comilla", lat: 23.4607, lon: 91.1809, avg_mw_per_1mw: 0.157, max_mw_per_1mw: 0.825 },
  { zone: "Sylhet", lat: 24.8949, lon: 91.8687, avg_mw_per_1mw: 0.154, max_mw_per_1mw: 0.809 },
  { zone: "Rangpur", lat: 25.7439, lon: 89.2752, avg_mw_per_1mw: 0.152, max_mw_per_1mw: 0.818 },
  { zone: "Barishal", lat: 22.7010, lon: 90.3535, avg_mw_per_1mw: 0.152, max_mw_per_1mw: 0.814 },
  { zone: "Rajshahi", lat: 24.3745, lon: 88.6042, avg_mw_per_1mw: 0.150, max_mw_per_1mw: 0.852 },
  { zone: "Dhaka", lat: 23.8103, lon: 90.4125, avg_mw_per_1mw: 0.150, max_mw_per_1mw: 0.816 },
  { zone: "Khulna", lat: 22.8456, lon: 89.5403, avg_mw_per_1mw: 0.149, max_mw_per_1mw: 0.814 },
  { zone: "Mymensingh", lat: 24.7471, lon: 90.4203, avg_mw_per_1mw: 0.146, max_mw_per_1mw: 0.804 },
];

// =========================================================
// STATIC DATA — Wind Zones (CALCULATED, from BPDB weather data)
// Based on Open-Meteo reanalysis. NOT measured turbine output.
// =========================================================

const WIND_ZONES: WindZone[] = [
  { zone: "Cox's Bazar Coast", lat: 21.43, lon: 92.00, avg_speed_kmh: 18.5, classification: "HIGH" },
  { zone: "Chittagong Coast", lat: 22.36, lon: 91.78, avg_speed_kmh: 15.2, classification: "MODERATE" },
  { zone: "Sylhet Highlands", lat: 24.89, lon: 91.87, avg_speed_kmh: 12.8, classification: "MODERATE" },
  { zone: "Barishal Delta", lat: 22.70, lon: 90.35, avg_speed_kmh: 11.5, classification: "LOW" },
  { zone: "Rajshahi Plains", lat: 24.37, lon: 88.60, avg_speed_kmh: 10.2, classification: "LOW" },
  { zone: "Rangpur North", lat: 25.74, lon: 89.28, avg_speed_kmh: 9.8, classification: "LOW" },
];

// =========================================================
// HELPERS
// =========================================================

function getVoltageColor(voltageKv: number): string {
  if (voltageKv >= 400) return "#ef4444";
  if (voltageKv >= 230) return "#f97316";
  return "#eab308";
}

function getVerificationBadge(status?: string): string {
  switch (status) {
    case "VERIFIED": return "\u2713 VERIFIED";
    case "PARTIALLY_VERIFIED": return "~ PARTIAL";
    case "UNVERIFIED": return "? UNVERIFIED";
    case "ESTIMATE": return "\u2248 ESTIMATE";
    default: return "? UNKNOWN";
  }
}

function getVerificationColor(status?: string): string {
  switch (status) {
    case "VERIFIED": return "#22c55e";
    case "PARTIALLY_VERIFIED": return "#eab308";
    case "UNVERIFIED": return "#f59e0b";
    case "ESTIMATE": return "#94a3b8";
    default: return "#94a3b8";
  }
}

// =========================================================
// ICON FACTORIES
// =========================================================

function createSubstationIcon(voltageKv: number): L.DivIcon {
  const color = getVoltageColor(voltageKv);
  const label = voltageKv >= 400 ? "4" : voltageKv >= 230 ? "2" : "1";
  return L.divIcon({
    className: "substation-marker",
    html: `<div style="width:22px;height:22px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:bold;color:white;">${label}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

function createSolarIcon(): L.DivIcon {
  return L.divIcon({
    className: "solar-zone-marker",
    html: `<div style="width:28px;height:28px;background:#facc15;border:2px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;font-size:14px;">\u2600</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function createWindIcon(): L.DivIcon {
  return L.divIcon({
    className: "wind-zone-marker",
    html: `<div style="width:28px;height:28px;background:#22d3ee;border:2px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;font-size:14px;">\uD83C\uDF2C\uFE0F</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function createCandidateIcon(technology: string): L.DivIcon {
  let color = "#94a3b8";
  let symbol = "\u25CF";
  if (technology === "SOLAR") { color = "#facc15"; symbol = "\u2600"; }
  else if (technology === "WIND") { color = "#22d3ee"; symbol = "\uD83C\uDF2C\uFE0F"; }
  else if (technology === "GAS") { color = "#f97316"; symbol = "\u26A1"; }
  return L.divIcon({
    className: "candidate-marker",
    html: `<div style="width:18px;height:18px;background:${color};border:2px solid white;border-radius:3px;box-shadow:0 2px 4px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;font-size:10px;">${symbol}</div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

// =========================================================
// POPUP HTML BUILDERS
// =========================================================

function substationPopup(sub: GridSubstation): string {
  const badge = getVerificationBadge(sub.verification_status);
  const badgeColor = getVerificationColor(sub.verification_status);
  return `<div style="min-width:180px;font-family:system-ui;font-size:12px;">
    <div style="font-weight:600;font-size:13px;margin-bottom:4px;">${sub.name}</div>
    <div style="color:#555;">Voltage: ${sub.voltage_kv} kV</div>
    ${sub.region ? `<div style="color:#555;">Region: ${sub.region}</div>` : ""}
    <div style="color:${badgeColor};font-weight:500;margin-top:4px;">${badge}</div>
    <div style="color:#999;font-size:10px;margin-top:4px;">Source: PUBLIC_INFO (not BPDB/PGCB verified)</div>
    <div style="color:#999;font-size:10px;">${sub.lat.toFixed(4)}, ${sub.lon.toFixed(4)}</div>
  </div>`;
}

function solarZonePopup(zone: SolarZone): string {
  return `<div style="min-width:180px;font-family:system-ui;font-size:12px;">
    <div style="font-weight:600;font-size:13px;margin-bottom:4px;">${zone.zone} Solar Zone</div>
    <div style="color:#555;">Avg: ${(zone.avg_mw_per_1mw * 100).toFixed(1)}% capacity</div>
    <div style="color:#555;">Peak: ${(zone.max_mw_per_1mw * 100).toFixed(1)}% capacity</div>
    <div style="color:#92400e;font-weight:500;margin-top:4px;">MODELED (weather-driven, not measured)</div>
    <div style="color:#999;font-size:10px;margin-top:4px;">Source: Open-Meteo + Solar AI forecast</div>
    <div style="color:#999;font-size:10px;">${zone.lat.toFixed(4)}, ${zone.lon.toFixed(4)}</div>
  </div>`;
}

function windZonePopup(zone: WindZone): string {
  return `<div style="min-width:180px;font-family:system-ui;font-size:12px;">
    <div style="font-weight:600;font-size:13px;margin-bottom:4px;">${zone.zone}</div>
    <div style="color:#555;">Avg wind: ${zone.avg_speed_kmh} km/h</div>
    <div style="color:#555;">Rating: ${zone.classification}</div>
    <div style="color:#0369a1;font-weight:500;margin-top:4px;">CALCULATED (weather reanalysis, not turbine data)</div>
    <div style="color:#999;font-size:10px;margin-top:4px;">Source: Open-Meteo + Wind Power Curve model</div>
    <div style="color:#999;font-size:10px;">${zone.lat.toFixed(4)}, ${zone.lon.toFixed(4)}</div>
  </div>`;
}

function candidatePopup(c: LocationCandidate): string {
  const gi = c.grid_information;
  return `<div style="min-width:180px;font-family:system-ui;font-size:12px;">
    <div style="font-weight:600;font-size:13px;margin-bottom:4px;">${c.name}</div>
    <div style="color:#555;">Technology: ${c.technology}</div>
    ${gi ? `<div style="color:#555;">Grid: ${gi.substation || "N/A"} (${gi.voltage_kv || "N/A"} kV)</div>
    <div style="color:#555;">Distance: ${gi.distance_km?.toFixed(1) || "N/A"} km</div>
    <div style="color:#555;">Proximity: ${gi.grid_proximity || "N/A"}</div>` : ""}
    <div style="color:#92400e;font-weight:500;margin-top:4px;">PLANNING (candidate suggestion, not construction)</div>
    <div style="color:#999;font-size:10px;margin-top:4px;">Source: PowerFlex Location Intelligence</div>
  </div>`;
}

// =========================================================
// MAP COMPONENT (client-only)
// =========================================================

function MapComponent({ className = "" }: MapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{
    substations: L.LayerGroup;
    solarZones: L.LayerGroup;
    windZones: L.LayerGroup;
    candidates: L.LayerGroup;
  } | null>(null);

  const [layers, setLayers] = useState<LayerVisibility>({
    substations: true,
    solarZones: false,
    windZones: false,
    candidates: true,
  });
  const [selectedTechnology, setSelectedTechnology] = useState<string>("ALL");
  const [mapReady, setMapReady] = useState(false);

  // Fetch candidate locations (300s = 5 min, not 30s)
  const { data: locationData, loading: locationLoading } = usePolling<LocationSearchResponse>({
    url: API_ENDPOINTS.V3_LOCATION_SEARCH,
    intervalMs: 300000,
  });

  const candidates = useMemo(
    () => locationData?.candidates ?? [],
    [locationData?.candidates],
  );

  const filteredCandidates = useMemo(
    () =>
      selectedTechnology === "ALL"
        ? candidates
        : candidates.filter((c) => c.technology === selectedTechnology),
    [candidates, selectedTechnology],
  );

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: BANGLADESH_CENTER,
      zoom: 7,
      minZoom: 6,
      maxZoom: 12,
      zoomControl: true,
    });

    map.fitBounds(BANGLADESH_BOUNDS);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
      maxZoom: 19,
    }).addTo(map);

    const substationsLayer = L.layerGroup().addTo(map);
    const solarZonesLayer = L.layerGroup();
    const windZonesLayer = L.layerGroup();
    const candidatesLayer = L.layerGroup().addTo(map);

    layersRef.current = {
      substations: substationsLayer,
      solarZones: solarZonesLayer,
      windZones: windZonesLayer,
      candidates: candidatesLayer,
    };

    mapInstanceRef.current = map;
    setMapReady(true);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Sync layer visibility
  const toggleLayer = useCallback((key: keyof LayerVisibility) => {
    setLayers((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      return next;
    });
  }, []);

  // Substations layer
  useEffect(() => {
    if (!layersRef.current || !mapReady) return;
    const layer = layersRef.current.substations;
    layer.clearLayers();
    if (!layers.substations) return;

    SUBSTATIONS.forEach((sub) => {
      const icon = createSubstationIcon(sub.voltage_kv);
      L.marker([sub.lat, sub.lon], { icon })
        .bindPopup(substationPopup(sub))
        .addTo(layer);
    });
  }, [layers.substations, mapReady]);

  // Solar zones layer
  useEffect(() => {
    if (!layersRef.current || !mapReady) return;
    const layer = layersRef.current.solarZones;
    layer.clearLayers();
    if (!layers.solarZones) return;

    SOLAR_ZONES.forEach((zone) => {
      const icon = createSolarIcon();
      L.marker([zone.lat, zone.lon], { icon })
        .bindPopup(solarZonePopup(zone))
        .addTo(layer);
    });
  }, [layers.solarZones, mapReady]);

  // Wind zones layer
  useEffect(() => {
    if (!layersRef.current || !mapReady) return;
    const layer = layersRef.current.windZones;
    layer.clearLayers();
    if (!layers.windZones) return;

    WIND_ZONES.forEach((zone) => {
      const icon = createWindIcon();
      L.marker([zone.lat, zone.lon], { icon })
        .bindPopup(windZonePopup(zone))
        .addTo(layer);
    });
  }, [layers.windZones, mapReady]);

  // Candidates layer
  useEffect(() => {
    if (!layersRef.current || !mapReady) return;
    const layer = layersRef.current.candidates;
    layer.clearLayers();
    if (!layers.candidates) return;

    filteredCandidates.forEach((c) => {
      const icon = createCandidateIcon(c.technology);
      L.marker([c.latitude, c.longitude], { icon })
        .bindPopup(candidatePopup(c))
        .addTo(layer);
    });
  }, [filteredCandidates, layers.candidates, mapReady]);

  // Sync layer groups to map
  useEffect(() => {
    if (!layersRef.current || !mapReady) return;
    const map = mapInstanceRef.current;
    if (!map) return;
    const refs = layersRef.current;

    Object.entries(layers).forEach(([key, visible]) => {
      const group = refs[key as keyof typeof refs];
      if (!group) return;
      if (visible && !map.hasLayer(group)) group.addTo(map);
      if (!visible && map.hasLayer(group)) map.removeLayer(group);
    });
  }, [layers, mapReady]);

  return (
    <div className={`relative ${className}`}>
      {/* Map Container */}
      <div
        ref={mapRef}
        className="w-full h-[500px] rounded-xl border border-slate-200 bg-slate-100"
      />

      {/* Layer Controls */}
      <div className="absolute top-3 right-3 bg-slate-800 rounded-lg shadow-lg p-3 z-[1000] min-w-[180px]">
        <div className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wide">Layers</div>
        <div className="space-y-1.5">
          {([
            ["substations", "Grid Substations", "18 locations \u2022 UNVERIFIED"],
            ["solarZones", "Solar Potential", "9 zones \u2022 MODELED"],
            ["windZones", "Wind Potential", "6 zones \u2022 CALCULATED"],
            ["candidates", "Candidate Sites", `${filteredCandidates.length} locations`],
          ] as const).map(([key, label, detail]) => (
            <label key={key} className="flex items-start gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={layers[key]}
                onChange={() => toggleLayer(key)}
                className="mt-0.5 rounded border-slate-600"
              />
              <div className="min-w-0">
                <div className="text-xs font-medium text-slate-300 group-hover:text-white">{label}</div>
                <div className="text-[10px] text-slate-500">{detail}</div>
              </div>
            </label>
          ))}
        </div>

        {layers.candidates && (
          <div className="mt-2 pt-2 border-t border-slate-700">
            <select
              value={selectedTechnology}
              onChange={(e) => setSelectedTechnology(e.target.value)}
              className="w-full text-xs border border-slate-600 rounded px-2 py-1 text-slate-300 bg-slate-700"
            >
              <option value="ALL">All Technologies</option>
              <option value="SOLAR">Solar</option>
              <option value="WIND">Wind</option>
              <option value="GAS">Gas</option>
            </select>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 bg-slate-800 rounded-lg shadow-lg p-3 z-[1000] text-[11px]">
        <div className="font-semibold text-slate-300 mb-1.5 uppercase tracking-wide text-[10px]">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
            <span className="text-slate-400">400 kV Substation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-orange-500"></div>
            <span className="text-slate-400">230 kV Substation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
            <span className="text-slate-400">132 kV Substation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-400"></div>
            <span className="text-slate-400">Solar Zone (MODELED)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400"></div>
            <span className="text-slate-400">Wind Zone (CALCULATED)</span>
          </div>
        </div>
        <div className="mt-2 pt-1.5 border-t border-slate-700">
          <div className="flex items-center gap-2">
            <span className="text-amber-500">?</span>
            <span className="text-slate-500">UNVERIFIED data</span>
          </div>
        </div>
      </div>

      {/* Attribution */}
      <div className="absolute bottom-3 right-3 bg-slate-800/90 rounded px-2 py-1 text-[10px] text-slate-500 z-[1000]">
        Substations: UNVERIFIED | Solar/Wind: MODELED | tiles: OpenStreetMap
      </div>

      {/* Loading indicator */}
      {locationLoading && mapReady && (
        <div className="absolute top-3 left-3 bg-slate-800 rounded-lg shadow px-2.5 py-1.5 z-[1000]">
          <span className="text-xs text-slate-400">Loading candidates...</span>
        </div>
      )}
    </div>
  );
}

// =========================================================
// EXPORT — ErrorBoundary-wrapped
// =========================================================

export default function InteractiveMap({ className }: MapProps) {
  return (
    <ErrorBoundary fallback={<div className="p-4 text-red-500 text-sm">Map failed to load</div>}>
      <MapComponent className={className} />
    </ErrorBoundary>
  );
}
