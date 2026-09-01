"use client";

import { usePolling } from "@/hooks/usePolling";
import type { LoadShieldResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

const RESOURCES = [
  "solar", "wind", "hydro", "gas", "liquid_fuel",
  "coal", "biomass", "waste_to_energy", "nuclear",
  "battery", "flexible_demand",
] as const;

const RESOURCE_LABELS: Record<string, string> = {
  solar: "Solar", wind: "Wind", hydro: "Hydro",
  gas: "Gas", liquid_fuel: "Liquid Fuel", coal: "Coal",
  biomass: "Biomass", waste_to_energy: "Waste to Energy",
  nuclear: "Nuclear", battery: "Battery Storage",
  flexible_demand: "Flexible Demand",
};

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

function fmtStr(v: unknown): string {
  if (v == null) return "N/A";
  return String(v);
}

export default function LoadShield() {
  const { data, loading, error, lastUpdated, refresh } =
    usePolling<LoadShieldResponse>({
      url: `${API_BASE}/api/loadshield/live`,
      intervalMs: 120000,
    });

  if (loading && !data) {
    return (
      <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
        <LoadingSkeleton lines={10} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">Failed to load LoadShield data.</p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
        <button onClick={refresh} className="mt-4 text-sm text-emerald-400 hover:underline">
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const isWaiting = data.status === "WAITING_FOR_GRID_DATA";

  return (
    <section className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">
            LoadShield — AI-Powered Grid Protection
          </h2>
          <StatusIndicator live={!isWaiting && data.status !== "DATA_INCOMPLETE"} />
        </div>
        <RefreshButton onClick={refresh} loading={loading} />
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-400">
          Last updated: {lastUpdated.toLocaleString()}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <DataBadge classification={data.status || "DATA_UNAVAILABLE"} />
      </div>

      {isWaiting ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-yellow-500/30 bg-yellow-500/10 py-12 text-center">
          <p className="text-lg font-medium text-yellow-400">WAITING_FOR_GRID_DATA</p>
          <p className="mt-2 text-sm text-yellow-400/70">{data.message}</p>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Current Situation</h3>
            {data.current_situation?.grid ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <span className="text-xs text-slate-400">Demand</span>
                  <p className="text-sm font-medium text-white">{fmtMw(data.current_situation.grid.demand_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Supply</span>
                  <p className="text-sm font-medium text-white">{fmtMw(data.current_situation.grid.supply_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Deficit</span>
                  <p className="text-sm font-medium text-red-400">{fmtMw(data.current_situation.grid.deficit_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Load Shedding</span>
                  <p className="text-sm font-medium text-red-400">{fmtMw(data.current_situation.grid.load_shedding_mw)}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">No grid data available.</p>
            )}
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs text-slate-400">Risk Level</span>
                <p className="mt-1 text-sm text-white">{fmtStr(data.current_situation?.risk_level)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400">System Status</span>
                <p className="mt-1 text-sm text-white">{fmtStr(data.current_situation?.system_status)}</p>
              </div>
            </div>
          </div>

          {data.resource_analysis && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-300">Resource Analysis</h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {RESOURCES.map((key) => {
                  const entry = (data.resource_analysis as Record<string, Record<string, unknown>>)[key];
                  if (!entry) return null;
                  const isPrototype = key === "battery" || key === "flexible_demand";
                  return (
                    <div key={key} className="rounded-lg border border-slate-700/50 bg-slate-900/50 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-white">{RESOURCE_LABELS[key]}</span>
                        {isPrototype && <DataBadge classification="PROTOTYPE" />}
                      </div>
                      <p className="mt-2 text-xs text-slate-400">
                        Generation: <span className="text-white">{fmtMw(entry.current_generation_mw as number | null)}</span>
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        Classification: <span className="text-white">{fmtStr(entry.data_classification)}</span>
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {data.current_recommendation && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-300">Current Recommendation</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-xs text-slate-400">Initial Deficit</span>
                  <p className="text-sm font-medium text-red-400">{fmtMw(data.current_recommendation.initial_deficit_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Total Support</span>
                  <p className="text-sm font-medium text-emerald-400">{fmtMw(data.current_recommendation.total_support_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Remaining Gap</span>
                  <p className={`text-sm font-medium ${data.current_recommendation.remaining_gap_mw > 0 ? "text-red-400" : "text-emerald-400"}`}>
                    {fmtMw(data.current_recommendation.remaining_gap_mw)}
                  </p>
                </div>
              </div>

              {data.current_recommendation.recommended_deployment?.length > 0 && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="pb-2 pr-4 font-medium text-slate-400">Zone</th>
                        <th className="pb-2 pr-4 font-medium text-slate-400">Resource</th>
                        <th className="pb-2 font-medium text-slate-400">Support (MW)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.current_recommendation.recommended_deployment.map((d, i) => (
                        <tr key={i} className="border-b border-slate-700/50">
                          <td className="py-2 pr-4 text-white">{d.zone}</td>
                          <td className="py-2 pr-4 text-white">{d.resource}</td>
                          <td className="py-2 text-white">{fmtMw(d.support_mw)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {data.forecast_preparation && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-300">Forecast Preparation</h3>
              <DataBadge classification="MODEL_FORECAST" />
              <div className="mt-3 grid grid-cols-3 gap-4">
                <div>
                  <span className="text-xs text-slate-400">Forecast Peak</span>
                  <p className="text-sm font-medium text-white">{fmtMw((data.forecast_preparation as Record<string, number>).forecast_peak_mw)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Peak Timestamp</span>
                  <p className="text-sm font-medium text-white">{fmtStr((data.forecast_preparation as Record<string, unknown>).peak_timestamp)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Expected Deficit</span>
                  <p className="text-sm font-medium text-red-400">{fmtMw((data.forecast_preparation as Record<string, number>).expected_deficit_mw)}</p>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Data Sources</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.data_source).map(([key, val]) => (
                <span key={key} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300">
                  {key}: {val}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
