"use client";

import { usePolling } from "@/hooks/usePolling";
import type { WindLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import DataBadge from "@/components/ui/DataBadge";
import StatusIndicator from "@/components/ui/StatusIndicator";
import RefreshButton from "@/components/ui/RefreshButton";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
const POLL_INTERVAL = 300_000;

function fmt(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export default function WindAI() {
  const { data, error, loading, lastUpdated, refresh } =
    usePolling<WindLiveResponse>({
      url: `${API_BASE}/api/wind/live`,
      intervalMs: POLL_INTERVAL,
    });

  if (loading && !data) {
    return (
      <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
        <LoadingSkeleton lines={6} />
      </section>
    );
  }

  if (error && !data) {
    return (
      <section className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
        <p className="text-sm font-medium text-red-400">Failed to load wind data: {error}</p>
        <div className="mt-3">
          <RefreshButton onClick={refresh} loading={loading} variant="dark" />
        </div>
      </section>
    );
  }

  const best = data?.best_forecast_zone;
  const opp = data?.best_opportunity;
  const ranking = data?.zone_ranking ?? [];
  const turbine = data?.turbine_assumption ?? {};

  return (
    <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-white">
          Wind Estimation — Bangladesh
        </h2>
        <StatusIndicator live={!!data?.forecast_basis} lastUpdated={lastUpdated} />
        <RefreshButton onClick={refresh} loading={loading} />
        <DataBadge classification={data?.status === "STALE" ? "STALE" : "CALCULATED"} />
      </div>

      {/* Classification Notice */}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-300">
        Engineering power-curve model applied to 100m wind speed data.
        This is NOT measured turbine generation. Experimental — not validated against real data.
      </div>

      {/* Best Wind Zone */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-5 space-y-2">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          Best Wind Zone
        </h3>
        {best ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-slate-400">Zone</p>
              <p className="text-base font-semibold text-white">{best.zone}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Expected Energy (MWh / 1 MW · 24 h)</p>
              <p className="text-base font-semibold text-white">
                {fmt(best.expected_energy_mwh_per_1mw_24h)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Modeled Capacity Factor</p>
              <p className="text-base font-semibold text-white">
                {fmt(best.modeled_capacity_factor_pct)}%
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">N/A</p>
        )}
      </div>

      {/* Best Hourly Opportunity */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-5 space-y-2">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          Best Hourly Opportunity
        </h3>
        {opp ? (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-slate-400">Zone</p>
              <p className="text-base font-semibold text-white">{opp.zone}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Timestamp</p>
              <p className="text-base font-semibold text-white">
                {opp.timestamp ?? "N/A"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Wind Speed @ 100 m (km/h)</p>
              <p className="text-base font-semibold text-white">
                {fmt(opp.wind_speed_100m_kmh)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Predicted Gen. (MW / 1 MW)</p>
              <p className="text-base font-semibold text-white">
                {fmt(opp.predicted_generation_mw_per_1mw)}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">N/A</p>
        )}
      </div>

      {/* Zone Ranking Table */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          Zone Ranking
        </h3>
        {ranking.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-slate-700 text-xs text-slate-400 uppercase">
                  <th className="pb-2 pr-4 font-medium">Rank</th>
                  <th className="pb-2 pr-4 font-medium">Zone</th>
                  <th className="pb-2 pr-4 font-medium">Expected Energy (MWh / 1 MW · 24 h)</th>
                  <th className="pb-2 font-medium">Capacity Factor %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {ranking
                  .slice()
                  .sort((a, b) => a.rank - b.rank)
                  .map((row) => (
                    <tr key={row.zone} className="text-slate-300">
                      <td className="py-2 pr-4 font-medium">{row.rank}</td>
                      <td className="py-2 pr-4">{row.zone}</td>
                      <td className="py-2 pr-4">{fmt(row.expected_energy_mwh_per_1mw_24h)}</td>
                      <td className="py-2">{fmt(row.modeled_capacity_factor_pct)}%</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-400">N/A</p>
        )}
      </div>

      {/* Turbine Assumption */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-5 space-y-2">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          Turbine Assumption
        </h3>
        {Object.keys(turbine).length > 0 ? (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
            {Object.entries(turbine).map(([key, val]) => (
              <div key={key} className="flex justify-between py-1">
                <dt className="text-xs text-slate-400 capitalize">
                  {key.replace(/_/g, " ")}
                </dt>
                <dd className="text-sm font-medium text-slate-300">
                  {val != null ? String(val) : "N/A"}
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-slate-400">N/A</p>
        )}
      </div>
    </section>
  );
}
