"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { SourcesResponse } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function DataSourcesStatus() {
  const { data, error, loading, refresh } = usePolling<SourcesResponse>({
    url: API_ENDPOINTS.V3_SOURCES,
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

  const sources = data?.sources ? Object.values(data.sources) : [];
  const summary = data?.summary;

  const statusColors: Record<string, string> = {
    ACTIVE: "text-emerald-400 bg-emerald-500/10",
    INACTIVE: "text-red-400 bg-red-500/10",
    UNVERIFIED: "text-amber-400 bg-amber-500/10",
    RATE_LIMITED: "text-orange-400 bg-orange-500/10",
    BLOCKED: "text-red-400 bg-red-500/10",
  };

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">
          Data Sources
        </h3>
        <button
          onClick={refresh}
          className="text-xs text-emerald-400 hover:text-emerald-300"
        >
          Refresh
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-400">{summary.active_sources}</p>
            <p className="text-xs text-slate-500">Active</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-amber-400">{summary.unverified_sources}</p>
            <p className="text-xs text-slate-500">Unverified</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-400">{summary.ml_models}</p>
            <p className="text-xs text-slate-500">ML Models</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-cyan-400">{summary.calculated}</p>
            <p className="text-xs text-slate-500">Calculated</p>
          </div>
        </div>
      )}

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {sources.map((source) => (
          <div
            key={source.source_id}
            className="flex items-center justify-between p-2 rounded bg-slate-800/30"
          >
            <div className="flex-1">
              <p className="text-sm text-slate-300">{source.name}</p>
              <p className="text-xs text-slate-500">{source.organization}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">{source.classification}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                statusColors[source.status] || "text-slate-400 bg-slate-500/10"
              }`}>
                {source.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-xs text-slate-600">
        Total: {sources.length} sources
      </div>
    </div>
  );
}
