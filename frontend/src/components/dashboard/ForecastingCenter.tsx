"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { DemandForecastResponse, ForecastMetadata } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

const CLASSIFICATION_STYLES: Record<string, { border: string; bg: string; text: string; label: string }> = {
  PRODUCTION_READY: {
    border: "border-emerald-500/25",
    bg: "bg-emerald-500/8",
    text: "text-emerald-400",
    label: "Production Forecast",
  },
  INSUFFICIENT_HISTORICAL_DATA: {
    border: "border-amber-500/25",
    bg: "bg-amber-500/8",
    text: "text-amber-400",
    label: "Prototype Forecast",
  },
  SYNTHETIC_TRAINED: {
    border: "border-amber-500/25",
    bg: "bg-amber-500/8",
    text: "text-amber-400",
    label: "Synthetic Forecast",
  },
  VALIDATION_PENDING: {
    border: "border-blue-500/25",
    bg: "bg-blue-500/8",
    text: "text-blue-400",
    label: "Model Forecast",
  },
  DEVELOPMENT_ONLY: {
    border: "border-slate-500/25",
    bg: "bg-slate-500/8",
    text: "text-slate-400",
    label: "Development Only",
  },
};

function ForecastStatusBadge({ metadata }: { metadata: ForecastMetadata }) {
  const style = CLASSIFICATION_STYLES[metadata.forecast_classification] || CLASSIFICATION_STYLES.DEVELOPMENT_ONLY;

  return (
    <div className={`rounded-lg border ${style.border} ${style.bg} p-2.5`}>
      <div className="mb-1.5 flex items-center gap-2">
        <div className={`h-1.5 w-1.5 rounded-full ${metadata.production_ready ? "bg-emerald-400" : "bg-amber-400"}`} />
        <span className={`text-[11px] font-semibold ${style.text}`}>
          {style.label}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1 text-[10px]">
        <div>
          <span className="text-slate-500">Status: </span>
          <span className={style.text}>{metadata.forecast_classification}</span>
        </div>
        <div>
          <span className="text-slate-500">Ready: </span>
          <span className={metadata.production_ready ? "text-emerald-400" : "text-amber-400"}>
            {metadata.production_ready ? "Yes" : "No"}
          </span>
        </div>
      </div>
    </div>
  );
}

function ForecastDataQuality({ metadata }: { metadata: ForecastMetadata }) {
  const coveragePct = Math.min(100, (metadata.observation_count / metadata.minimum_required_observations) * 100);

  return (
    <div className="space-y-2 rounded-lg bg-slate-900/40 p-2.5">
      <div>
        <div className="mb-0.5 flex justify-between text-[10px]">
          <span className="text-slate-500">Observations</span>
          <span className="text-blue-400">
            {metadata.observation_count} / {metadata.minimum_required_observations}
          </span>
        </div>
        <div className="overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${coveragePct}%` }}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-1 text-[10px]">
        <div>
          <span className="text-slate-500">Coverage: </span>
          <span className="text-slate-300">{metadata.data_coverage_hours.toFixed(1)}h</span>
        </div>
        <div>
          <span className="text-slate-500">Training: </span>
          <span className={metadata.training_data_synthetic ? "text-amber-400" : "text-emerald-400"}>
            {metadata.training_data_synthetic ? "Synthetic" : "Real"}
          </span>
        </div>
      </div>
    </div>
  );
}

