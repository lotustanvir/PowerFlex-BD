"use client";

import { usePolling } from "@/hooks/usePolling";
import type { LoadShieldResponse, ZoneAnalysis } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return v.toLocaleString();
}

export default function NineZoneAnalysis() {
  const { data, loading, error, lastUpdated, refresh } =
    usePolling<LoadShieldResponse>({
      url: `${API_BASE}/api/loadshield/live`,
      intervalMs: 120000,
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
        <p className="text-sm text-red-400">Failed to load zone analysis.</p>
        <button onClick={refresh} className="mt-4 text-sm text-emerald-400 hover:underline">Retry</button>
      </div>
    );
  }

  const zones: ZoneAnalysis[] = data?.zone_analysis || [];

  if (zones.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">9-Zone Analysis — Bangladesh</h2>
        <p className="text-slate-400">Zone data unavailable. Waiting for grid data.</p>
      </div>
    );
  }

  const topZone = zones[0];

  return (
    <section className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">9-Zone Analysis — Bangladesh</h2>
          <DataBadge classification="LIVE" />
        </div>
        <RefreshButton onClick={refresh} loading={loading} />
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-400">Last updated: {lastUpdated.toLocaleString()}</p>
      )}

      <div className="flex flex-wrap gap-4 text-sm">
        <span className="text-slate-400">Zones: <span className="text-white">{zones.length}</span></span>
        <span className="text-slate-400">Top Zone: <span className="text-emerald-400 font-medium">{topZone.zone}</span></span>
        <span className="text-slate-400">Score: <span className="text-white">{fmtNum(topZone.combined_renewable_score)}</span></span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {zones.map((zone, idx) => (
          <div
            key={zone.zone}
            className={`rounded-xl border p-4 ${
              idx === 0
                ? "border-emerald-500/50 bg-emerald-500/5"
                : "border-slate-700/50 bg-slate-800/50"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">{zone.zone}</h3>
              <span className="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
                #{zone.rank}
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Solar (MWh/1MW/24h)</span>
                <span className="text-amber-400">{fmtNum(zone.solar_available_mwh_per_1mw_24h)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Wind (MWh/1MW/24h)</span>
                <span className="text-sky-400">{fmtNum(zone.wind_available_mwh_per_1mw_24h)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Combined Score</span>
                <span className="text-white font-medium">{fmtNum(zone.combined_renewable_score)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Biomass</span>
                <span className="text-emerald-400">{fmtMw(zone.biomass_available_mw)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Waste</span>
                <span className="text-purple-400">{fmtMw(zone.waste_available_mw)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Hydro</span>
                <span className="text-blue-400">{fmtMw(zone.hydro_available_mw)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
