"use client";

import { useLoadShieldData } from "@/hooks/useLoadShieldData";
import type { GridRiskComponent, GridRiskScenario } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { RiskBadge } from "@/components/ui/RiskBadge";

function RiskGauge({ score, level }: { score: number; level: string }) {
  const rotation = (score / 100) * 180 - 90;
  const color =
    level === "LOW"
      ? "#10b981"
      : level === "MODERATE"
        ? "#eab308"
        : level === "ELEVATED"
          ? "#f97316"
          : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-16 w-32 overflow-hidden">
        <div className="absolute inset-0 rounded-t-full border-2 border-b-0 border-slate-700/60" />
        <div
          className="absolute bottom-0 left-1/2 h-12 w-0.5 origin-bottom transition-transform duration-700"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)`, backgroundColor: color }}
        />
        <div className="absolute bottom-0 left-1/2 h-2 w-2 -translate-x-1/2 rounded-full bg-white" />
      </div>
      <p className="mt-1 text-2xl font-bold tabular-nums text-white">{score.toFixed(1)}</p>
      <RiskBadge level={level} className="mt-0.5" />
    </div>
  );
}

function ComponentRow({ component }: { component: GridRiskComponent }) {
  const barColor =
    component.score <= 30
      ? "#10b981"
      : component.score <= 55
        ? "#eab308"
        : component.score <= 75
          ? "#f97316"
          : "#ef4444";

  return (
    <div className="flex items-center gap-2">
      <span className="w-24 shrink-0 truncate text-[11px] text-slate-400">{component.name}</span>
      <div className="h-1.5 flex-1 rounded-full bg-slate-700/60">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(component.score, 100)}%`, backgroundColor: barColor }}
          role="progressbar"
          aria-valuenow={component.score}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${component.name}: ${component.score.toFixed(1)} out of 100`}
        />
      </div>
      <span className="w-8 text-right font-mono text-[11px] text-white">{component.score.toFixed(0)}</span>
    </div>
  );
}

function ScenarioRow({ scenario }: { scenario: GridRiskScenario }) {
  return (
    <tr className="border-b border-slate-700/30">
      <td className="py-1.5 pr-2 text-[11px] text-white">{scenario.label}</td>
      <td className="py-1.5 pr-2 text-right font-mono text-[11px] text-white">{scenario.risk_score.toFixed(1)}</td>
      <td className="py-1.5 pr-2 text-right">
        <RiskBadge level={scenario.risk_level} />
      </td>
      <td className="py-1.5 text-right text-[11px] text-slate-400">{scenario.gap_mw.toFixed(0)} MW</td>
    </tr>
  );
}

export default function RiskIntelligence() {
  const { data, loading } = useLoadShieldData();

  if (loading && !data) {
    return (
      <section aria-label="Risk Intelligence" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Risk Intelligence</h2>
        <LoadingSkeleton lines={4} />
      </section>
    );
  }

  if (!data?.grid_risk) {
    return (
      <section aria-label="Risk Intelligence" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Risk Intelligence</h2>
        <div className="rounded-lg bg-slate-900/40 p-4 text-center">
          <p className="text-xs text-slate-400">Risk data unavailable</p>
        </div>
      </section>
    );
  }

  const risk = data.grid_risk;
  const scenarios = Object.entries(risk.scenarios);

  return (
    <section aria-label="Risk Intelligence" className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <h2 className="text-sm font-semibold text-white">Risk Intelligence</h2>

      {/* Gauge + Components */}
      <div className="flex items-start gap-4">
        <RiskGauge score={risk.composite_score} level={risk.risk_level} />
        <div className="flex-1 space-y-1.5">
          {risk.components.map((c) => (
            <ComponentRow key={c.name} component={c} />
          ))}
        </div>
      </div>

      {/* Scenario table */}
      {scenarios.length > 0 && (
        <div className="border-t border-slate-700/30 pt-2">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">Scenarios</p>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700/60">
                  <th className="pb-1 pr-2 text-[10px] font-medium text-slate-500">Scenario</th>
                  <th className="pb-1 pr-2 text-right text-[10px] font-medium text-slate-500">Score</th>
                  <th className="pb-1 pr-2 text-right text-[10px] font-medium text-slate-500">Level</th>
                  <th className="pb-1 text-right text-[10px] font-medium text-slate-500">Gap</th>
                </tr>
              </thead>
              <tbody>
                {scenarios.map(([key, s]) => (
                  <ScenarioRow key={key} scenario={s} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Data Sources */}
      {Object.keys(risk.data_sources).length > 0 && (
        <div className="flex flex-wrap gap-1 border-t border-slate-700/30 pt-2">
          {Object.entries(risk.data_sources).map(([src, cls]) => (
            <span key={src} className="rounded bg-slate-900/60 px-1.5 py-0.5 text-[9px] text-slate-500">
              {src}: {cls}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
