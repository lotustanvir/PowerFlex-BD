"use client";

import { useDecisionSupport } from "@/hooks/useDecisionSupport";
import type { Recommendation } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: "text-red-400",
  HIGH: "text-amber-400",
  MEDIUM: "text-blue-400",
  LOW: "text-emerald-400",
  INFORMATIONAL: "text-slate-400",
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  RULE_BASED: "Rule-based",
  HISTORICAL_ANALYSIS: "Historical",
  SYSTEM_STATUS: "System",
  FORECAST: "Forecast",
  SIMULATION: "Simulation",
  MODEL_BASED: "Model",
};

const DATA_STATUS_LABELS: Record<string, string> = {
  LIVE: "Live",
  HISTORICAL: "Historical",
  CACHED: "Cached",
  ESTIMATED: "Estimated",
  MODELED: "Modeled",
  SYNTHETIC: "Synthetic",
  UNAVAILABLE: "Unavailable",
};

function TopRecommendation({ rec }: { rec: Recommendation }) {
  return (
    <div className="space-y-1.5 rounded-lg bg-slate-900/40 p-3">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] font-semibold ${PRIORITY_COLORS[rec.priority] || "text-slate-400"}`}>
          {rec.priority}
        </span>
        <span className="text-[11px] font-medium text-slate-300">{rec.title}</span>
      </div>
      <p className="text-[11px] leading-relaxed text-slate-400">{rec.summary}</p>
      <p className="text-[10px] text-slate-500">{rec.expected_impact}</p>
    </div>
  );
}

function ForecastGateWarning({
  forecastReady,
  observations,
}: {
  forecastReady: boolean;
  observations: number;
}) {
  if (forecastReady) return null;

  return (
    <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 p-2">
      <p className="text-[10px] text-amber-400">
        Forecast unavailable ({observations}/168 observations).
      </p>
    </div>
  );
}

function MetadataBar({
  sourceType,
  dataStatus,
  confidence,
  timestamp,
}: {
  sourceType: string;
  dataStatus: string;
  confidence: number;
  timestamp: string;
}) {
  const formattedTime = (() => {
    try {
      const d = new Date(timestamp);
      return d.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "Asia/Dhaka",
      });
    } catch {
      return timestamp;
    }
  })();

  return (
    <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500">
      <span>
        Source: <span className="text-cyan-400">{SOURCE_TYPE_LABELS[sourceType] || sourceType}</span>
      </span>
      <span>
        Data: <span className="text-emerald-400">{DATA_STATUS_LABELS[dataStatus] || dataStatus}</span>
      </span>
      <span>
        Conf: <span className="text-blue-400">{confidence.toFixed(0)}%</span>
      </span>
      <span className="ml-auto text-slate-600">{formattedTime}</span>
    </div>
  );
}

export default function SmartInsights() {
  const { data, error, loading } = useDecisionSupport();

  if (loading && !data) return <LoadingSkeleton lines={3} />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <ErrorState message="No data available" />;

  const recommendations = data.recommendations || [];
  const topRec = recommendations.length > 0 ? recommendations[0] : null;
  const metadata = data.metadata;
  const missingInputs = data.missing_inputs || [];
  const hasDegradedData = missingInputs.length > 0;

  if (recommendations.length === 0 && !hasDegradedData) {
    return (
      <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
          <h3 className="text-xs font-semibold text-slate-200">Smart Insights</h3>
        </div>
        <EmptyState title="System operating within normal parameters" />
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center gap-2">
        <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
        <h3 className="text-xs font-semibold text-slate-200">Smart Insights</h3>
        {metadata && (
          <span className="ml-auto text-[10px] text-slate-600">
            {recommendations.length} active
          </span>
        )}
      </div>

      <ForecastGateWarning
        forecastReady={metadata?.forecast_available ?? false}
        observations={metadata?.independent_observations ?? 0}
      />

      {topRec && <TopRecommendation rec={topRec} />}

      {hasDegradedData && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 p-2">
          <p className="text-[10px] text-amber-400">
            Degraded ({missingInputs.length} source{missingInputs.length !== 1 ? "s" : ""} unavailable)
          </p>
        </div>
      )}

      {metadata && (
        <MetadataBar
          sourceType={metadata.source_type}
          dataStatus={metadata.data_status}
          confidence={metadata.confidence_average}
          timestamp={data.timestamp}
        />
      )}
    </div>
  );
}
