"use client";

import { usePolling } from "@/hooks/usePolling";
import type { DemandForecastResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

export default function DemandForecast() {
  const { data, loading, error, lastUpdated, refresh } =
    usePolling<DemandForecastResponse>({
      url: `${API_BASE}/api/demand/forecast`,
      intervalMs: 300000,
    });

  if (loading && !data) {
    return (
      <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
        <LoadingSkeleton lines={8} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">Failed to load demand forecast.</p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
        <button onClick={refresh} className="mt-4 text-sm text-emerald-400 hover:underline">Retry</button>
      </div>
    );
  }

  if (!data) return null;

  const maxDemand = Math.max(
    ...data.hourly_forecast.map((h) => h.predicted_demand_mw),
    1
  );

  return (
    <section className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Demand Forecast — Next 24 Hours</h2>
          <DataBadge classification="MODEL_FORECAST" />
          {data.weather_data_status === "UNAVAILABLE" && (
            <span className="rounded-full bg-yellow-500/20 px-2 py-0.5 text-xs text-yellow-400">
              Weather data unavailable — using default temperature
            </span>
          )}
        </div>
        <RefreshButton onClick={refresh} loading={loading} />
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-400">Last updated: {lastUpdated.toLocaleString()}</p>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400">Current PGCB Demand</span>
          <p className="mt-1 text-lg font-bold text-white">{fmtMw(data.current_pgcb_demand_mw)}</p>
          <DataBadge classification="OFFICIAL_PGCB" />
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400">Forecast Peak</span>
          <p className="mt-1 text-lg font-bold text-amber-400">{fmtMw(data.forecast_peak_mw)}</p>
          <p className="mt-1 text-xs text-slate-400">{data.peak_timestamp || "N/A"}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400">PGCB Supply</span>
          <p className="mt-1 text-lg font-bold text-white">{fmtMw(data.pgcb_source?.supply_mw)}</p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-300">24-Hour Forecast</h3>
        <div className="space-y-1">
          {data.hourly_forecast.map((h) => {
            const width = (h.predicted_demand_mw / maxDemand) * 100;
            const isPeak = h.predicted_demand_mw === data.forecast_peak_mw;
            return (
              <div key={h.hour_offset} className="flex items-center gap-2 text-xs">
                <span className="w-12 text-slate-400">{String(h.hour_bst).padStart(2, "0")}:00</span>
                <div className="flex-1 h-4 bg-slate-800 rounded overflow-hidden">
                  <div
                    className={`h-full rounded ${isPeak ? "bg-amber-500" : "bg-emerald-500/70"}`}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <span className="w-20 text-right text-slate-300">{fmtMw(h.predicted_demand_mw)}</span>
                <span className="w-12 text-right text-slate-500">{h.temperature_c}°C</span>
              </div>
            );
          })}
        </div>
      </div>

      {data.training_metadata && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Model Status</h3>
          <p className="text-xs text-slate-400">{String(data.training_metadata.model_status)}</p>
        </div>
      )}
    </section>
  );
}
