"use client";

import { useDecisionSupport } from "@/hooks/useDecisionSupport";
import type {
  DecisionSupportResponse,
  Recommendation,
} from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: "border-red-500/30 bg-red-500/8",
  HIGH: "border-amber-500/30 bg-amber-500/8",
  MEDIUM: "border-blue-500/30 bg-blue-500/8",
  LOW: "border-emerald-500/30 bg-emerald-500/8",
  INFORMATIONAL: "border-slate-500/30 bg-slate-500/8",
};

const PRIORITY_BADGES: Record<string, string> = {
  CRITICAL: "bg-red-500/20 text-red-400",
  HIGH: "bg-amber-500/20 text-amber-400",
  MEDIUM: "bg-blue-500/20 text-blue-400",
  LOW: "bg-emerald-500/20 text-emerald-400",
  INFORMATIONAL: "bg-slate-500/20 text-slate-400",
};

function RecommendationCard({ rec }: { rec: Recommendation }) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        PRIORITY_STYLES[rec.priority] || "border-slate-700/30 bg-slate-800/30"
      }`}
    >
      <div className="mb-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span
            className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
              PRIORITY_BADGES[rec.priority] || "bg-slate-500/20 text-slate-400"
            }`}
          >
            {rec.priority}
          </span>
          <h4 className="text-[11px] font-semibold text-slate-200">
            {rec.title}
          </h4>
        </div>
        <span className="text-[10px] text-slate-500">
          {rec.confidence.toFixed(0)}%
        </span>
      </div>

      <p className="mb-2 text-[11px] leading-relaxed text-slate-400">{rec.summary}</p>

      <div className="flex items-center gap-3 text-[10px] text-slate-500">
        <span>Source: <span className="text-cyan-400">{rec.evidence.source_type}</span></span>
        <span>Data: <span className="text-emerald-400">{rec.evidence.data_status}</span></span>
      </div>

      <p className="mt-1.5 text-[10px] text-slate-500">{rec.expected_impact}</p>
    </div>
  );
}

function SystemHealthBadge({
  health,
}: {
  health: DecisionSupportResponse["metadata"];
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-500">
      <span>
        Source: <span className="text-cyan-400">{health.source_type}</span>
      </span>
      <span>
        Data: <span className="text-emerald-400">{health.data_status}</span>
      </span>
      <span>
        Obs: <span className="text-blue-400">{health.independent_observations}</span>
      </span>
      <span>
        Forecast:{" "}
        {health.forecast_available ? (
          <span className="text-emerald-400">Yes</span>
        ) : (
          <span className="text-amber-400">No</span>
        )}
      </span>
    </div>
  );
}

export default function DecisionHub() {
  const { data, error, loading, refresh } = useDecisionSupport();

  if (loading && !data) return <LoadingSkeleton lines={3} />;
  if (error) {
    return (
      <ErrorBoundary>
        <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
          <h3 className="text-xs font-semibold text-slate-200">Decision Support</h3>
          <div className="rounded-lg border border-red-500/20 bg-red-500/8 p-3">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  const recommendations = data?.recommendations || [];
  const metadata = data?.metadata;

  return (
    <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
          <h3 className="text-xs font-semibold text-slate-200">
            Decision Support
          </h3>
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300"
          aria-label="Refresh decision support"
        >
          Refresh
        </button>
      </div>

      {metadata && <SystemHealthBadge health={metadata} />}

      <div className="space-y-2">
        {recommendations.length === 0 ? (
          <div className="py-4 text-center text-[11px] text-slate-500">
            No active recommendations
          </div>
        ) : (
          recommendations.map((rec, i) => (
            <RecommendationCard key={`${rec.type}-${i}`} rec={rec} />
          ))
        )}
      </div>

      {data?.missing_inputs && data.missing_inputs.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 p-2">
          <p className="text-[10px] text-amber-400">
            Missing: {data.missing_inputs.join(", ")}
          </p>
        </div>
      )}
    </div>
  );
}
