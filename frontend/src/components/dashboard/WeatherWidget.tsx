"use client";

import { useMemo } from "react";
import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { WeatherResponse } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

interface Props {
  zone?: string;
}

function getStatus(lastUpdated: Date | null): { label: string; color: string } {
  if (!lastUpdated) return { label: "PENDING", color: "text-slate-500" };

  const ageMs = Date.now() - lastUpdated.getTime();
  const FIVE_MIN = 5 * 60 * 1000;
  const THIRTY_MIN = 30 * 60 * 1000;

  if (ageMs < FIVE_MIN) {
    return { label: "LIVE", color: "text-emerald-400" };
  }
  if (ageMs < THIRTY_MIN) {
    return { label: "CACHED", color: "text-amber-400" };
  }
  return { label: "STALE", color: "text-red-400" };
}

export default function WeatherWidget({ zone = "Dhaka" }: Props) {
  const { data, error, loading, lastUpdated, refresh } = usePolling<WeatherResponse>({
    url: `${API_ENDPOINTS.V3_WEATHER_CURRENT}?zone=${zone}`,
    intervalMs: 1800000,
  });

  const status = useMemo(() => getStatus(lastUpdated), [lastUpdated]);

  if (loading && !data) return <LoadingSkeleton />;
  if (error && !data) {
    return (
      <ErrorBoundary>
        <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
          <p className="text-red-400">{error}</p>
        </div>
      </ErrorBoundary>
    );
  }

  const weather = data?.data;

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">
          Weather - {zone}
        </h3>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium ${status.color}`}>{status.label}</span>
          <span className="text-xs text-slate-500">
            {data?.classification || "UNKNOWN"}
          </span>
          <button
            onClick={refresh}
            disabled={loading}
            className="text-xs text-emerald-400 hover:text-emerald-300 disabled:opacity-50"
          >
            {loading ? "Updating..." : "Refresh"}
          </button>
        </div>
      </div>

      {weather ? (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Temperature</p>
            <p className="text-2xl font-bold text-amber-400">
              {weather.temperature_c !== null
                ? `${weather.temperature_c.toFixed(1)}°C`
                : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Humidity</p>
            <p className="text-2xl font-bold text-blue-400">
              {weather.humidity_percent !== null
                ? `${weather.humidity_percent.toFixed(0)}%`
                : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Wind Speed</p>
            <p className="text-2xl font-bold text-cyan-400">
              {weather.wind_speed_kmh !== null
                ? `${weather.wind_speed_kmh.toFixed(1)} km/h`
                : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Solar Radiation</p>
            <p className="text-2xl font-bold text-yellow-400">
              {weather.solar_radiation_wm2 !== null
                ? `${weather.solar_radiation_wm2.toFixed(0)} W/m²`
                : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Cloud Cover</p>
            <p className="text-2xl font-bold text-slate-300">
              {weather.cloud_cover_percent !== null
                ? `${weather.cloud_cover_percent.toFixed(0)}%`
                : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Source</p>
            <p className="text-sm text-slate-400">{weather.source}</p>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          Weather data unavailable
        </div>
      )}

      <div className="mt-4 text-xs text-slate-600">
        Updated: {lastUpdated ? lastUpdated.toLocaleString() : "Never"}
      </div>
    </div>
  );
}
