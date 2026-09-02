"use client";

import { useLoadShieldData } from "@/hooks/useLoadShieldData";
import type { GridRiskResponse, GridRiskScenario } from "@/lib/types";
import { fmtMw } from "@/lib/utils";
import { DataBadge } from "@/components/ui/DataBadge";
import { LiveIndicator } from "@/components/ui/LiveIndicator";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

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

function RiskGauge({ score, level }: { score: number; level: string }) {
  const rotation = (score / 100) * 180 - 90;
  const color = level === "LOW" ? "#10b981" : level === "MODERATE" ? "#eab308" : level === "ELEVATED" ? "#f97316" : "#ef4444";
  return (
    <div className="flex flex-col items-center">
      <div className="relative h-20 w-40 overflow-hidden">
        <div className="absolute inset-0 rounded-t-full border-2 border-b-0 border-slate-700/60" />
        <div
          className="absolute bottom-0 left-1/2 h-16 w-1 origin-bottom transition-transform duration-700"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)`, backgroundColor: color }}
        />
        <div className="absolute bottom-0 left-1/2 h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-white" />
      </div>
      <p className="mt-1 text-2xl font-bold tabular-nums text-white">{score.toFixed(1)}</p>
      <RiskBadge level={level} className="mt-0.5" />
    </div>
  );
}

function ScenarioTable({ scenarios }: { scenarios: Record<string, GridRiskScenario> }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-slate-700/60">
            <th className="pb-1.5 pr-3 font-medium text-slate-400">Scenario</th>
            <th className="pb-1.5 pr-3 font-medium text-slate-400">Score</th>
            <th className="pb-1.5 pr-3 font-medium text-slate-400">Level</th>
            <th className="pb-1.5 pr-3 font-medium text-slate-400">Demand</th>
            <th className="pb-1.5 pr-3 font-medium text-slate-400">Supply</th>
            <th className="pb-1.5 font-medium text-slate-400">Gap</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(scenarios).map(([key, s]) => (
            <tr key={key} className="border-b border-slate-700/30">
              <td className="py-1.5 pr-3 text-white">{s.label}</td>
              <td className="py-1.5 pr-3 font-mono text-white">{s.risk_score.toFixed(1)}</td>
              <td className="py-1.5 pr-3">
                <RiskBadge level={s.risk_level} />
              </td>
              <td className="py-1.5 pr-3 text-white">{fmtMw(s.demand_mw)}</td>
              <td className="py-1.5 pr-3 text-white">{fmtMw(s.supply_mw)}</td>
              <td className="py-1.5 text-red-400">{fmtMw(s.gap_mw)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GridRiskInline({ risk }: { risk: GridRiskResponse }) {
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-6">
        <RiskGauge score={risk.composite_score} level={risk.risk_level} />
        <div className="flex-1 space-y-2">
          <p className="text-xs font-medium text-slate-400">Risk Components</p>
          <div className="space-y-1.5">
            {risk.components.map((c) => (
              <div key={c.name} className="flex items-center gap-2">
                <span className="w-28 shrink-0 truncate text-[11px] text-slate-400">{c.name}</span>
                <div className="h-1.5 flex-1 rounded-full bg-slate-700/60">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(c.score, 100)}%`, backgroundColor: c.score <= 30 ? "#10b981" : c.score <= 55 ? "#eab308" : c.score <= 75 ? "#f97316" : "#ef4444" }}
                  />
                </div>
                <span className="w-10 text-right font-mono text-[11px] text-white">{c.score.toFixed(0)}</span>
                <span className="text-[10px] text-slate-600">{c.unit}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {Object.keys(risk.scenarios).length > 0 && (
        <div>
          <p className="mb-1 text-[11px] font-medium text-slate-500">Scenario Comparison</p>
          <ScenarioTable scenarios={risk.scenarios} />
        </div>
      )}
    </div>
  );
}

