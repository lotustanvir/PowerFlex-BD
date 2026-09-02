"use client";

import { useLoadShieldData } from "@/hooks/useLoadShieldData";
import type { ZoneAnalysis } from "@/lib/types";
import { fmtMw, fmtNum } from "@/lib/utils";
import { DataBadge } from "@/components/ui/DataBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

export default function NineZoneAnalysis() {
  const { data, loading, error, refresh } = useLoadShieldData();

  if (loading && !data) {
    return (
      <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <LoadingSkeleton lines={6} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <ErrorState message="Failed to load zone analysis" onRetry={refresh} />
      </div>
    );
  }

  const zones: ZoneAnalysis[] = data?.zone_analysis || [];

  if (zones.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-2 text-sm font-semibold text-white">9-Zone Analysis</h2>
        <p className="text-[11px] text-slate-400">Zone data unavailable.</p>
      </div>
    );
  }

  const topZone = zones[0];

  return (
    <section className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white">9-Zone Analysis</h2>
          <DataBadge classification="LIVE" />
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
          disabled={loading}
          aria-label="Refresh zone analysis"
        >
          Refresh
        </button>
      </div>

      <div className="flex items-center gap-4 text-[11px]">
        <span className="text-slate-400">Zones: <span className="text-white">{zones.length}</span></span>
        <span className="text-slate-400">Top: <span className="font-medium text-emerald-400">{topZone.zone}</span></span>
        <span className="text-slate-400">Score: <span className="text-white">{fmtNum(topZone.combined_renewable_score)}</span></span>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {zones.map((zone, idx) => (
          <div
            key={zone.zone}
            className={`rounded-lg p-2.5 ${
              idx === 0
                ? "border border-emerald-500/25 bg-emerald-500/8"
                : "bg-slate-900/40"
            }`}
          >
            <div className="mb-1.5 flex items-center justify-between">
              <h3 className="text-[11px] font-semibold text-white">{zone.zone}</h3>
              <span className="text-[9px] text-slate-500">#{zone.rank}</span>
            </div>

            <div className="space-y-0.5 text-[10px]">
              <div className="flex justify-between">
                <span className="text-slate-500">Solar</span>
                <span className="text-amber-400">{fmtNum(zone.solar_available_mwh_per_1mw_24h)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Wind</span>
                <span className="text-sky-400">{fmtNum(zone.wind_available_mwh_per_1mw_24h)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Score</span>
                <span className="font-medium text-white">{fmtNum(zone.combined_renewable_score)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Biomass</span>
                <span className="text-emerald-400">{fmtMw(zone.biomass_available_mw)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Waste</span>
                <span className="text-purple-400">{fmtMw(zone.waste_available_mw)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Hydro</span>
                <span className="text-blue-400">{fmtMw(zone.hydro_available_mw)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
