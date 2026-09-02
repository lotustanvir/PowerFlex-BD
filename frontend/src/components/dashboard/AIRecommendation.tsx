"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { FullRecommendationResponse } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function AIRecommendation() {
  const { data, error, loading, refresh } = usePolling<FullRecommendationResponse>({
    url: API_ENDPOINTS.V3_FULL_RECOMMENDATION,
    intervalMs: 300000,
  });

  if (loading && !data) return <LoadingSkeleton />;
  if (error) {
    return (
      <ErrorBoundary>
        <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
          <p className="text-red-400">{error}</p>
        </div>
      </ErrorBoundary>
    );
  }

  const rec = data?.recommendation;

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">
          AI Planning Recommendation
        </h3>
        <button
          onClick={refresh}
          className="text-xs text-emerald-400 hover:text-emerald-300"
        >
          Refresh
        </button>
      </div>

      {rec ? (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Forecast Demand</p>
              <p className="text-xl font-bold text-amber-400">
                {rec.forecast_demand_mw !== null
                  ? `${rec.forecast_demand_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Forecast Supply</p>
              <p className="text-xl font-bold text-emerald-400">
                {rec.forecast_supply_mw !== null
                  ? `${rec.forecast_supply_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Expected Deficit</p>
              <p className={`text-xl font-bold ${
                rec.expected_deficit_mw !== null && rec.expected_deficit_mw > 0
                  ? "text-red-400"
                  : "text-emerald-400"
              }`}>
                {rec.expected_deficit_mw !== null
                  ? `${rec.expected_deficit_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
          </div>

          {rec.recommended_technology && (
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">
                Recommended Technology
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500">Technology</p>
                  <p className="text-lg font-bold text-blue-400">
                    {rec.recommended_technology.technology}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Capacity Factor</p>
                  <p className="text-lg font-bold text-cyan-400">
                    {rec.recommended_technology.capacity_factor !== null
                      ? `${(rec.recommended_technology.capacity_factor * 100).toFixed(0)}%`
                      : "N/A"}
                  </p>
                </div>
              </div>
              {rec.recommended_technology.reasons.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-slate-500 mb-1">Reasons:</p>
                  <ul className="text-xs text-slate-400 space-y-1">
                    {rec.recommended_technology.reasons.slice(0, 3).map((reason, i) => (
                      <li key={i}>• {reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <h4 className="text-sm font-semibold text-slate-300 mb-3">
              Recommended Capacity
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500">Capacity</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {rec.recommended_capacity_mw !== null
                    ? `${rec.recommended_capacity_mw.toFixed(0)} MW`
                    : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Expected Generation</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {rec.expected_hourly_generation_mw !== null
                    ? `${rec.expected_hourly_generation_mw.toFixed(0)} MW`
                    : "N/A"}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <p className="text-xs text-slate-500">Daily Energy</p>
                <p className="text-lg font-bold text-blue-400">
                  {rec.expected_daily_energy_mwh !== null
                    ? `${rec.expected_daily_energy_mwh.toFixed(0)} MWh`
                    : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Annual Energy</p>
                <p className="text-lg font-bold text-cyan-400">
                  {rec.expected_annual_energy_gwh !== null
                    ? `${rec.expected_annual_energy_gwh.toFixed(1)} GWh`
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>Model: {rec.model_used}</span>
            <span>Quality: {rec.data_quality}</span>
            <span>Score: {rec.site_score?.toFixed(0) || "N/A"}/100</span>
          </div>

          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
            <p className="text-xs text-amber-400">
              {rec.disclaimer}
            </p>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          Recommendation unavailable - insufficient data
        </div>
      )}
    </div>
  );
}
