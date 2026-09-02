"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import { fmtMw } from "@/lib/utils";
import type { FullRecommendationResponse, DeficitResponse } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

const SEVERITY_STYLES: Record<string, string> = {
  NO_RISK: "bg-emerald-500/12 text-emerald-400 border-emerald-500/25",
  LOW: "bg-yellow-500/12 text-yellow-400 border-yellow-500/25",
  MODERATE: "bg-amber-500/12 text-amber-400 border-amber-500/25",
  HIGH: "bg-orange-500/12 text-orange-400 border-orange-500/25",
  CRITICAL: "bg-red-500/12 text-red-400 border-red-500/25",
  UNKNOWN: "bg-slate-500/12 text-slate-400 border-slate-500/25",
};

export default function EnergyInsights() {
  const { data: recData, loading: recLoading, error: recError } =
    usePolling<FullRecommendationResponse>({
      url: API_ENDPOINTS.V3_FULL_RECOMMENDATION,
      intervalMs: 300000,
    });

  const { data: deficitData, loading: deficitLoading, error: deficitError } =
    usePolling<DeficitResponse>({
      url: API_ENDPOINTS.V3_DEFICIT,
      intervalMs: 60000,
    });

  const rec = recData?.recommendation;
  const analysis = deficitData?.analysis;

  const isLoading = (recLoading && !recData) || (deficitLoading && !deficitData);

  return (
    <section aria-label="Energy Insights" className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <h2 className="text-xs font-semibold text-slate-200">Energy Insights</h2>

      {isLoading && <LoadingSkeleton lines={4} />}

      <div className="space-y-3">
        {/* Deficit Risk */}
        <div className="space-y-2 rounded-lg bg-slate-900/40 p-3">
          <p className="text-[10px] font-medium text-slate-400">Deficit Risk</p>

          {deficitError && !deficitData && (
            <p className="text-[10px] text-red-400">Deficit data unavailable</p>
          )}

          {analysis ? (
            <div className="space-y-2">
              <span
                className={`inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                  SEVERITY_STYLES[analysis.severity] || SEVERITY_STYLES.UNKNOWN
                }`}
              >
                {analysis.severity === "NO_RISK" ? "No Risk" : analysis.severity}
              </span>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="text-[9px] text-slate-500">Demand</p>
                  <p className="text-[11px] font-bold text-amber-400">{fmtMw(analysis.forecast_demand_mw)}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-500">Supply</p>
                  <p className="text-[11px] font-bold text-emerald-400">{fmtMw(analysis.forecast_supply_mw)}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-500">Gap</p>
                  <p className={`text-[11px] font-bold ${
                    analysis.forecast_gap_mw != null && analysis.forecast_gap_mw > 0 ? "text-red-400" : "text-emerald-400"
                  }`}>
                    {fmtMw(analysis.forecast_gap_mw)}
                  </p>
                </div>
              </div>

              {analysis.notes && (
                <p className="text-[10px] leading-relaxed text-slate-500">{analysis.notes}</p>
              )}
            </div>
          ) : !deficitError ? (
            <p className="text-[10px] text-slate-500">Awaiting deficit analysis</p>
          ) : null}
        </div>

        {/* System Insight */}
        <div className="space-y-2 rounded-lg bg-slate-900/40 p-3">
          <p className="text-[10px] font-medium text-slate-400">System Insight</p>

          {recError && !recData && (
            <p className="text-[10px] text-red-400">Recommendation data unavailable</p>
          )}

          {rec ? (
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="text-[9px] text-slate-500">Forecast Demand</p>
                  <p className="text-[11px] font-bold text-amber-400">{fmtMw(rec.forecast_demand_mw)}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-500">Forecast Supply</p>
                  <p className="text-[11px] font-bold text-emerald-400">{fmtMw(rec.forecast_supply_mw)}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-500">Expected Deficit</p>
                  <p className={`text-[11px] font-bold ${
                    rec.expected_deficit_mw != null && rec.expected_deficit_mw > 0
                      ? "text-red-400"
                      : "text-emerald-400"
                  }`}>
                    {fmtMw(rec.expected_deficit_mw)}
                  </p>
                </div>
              </div>

              {rec.recommended_technology && (
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-slate-500">Recommended:</span>
                  <span className="font-medium text-white">{rec.recommended_technology.technology || "N/A"}</span>
                  {rec.recommended_technology.suitability_score != null && (
                    <span className="text-slate-500">(score: {rec.recommended_technology.suitability_score})</span>
                  )}
                </div>
              )}

              {rec.recommended_location && (
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-slate-500">Location:</span>
                  <span className="font-medium text-white">
                    {typeof rec.recommended_location === "object" && rec.recommended_location !== null
                      ? (rec.recommended_location.division as string) || JSON.stringify(rec.recommended_location)
                      : "N/A"}
                  </span>
                </div>
              )}
            </div>
          ) : !recError ? (
            <p className="text-[10px] text-slate-500">Awaiting system analysis</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