export default function LoadShield() {
  const { data, loading, error, lastUpdated, refresh } = useLoadShieldData();

  if (loading && !data) {
    return (
      <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <LoadingSkeleton lines={8} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <ErrorState message={`Failed to load LoadShield data: ${error}`} onRetry={refresh} />
      </div>
    );
  }

  if (!data) return null;

  const isWaiting = data.status === "WAITING_FOR_GRID_DATA";

  return (
    <section className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-semibold text-white">
            LoadShield — AI-Powered Grid Protection
          </h2>
          <LiveIndicator
            status={!isWaiting && data.status !== "DATA_INCOMPLETE" ? "live" : "unavailable"}
            lastUpdated={lastUpdated}
          />
          <DataBadge classification={data.status || "DATA_UNAVAILABLE"} />
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
          disabled={loading}
          aria-label="Refresh LoadShield"
        >
          Refresh
        </button>
      </div>

      {isWaiting ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-yellow-500/25 bg-yellow-500/8 py-10 text-center">
          <p className="text-base font-medium text-yellow-400">WAITING_FOR_GRID_DATA</p>
          <p className="mt-1.5 text-xs text-yellow-400/70">{data.message}</p>
        </div>
      ) : (
        <>
          {/* Current Situation — inline metrics */}
          {data.current_situation?.grid && (
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
              <div>
                <span className="text-[10px] text-slate-500">Demand</span>
                <p className="text-sm font-semibold text-white">{fmtMw(data.current_situation.grid.demand_mw)}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-500">Supply</span>
                <p className="text-sm font-semibold text-white">{fmtMw(data.current_situation.grid.supply_mw)}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-500">Deficit</span>
                <p className="text-sm font-semibold text-red-400">{fmtMw(data.current_situation.grid.deficit_mw)}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-500">Load Shedding</span>
                <p className="text-sm font-semibold text-red-400">{fmtMw(data.current_situation.grid.load_shedding_mw)}</p>
              </div>
            </div>
          )}

          {/* Risk + Scenarios — inline */}
          {data.grid_risk && (
            <div className="border-t border-slate-700/30 pt-3">
              <GridRiskInline risk={data.grid_risk} />
            </div>
          )}

          {/* Resource Analysis — compact grid */}
          {data.resource_analysis && (
            <div className="border-t border-slate-700/30 pt-3">
              <p className="mb-2 text-[11px] font-medium text-slate-500">Resource Analysis</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
                {RESOURCES.map((key) => {
                  const entry = (data.resource_analysis as Record<string, Record<string, unknown>>)[key];
                  if (!entry) return null;
                  const isPrototype = key === "battery" || key === "flexible_demand";
                  return (
                    <div key={key} className="space-y-1 rounded-lg bg-slate-900/40 p-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-medium text-white">{RESOURCE_LABELS[key]}</span>
                        {isPrototype && <span className="text-[9px] text-amber-400">PROTOTYPE</span>}
                      </div>
                      <p className="text-[11px] text-slate-400">
                        <span className="text-white">{fmtMw(entry.current_generation_mw as number | null)}</span>
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Current Recommendation — compact */}
          {data.current_recommendation && (
            <div className="border-t border-slate-700/30 pt-3">
              <p className="mb-2 text-[11px] font-medium text-slate-500">Current Recommendation</p>
              <div className="mb-2 grid grid-cols-3 gap-4">
                <div>
                  <span className="text-[10px] text-slate-500">Initial Deficit</span>
                  <p className="text-sm font-semibold text-red-400">{fmtMw(data.current_recommendation.initial_deficit_mw)}</p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Total Support</span>
                  <p className="text-sm font-semibold text-emerald-400">{fmtMw(data.current_recommendation.total_support_mw)}</p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Remaining Gap</span>
                  <p className={`text-sm font-semibold ${data.current_recommendation.remaining_gap_mw > 0 ? "text-red-400" : "text-emerald-400"}`}>
                    {fmtMw(data.current_recommendation.remaining_gap_mw)}
                  </p>
                </div>
              </div>

              {data.current_recommendation.recommended_deployment?.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-slate-700/60">
                        <th className="pb-1 pr-3 font-medium text-slate-400">Zone</th>
                        <th className="pb-1 pr-3 font-medium text-slate-400">Resource</th>
                        <th className="pb-1 font-medium text-slate-400">Support (MW)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.current_recommendation.recommended_deployment.map((d, i) => (
                        <tr key={i} className="border-b border-slate-700/30">
                          <td className="py-1 pr-3 text-white">{d.zone}</td>
                          <td className="py-1 pr-3 text-white">{d.resource}</td>
                          <td className="py-1 text-white">{fmtMw(d.support_mw)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Data Sources — inline badges */}
          <div className="flex flex-wrap gap-1.5 border-t border-slate-700/30 pt-3">
            {Object.entries(data.data_source).map(([key, val]) => (
              <span key={key} className="rounded bg-slate-900/60 px-2 py-0.5 text-[10px] text-slate-400">
                {key}: {val}
              </span>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
