"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { DeficitResponse } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function DeficitAlert() {
  const { data, error, loading, refresh } = usePolling<DeficitResponse>({
    url: API_ENDPOINTS.V3_DEFICIT,
    intervalMs: 60000,
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

  const analysis = data?.analysis;
  const isDeficit = analysis?.gap_type === "DEFICIT_RISK";
  const isSurplus = analysis?.gap_type === "SURPLUS";

  const severityColors: Record<string, string> = {
    NO_RISK: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    LOW: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    MODERATE: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    HIGH: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    CRITICAL: "text-red-400 bg-red-500/10 border-red-500/30",
    UNKNOWN: "text-slate-400 bg-slate-500/10 border-slate-500/30",
  };

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">
          Supply Deficit Risk
        </h3>
        <button
          onClick={refresh}
          className="text-xs text-emerald-400 hover:text-emerald-300"
        >
          Refresh
        </button>
      </div>

      {analysis ? (
        <div className="space-y-4">
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${
            severityColors[analysis.severity] || severityColors.UNKNOWN
          }`}>
            {analysis.severity === "NO_RISK" ? "No Risk" : analysis.severity}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Demand</p>
              <p className="text-xl font-bold text-amber-400">
                {analysis.forecast_demand_mw !== null
                  ? `${analysis.forecast_demand_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Supply</p>
              <p className="text-xl font-bold text-emerald-400">
                {analysis.forecast_supply_mw !== null
                  ? `${analysis.forecast_supply_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-500">Gap</p>
              <p className={`text-xl font-bold ${
                isDeficit ? "text-red-400" : isSurplus ? "text-emerald-400" : "text-slate-400"
              }`}>
                {analysis.forecast_gap_mw !== null
                  ? `${analysis.forecast_gap_mw > 0 ? "+" : ""}${analysis.forecast_gap_mw.toFixed(0)} MW`
                  : "N/A"}
              </p>
            </div>
          </div>

          <div className="text-sm text-slate-400">
            Status: <span className={`font-medium ${
              isDeficit ? "text-red-400" : isSurplus ? "text-emerald-400" : "text-slate-300"
            }`}>
              {analysis.gap_type === "DEFICIT_RISK"
                ? "DEFICIT RISK"
                : analysis.gap_type === "SURPLUS"
                ? "SURPLUS"
                : analysis.gap_type}
            </span>
          </div>

          {isDeficit && analysis.forecast_gap_mw !== null && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <p className="text-sm text-red-400">
                Additional generation potentially required: <strong>{analysis.forecast_gap_mw.toFixed(0)} MW</strong>
              </p>
            </div>
          )}

          {analysis.notes && (
            <p className="text-xs text-slate-500">{analysis.notes}</p>
          )}

          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span>Source: {data?.data_source}</span>
            <span>Classification: {data?.classification}</span>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          Deficit analysis unavailable
        </div>
      )}
    </div>
  );
}
