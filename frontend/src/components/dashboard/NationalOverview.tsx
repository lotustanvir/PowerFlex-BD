"use client";

import { useGridData } from "@/hooks/useGridData";
import { useLoadShieldData } from "@/hooks/useLoadShieldData";
import { LiveIndicator } from "@/components/ui/LiveIndicator";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

function MetricBlock({
  label,
  value,
  unit,
  status,
}: {
  label: string;
  value: string | number | null;
  unit?: string;
  status?: "normal" | "warning" | "critical" | "info";
}) {
  const colorMap = {
    normal: "text-emerald-400",
    warning: "text-amber-400",
    critical: "text-red-400",
    info: "text-sky-400",
  };

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <span className={`text-xl font-bold tabular-nums ${colorMap[status || "normal"]}`}>
        {value != null ? value : "N/A"}
        {unit && value != null && (
          <span className="ml-0.5 text-xs font-normal text-slate-500">{unit}</span>
        )}
      </span>
    </div>
  );
}

export default function NationalOverview() {
  const { data: gridData, loading: gridLoading, error: gridError, lastUpdated, refresh: refreshGrid } =
    useGridData();

  const { data: lsData } = useLoadShieldData();

  const snapshot = gridData?.grid_snapshot;
  const risk = lsData?.grid_risk;
  const currentSituation = lsData?.current_situation;

  const demand = snapshot?.current_demand_mw ?? currentSituation?.grid?.demand_mw;
  const supply = snapshot?.supply_mw ?? currentSituation?.grid?.supply_mw;
  const gap = snapshot?.demand_supply_gap_mw ?? currentSituation?.grid?.deficit_mw;
  const loadShedding = snapshot?.load_shedding_mw ?? currentSituation?.grid?.load_shedding_mw;
  const riskLevel = risk?.risk_level ?? currentSituation?.risk_level ?? gridData?.risk_level;
  const riskScore = risk?.composite_score;
  const systemStatus = currentSituation?.system_status;

  const isLoading = gridLoading && !gridData;

  return (
    <section aria-label="National Energy Overview">
      {isLoading && <LoadingSkeleton lines={2} />}

      {gridError && !gridData && (
        <ErrorState message={`Grid data unavailable: ${gridError}`} onRetry={refreshGrid} />
      )}

      {!isLoading && !gridError && !gridData?.live && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 p-3">
          <p className="text-xs font-medium text-amber-400">WAITING FOR GRID DATA</p>
          <p className="mt-0.5 text-[10px] text-amber-400/60">
            Official PGCB/NLDC data required. No hardcoded values used.
          </p>
        </div>
      )}

      {snapshot && (
        <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
          {/* Top bar: title + status + refresh */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-white">National Energy Overview</h2>
              <LiveIndicator
                status={gridData?.live ? "live" : "delayed"}
                lastUpdated={lastUpdated}
              />
              {riskLevel && <RiskBadge level={riskLevel} />}
            </div>
            <button
              onClick={refreshGrid}
              className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
              disabled={gridLoading}
              aria-label="Refresh grid data"
            >
              Refresh
            </button>
          </div>

          {/* Metrics row */}
          <div className="grid grid-cols-3 gap-x-6 gap-y-2 sm:grid-cols-3 lg:grid-cols-6">
            <MetricBlock
              label="Demand"
              value={demand != null ? Math.round(demand) : null}
              unit="MW"
              status={demand != null && demand > 14000 ? "warning" : "normal"}
            />
            <MetricBlock
              label="Supply"
              value={supply != null ? Math.round(supply) : null}
              unit="MW"
              status="info"
            />
            <MetricBlock
              label="Gap"
              value={gap != null ? Math.round(gap) : null}
              unit="MW"
              status={gap != null && gap > 0 ? "critical" : "normal"}
            />
            <MetricBlock
              label="Load Shedding"
              value={loadShedding != null && loadShedding > 0 ? Math.round(loadShedding) : null}
              unit="MW"
              status={loadShedding != null && loadShedding > 0 ? "critical" : "normal"}
            />
            <MetricBlock
              label="Risk Score"
              value={riskScore != null ? riskScore.toFixed(1) : null}
              status={
                riskScore != null
                  ? riskScore <= 30
                    ? "normal"
                    : riskScore <= 55
                      ? "warning"
                      : "critical"
                  : "normal"
              }
            />
            <MetricBlock
              label="Status"
              value={systemStatus || gridData?.grid_status || null}
              status={
                systemStatus === "BALANCED" || gridData?.grid_status === "NORMAL"
                  ? "normal"
                  : systemStatus === "CRITICAL"
                    ? "critical"
                    : "warning"
              }
            />
          </div>

          {snapshot.timestamp && (
            <p className="mt-2 text-[10px] text-slate-600">
              Grid timestamp: {snapshot.timestamp}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