function ForecastHourlyChart({ forecasts }: { forecasts: DemandForecastResponse["hourly_forecast"] }) {
  if (!forecasts || forecasts.length === 0) return null;

  const maxDemand = Math.max(...forecasts.map((f) => f.predicted_demand_mw));
  const minDemand = Math.min(...forecasts.map((f) => f.predicted_demand_mw));
  const range = maxDemand - minDemand || 1;

  return (
    <div className="rounded-lg bg-slate-900/40 p-2.5">
      <p className="mb-2 text-[10px] font-medium text-slate-400">24-Hour Forecast</p>
      <div className="flex h-20 items-end gap-px">
        {forecasts.map((f, i) => {
          const height = ((f.predicted_demand_mw - minDemand) / range) * 80 + 20;
          const isPeak = f.predicted_demand_mw === maxDemand;
          return (
            <div
              key={i}
              className="flex flex-1 flex-col items-center"
              title={`${f.hour_bst}:00 BST - ${f.predicted_demand_mw.toFixed(0)} MW`}
            >
              <div
                className={`w-full rounded-t ${isPeak ? "bg-amber-500" : "bg-cyan-500/60"}`}
                style={{ height: `${height}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-0.5 flex justify-between text-[9px] text-slate-600">
        <span>{forecasts[0]?.hour_bst}:00</span>
        <span>{forecasts[forecasts.length - 1]?.hour_bst}:00</span>
      </div>
    </div>
  );
}

function ForecastSummary({ data }: { data: DemandForecastResponse }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="rounded-lg bg-slate-900/40 p-2">
        <p className="text-[10px] text-slate-500">Current Demand</p>
        <p className="text-sm font-bold text-cyan-400">
          {data.current_pgcb_demand_mw?.toFixed(0) || "N/A"} <span className="text-[10px] font-normal text-slate-500">MW</span>
        </p>
      </div>
      <div className="rounded-lg bg-slate-900/40 p-2">
        <p className="text-[10px] text-slate-500">Forecast Peak</p>
        <p className="text-sm font-bold text-amber-400">
          {data.forecast_peak_mw?.toFixed(0) || "N/A"} <span className="text-[10px] font-normal text-slate-500">MW</span>
        </p>
      </div>
      <div className="rounded-lg bg-slate-900/40 p-2">
        <p className="text-[10px] text-slate-500">Model</p>
        <p className="text-[11px] font-medium text-blue-400">
          {data.model || "N/A"}
        </p>
      </div>
      <div className="rounded-lg bg-slate-900/40 p-2">
        <p className="text-[10px] text-slate-500">Classification</p>
        <p className="text-[11px] font-medium text-emerald-400">
          {data.data_classification || "N/A"}
        </p>
      </div>
    </div>
  );
}

function ForecastUnavailableState({ metadata }: { metadata?: ForecastMetadata }) {
  if (!metadata) {
    return (
      <div className="py-4 text-center text-slate-500">
        <p className="text-[11px]">Forecast data unavailable</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 p-3">
        <p className="mb-1 text-[11px] text-amber-400">
          Production forecasting unavailable.
        </p>
        <p className="text-[10px] text-slate-500">
          Insufficient verified observations for production forecasting.
        </p>
      </div>
      <ForecastDataQuality metadata={metadata} />
    </div>
  );
}

export default function ForecastingCenter() {
  const { data, error, loading, refresh } =
    usePolling<DemandForecastResponse>({
      url: API_ENDPOINTS.DEMAND_FORECAST,
      intervalMs: 300000,
    });

  if (loading && !data) return <LoadingSkeleton lines={3} />;
  if (error) {
    return (
      <ErrorBoundary>
        <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
          <h3 className="text-xs font-semibold text-slate-200">Forecasting Center</h3>
          <div className="rounded-lg border border-red-500/20 bg-red-500/8 p-3">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  const metadata = data?.forecast_metadata;
  const isProductionReady = metadata?.production_ready ?? false;

  return (
    <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`h-1.5 w-1.5 rounded-full ${isProductionReady ? "bg-emerald-400" : "bg-amber-400 animate-pulse-slow"}`} />
          <h3 className="text-xs font-semibold text-slate-200">
            Forecasting Center
          </h3>
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300"
          aria-label="Refresh forecast"
        >
          Refresh
        </button>
      </div>

      {metadata && <ForecastStatusBadge metadata={metadata} />}

      {isProductionReady ? (
        <>
          <ForecastSummary data={data!} />
          <ForecastHourlyChart forecasts={data!.hourly_forecast || []} />
        </>
      ) : (
        <ForecastUnavailableState metadata={metadata} />
      )}
    </div>
  );
}
