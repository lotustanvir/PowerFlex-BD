"use client";

import { usePolling } from "@/hooks/usePolling";
import type { GridLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import DataBadge from "@/components/ui/DataBadge";
import StatusIndicator from "@/components/ui/StatusIndicator";
import RefreshButton from "@/components/ui/RefreshButton";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

function MetricCard({ label, value, unit, highlight }: { label: string; value: string | number | null; unit?: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-4">
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${highlight ? "text-red-400" : "text-white"}`}>
        {value != null ? value : "N/A"}
        {unit && <span className="ml-1 text-sm font-normal text-slate-400">{unit}</span>}
      </p>
    </div>
  );
}

function GenerationRow({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-sm font-semibold text-white">{value != null ? `${value} MW` : "N/A"}</span>
    </div>
  );
}

export default function GridStatus() {
  const { data, error, loading, lastUpdated, refresh } = usePolling<GridLiveResponse>({
    url: `${API_BASE}/api/grid/live`,
    intervalMs: 60000,
  });

  const snapshot = data?.grid_snapshot;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-white">
          Bangladesh National Grid
        </h2>
        <StatusIndicator live={data?.live ?? false} lastUpdated={lastUpdated} />
        <RefreshButton onClick={refresh} loading={loading && !data} variant="dark" />
        <DataBadge classification="OFFICIAL_PGCB" />
      </div>

      {loading && !data && <LoadingSkeleton lines={6} />}

      {error && !data && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm font-medium text-red-400">
            Failed to load grid data: {error}
          </p>
          <button
            onClick={refresh}
            className="mt-2 text-sm font-medium text-red-400 underline hover:text-red-300"
          >
            Retry
          </button>
        </div>
      )}

      {data && !data.live && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
          <p className="text-sm font-medium text-amber-400">
            WAITING_FOR_GRID_DATA
          </p>
        </div>
      )}

      {snapshot && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <MetricCard
              label="Demand MW"
              value={snapshot.current_demand_mw}
              unit="MW"
            />
            <MetricCard
              label="Supply MW"
              value={snapshot.supply_mw}
              unit="MW"
            />
            <MetricCard
              label="Deficit MW"
              value={snapshot.demand_supply_gap_mw}
              unit="MW"
              highlight={snapshot.demand_supply_gap_mw != null && snapshot.demand_supply_gap_mw > 0}
            />
            <MetricCard
              label="Load Shedding MW"
              value={snapshot.load_shedding_mw}
              unit="MW"
              highlight={snapshot.load_shedding_mw != null && snapshot.load_shedding_mw > 0}
            />
            <MetricCard
              label="Grid Status"
              value={data.grid_status || null}
            />
            <MetricCard
              label="Risk Level"
              value={data.risk_level || null}
            />
          </div>

          <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-300">
              Generation Breakdown
            </h3>
            <div className="divide-y divide-slate-700">
              <GenerationRow label="Gas" value={snapshot.generation_breakdown.gas_mw ?? null} />
              <GenerationRow label="Liquid Fuel" value={snapshot.generation_breakdown.liquid_fuel_mw ?? null} />
              <GenerationRow label="Coal" value={snapshot.generation_breakdown.coal_mw ?? null} />
              <GenerationRow label="Hydro" value={snapshot.generation_breakdown.hydro_mw ?? null} />
              <GenerationRow label="Solar" value={snapshot.generation_breakdown.solar_mw ?? null} />
              <GenerationRow label="Wind" value={snapshot.generation_breakdown.wind_mw ?? null} />
            </div>
          </div>

          {Object.keys(snapshot.imports).length > 0 && (
            <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-300">
                Imports
              </h3>
              <div className="divide-y divide-slate-700">
                {Object.entries(snapshot.imports).map(([key, val]) => (
                  <GenerationRow key={key} label={key} value={val} />
                ))}
              </div>
            </div>
          )}

          {snapshot.timestamp && (
            <p className="text-xs text-slate-500">
              Grid timestamp: {snapshot.timestamp}
            </p>
          )}

          {snapshot.remarks && (
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
              <p className="text-sm text-slate-400">
                {snapshot.remarks}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
