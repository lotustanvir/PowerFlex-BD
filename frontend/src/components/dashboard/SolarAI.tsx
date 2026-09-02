"use client";

import { usePolling } from "@/hooks/usePolling";
import type { SolarLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

export default function SolarAI() {
  const { data, error, loading, lastUpdated, refresh } =
    usePolling<SolarLiveResponse>({
      url: `${API_BASE}/api/solar/live`,
      intervalMs: 300000,
    });

  if (loading && !data) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton lines={2} />
        <LoadingSkeleton lines={4} />
        <LoadingSkeleton lines={6} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center">
        <p className="text-sm font-medium text-red-400">
          Failed to load solar forecast data
        </p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
        <div className="mt-3">
          <RefreshButton onClick={refresh} loading={loading} variant="dark" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  const best = data.best_forecast_zone;
  const opportunity = data.best_opportunity;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">
            Solar Forecast — Bangladesh
          </h2>
          <StatusIndicator live lastUpdated={lastUpdated} />
        </div>
        <div className="flex items-center gap-2">
          <DataBadge classification={data.status === "STALE" ? "STALE" : "FORECAST"} />
          <RefreshButton onClick={refresh} loading={loading} variant="dark" />
        </div>
      </div>

      {/* Classification Notice */}
      <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3 text-xs text-blue-300">
        Weather-driven solar generation forecast. This is NOT measured plant output.
        Model trained on synthetic targets — experimental, not validated against real data.
      </div>

      {/* Best Solar Zone */}
      <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-5">
        <h3 className="mb-3 text-sm font-medium text-slate-400">
          Best Solar Zone
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-slate-400">Zone</p>
            <p className="mt-0.5 text-xl font-bold text-white">
              {best.zone ?? "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">
              Expected Energy (MWh per 1MW / 24h)
            </p>
            <p className="mt-0.5 text-xl font-bold text-white">
              {best.expected_energy_mwh_per_1mw_24h != null
                ? best.expected_energy_mwh_per_1mw_24h.toFixed(2)
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Best Hourly Opportunity */}
      <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-5">
        <h3 className="mb-3 text-sm font-medium text-slate-400">
          Best Hourly Opportunity
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs text-slate-400">Zone</p>
            <p className="mt-0.5 text-base font-semibold text-white">
              {opportunity.zone ?? "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Timestamp</p>
            <p className="mt-0.5 text-base font-semibold text-white">
              {opportunity.timestamp ?? "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Solar Radiation (W/m²)</p>
            <p className="mt-0.5 text-base font-semibold text-white">
              {opportunity.solar_radiation_wm2 != null
                ? opportunity.solar_radiation_wm2.toFixed(1)
                : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">
              Predicted Generation (MW per 1MW)
            </p>
            <p className="mt-0.5 text-base font-semibold text-white">
              {opportunity.predicted_generation_mw_per_1mw != null
                ? opportunity.predicted_generation_mw_per_1mw.toFixed(3)
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Zone Ranking Table */}
      <div className="rounded-lg border border-slate-700/50 bg-slate-800/40">
        <div className="border-b border-slate-700 px-5 py-3">
          <h3 className="text-sm font-medium text-slate-400">Zone Ranking</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800 text-xs text-slate-400">
                <th className="px-5 py-2.5 font-medium">Rank</th>
                <th className="px-5 py-2.5 font-medium">Zone</th>
                <th className="px-5 py-2.5 font-medium">
                  Expected Energy (MWh per 1MW / 24h)
                </th>
              </tr>
            </thead>
            <tbody>
              {data.zone_ranking.map((row) => (
                <tr
                  key={row.rank}
                  className={`border-b border-slate-700/50 ${
                    row.rank === 1
                      ? "bg-emerald-500/10 font-medium"
                      : "hover:bg-slate-800/50"
                  }`}
                >
                  <td className="px-5 py-2.5">
                    <span
                      className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                        row.rank === 1
                          ? "bg-emerald-500 text-white"
                          : "bg-slate-700 text-slate-300"
                      }`}
                    >
                      {row.rank}
                    </span>
                  </td>
                  <td className="px-5 py-2.5 text-white">{row.zone}</td>
                  <td className="px-5 py-2.5 text-white">
                    {row.expected_energy_mwh_per_1mw_24h != null
                      ? row.expected_energy_mwh_per_1mw_24h.toFixed(2)
                      : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer info */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-500">
        <span>Data source: {data.data_source ?? "N/A"}</span>
        <span>
          Forecast hours: {data.forecast_hours ?? "N/A"}
        </span>
      </div>
    </div>
  );
}
