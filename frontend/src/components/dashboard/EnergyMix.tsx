"use client";

import { useGridData } from "@/hooks/useGridData";
import { fmtMw } from "@/lib/utils";
import { LiveIndicator } from "@/components/ui/LiveIndicator";
import { ErrorState } from "@/components/ui/ErrorState";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  gas_mw: { label: "Gas", color: "#3b82f6" },
  liquid_fuel_mw: { label: "Liquid Fuel", color: "#f59e0b" },
  coal_mw: { label: "Coal", color: "#6b7280" },
  hydro_mw: { label: "Hydro", color: "#06b6d4" },
  solar_mw: { label: "Solar", color: "#fbbf24" },
  wind_mw: { label: "Wind", color: "#22d3ee" },
  biomass_mw: { label: "Biomass", color: "#10b981" },
  nuclear_mw: { label: "Nuclear", color: "#a855f7" },
};

function BarSegment({
  label,
  mw,
  total,
  color,
}: {
  label: string;
  mw: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? (mw / total) * 100 : 0;
  if (pct < 0.5) return null;

  return (
    <div className="flex items-center gap-2" role="listitem">
      <div className="w-16 shrink-0 text-right text-[10px] text-slate-500">{label}</div>
      <div className="relative h-4 flex-1 overflow-hidden rounded bg-slate-700/40">
        <div
          className="absolute inset-y-0 left-0 rounded transition-all duration-500"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
          aria-hidden="true"
        />
        <span className="relative z-10 flex h-full items-center px-1.5 text-[9px] font-medium text-white">
          {pct >= 10 ? `${mw.toLocaleString()} MW` : ""}
        </span>
      </div>
      <div className="w-10 shrink-0 text-right text-[10px] text-slate-500">
        {pct.toFixed(1)}%
      </div>
    </div>
  );
}

function CompactBar({
  label,
  mw,
  total,
  color,
}: {
  label: string;
  mw: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? (mw / total) * 100 : 0;
  if (pct < 0.5) return null;

  return (
    <div className="flex items-center gap-1.5">
      <div
        className="h-2 rounded"
        style={{ width: `${Math.max(pct, 2)}%`, backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="text-[10px] text-slate-400">
        {label}: {mw.toLocaleString()} MW ({pct.toFixed(1)}%)
      </span>
    </div>
  );
}

export default function EnergyMix() {
  const { data, loading, error, lastUpdated, refresh } = useGridData();

  const snapshot = data?.grid_snapshot;
  const breakdown = snapshot?.generation_breakdown ?? {};
  const total = snapshot?.supply_mw ?? 0;

  const entries = Object.entries(breakdown)
    .filter(([, v]) => v != null && v > 0)
    .sort(([, a], [, b]) => (b ?? 0) - (a ?? 0));

  const renewableTotal = entries
    .filter(([k]) => ["solar_mw", "wind_mw", "hydro_mw", "biomass_mw"].includes(k))
    .reduce((sum, [, v]) => sum + (v ?? 0), 0);

  const fossilTotal = entries
    .filter(([k]) => ["gas_mw", "coal_mw", "liquid_fuel_mw"].includes(k))
    .reduce((sum, [, v]) => sum + (v ?? 0), 0);

  if (loading && !data) {
    return (
      <section aria-label="Energy Generation Mix" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Generation Mix</h2>
        <LoadingSkeleton lines={4} />
      </section>
    );
  }

  if (error && !data) {
    return (
      <section aria-label="Energy Generation Mix" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Generation Mix</h2>
        <ErrorState message="Generation data unavailable" onRetry={refresh} />
      </section>
    );
  }

  if (!snapshot || entries.length === 0) {
    return (
      <section aria-label="Energy Generation Mix" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Generation Mix</h2>
        <div className="rounded-lg bg-slate-900/40 p-4 text-center">
          <p className="text-[11px] text-slate-400">No generation data available</p>
        </div>
      </section>
    );
  }

  return (
    <section aria-label="Energy Generation Mix" className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Generation Mix</h2>
        <LiveIndicator status={data?.live ? "live" : "delayed"} lastUpdated={lastUpdated} />
      </div>

      {/* Summary badges */}
      <div className="flex flex-wrap gap-1.5">
        <span className="rounded-full border border-sky-500/20 bg-sky-500/10 px-2 py-0.5 text-[10px] font-medium text-sky-400">
          Total: {total.toLocaleString()} MW
        </span>
        <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
          Renewable: {renewableTotal.toLocaleString()} MW ({total > 0 ? ((renewableTotal / total) * 100).toFixed(1) : 0}%)
        </span>
        <span className="rounded-full border border-slate-500/20 bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-400">
          Fossil: {fossilTotal.toLocaleString()} MW ({total > 0 ? ((fossilTotal / total) * 100).toFixed(1) : 0}%)
        </span>
      </div>

      {/* Full bars on desktop */}
      <div className="hidden space-y-1 sm:block" role="list" aria-label="Generation by source">
        {entries.map(([key, val]) => {
          const cfg = SOURCE_CONFIG[key] || { label: key, color: "#94a3b8" };
          return (
            <BarSegment key={key} label={cfg.label} mw={val ?? 0} total={total} color={cfg.color} />
          );
        })}
      </div>

      {/* Compact bars on mobile */}
      <div className="space-y-1 sm:hidden" role="list" aria-label="Generation by source">
        {entries.map(([key, val]) => {
          const cfg = SOURCE_CONFIG[key] || { label: key, color: "#94a3b8" };
          return (
            <CompactBar key={key} label={cfg.label} mw={val ?? 0} total={total} color={cfg.color} />
          );
        })}
      </div>

      {/* Imports */}
      {snapshot.imports && Object.keys(snapshot.imports).length > 0 && (
        <div className="flex flex-wrap gap-1.5 border-t border-slate-700/30 pt-2">
          {Object.entries(snapshot.imports).map(([k, v]) => (
            <span key={k} className="text-[10px] text-slate-500">
              {k}: {v != null ? `${v} MW` : "N/A"}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
