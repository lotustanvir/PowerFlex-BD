"use client";

import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { GridHistoryResponse, GridHistoryItem } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

function DataQualityIndicator({
  rawRecords,
  independentObs,
  duplicateRate,
  coverageHours,
}: {
  rawRecords: number;
  independentObs: number;
  duplicateRate: number;
  coverageHours: number;
}) {
  const obsPct = Math.min(100, (independentObs / 168) * 100);

  return (
    <div className="space-y-2 rounded-lg bg-slate-900/40 p-2.5">
      <div>
        <div className="mb-0.5 flex justify-between text-[10px]">
          <span className="text-slate-500">Independent Observations</span>
          <span className="text-blue-400">{independentObs} / 168</span>
        </div>
        <div className="overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${obsPct}%` }}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-1 text-[10px]">
        <div>
          <span className="text-slate-500">Raw: </span>
          <span className="text-slate-300">{rawRecords}</span>
        </div>
        <div>
          <span className="text-slate-500">Duplicates: </span>
          <span className="text-amber-400">{(duplicateRate * 100).toFixed(0)}%</span>
        </div>
        <div>
          <span className="text-slate-500">Coverage: </span>
          <span className="text-slate-300">{coverageHours.toFixed(1)}h</span>
        </div>
        <div>
          <span className="text-slate-500">Source: </span>
          <span className="text-emerald-400">PGCB</span>
        </div>
      </div>
    </div>
  );
}

function DemandChart({ data }: { data: GridHistoryItem[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="py-4 text-center text-slate-500">
        <p className="text-[11px]">No verified historical observations.</p>
      </div>
    );
  }

  const validData = data.filter((d) => d.demand_mw != null && d.supply_mw != null);
  if (validData.length === 0) {
    return (
      <div className="py-4 text-center text-slate-500">
        <p className="text-[11px]">No verified demand/supply data.</p>
      </div>
    );
  }

  const maxDemand = Math.max(...validData.map((d) => d.demand_mw!));
  const maxSupply = Math.max(...validData.map((d) => d.supply_mw!));
  const maxVal = Math.max(maxDemand, maxSupply);

  return (
    <div className="rounded-lg bg-slate-900/40 p-2.5">
      <p className="mb-2 text-[10px] font-medium text-slate-400">Demand vs Supply</p>
      <div className="flex h-24 items-end gap-px">
        {validData.map((d, i) => {
          const demandH = (d.demand_mw! / maxVal) * 100;
          const supplyH = (d.supply_mw! / maxVal) * 100;
          const gap = d.demand_mw! - d.supply_mw!;
          const hasDeficit = gap > 0;

          return (
            <div
              key={i}
              className="flex flex-1 flex-col items-center gap-px"
              title={`${d.timestamp || "N/A"}\nDemand: ${d.demand_mw?.toFixed(0)} MW\nSupply: ${d.supply_mw?.toFixed(0)} MW`}
            >
              <div className="flex w-full gap-px items-end" style={{ height: "100%" }}>
                <div
                  className="flex-1 rounded-t bg-cyan-500/60"
                  style={{ height: `${demandH}%` }}
                />
                <div
                  className={`flex-1 rounded-t ${hasDeficit ? "bg-amber-500/60" : "bg-emerald-500/60"}`}
                  style={{ height: `${supplyH}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-1.5 flex items-center gap-3 text-[9px] text-slate-500">
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded bg-cyan-500/60" /> Demand
        </span>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded bg-emerald-500/60" /> Supply
        </span>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded bg-amber-500/60" /> Deficit
        </span>
      </div>
    </div>
  );
}

function DataTable({ data }: { data: GridHistoryItem[] }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-lg bg-slate-900/40">
      <div className="max-h-48 overflow-x-auto">
        <table className="w-full text-[10px]">
          <thead className="sticky top-0 bg-slate-900/80">
            <tr className="border-b border-slate-700">
              <th className="px-2 py-1.5 text-left font-medium text-slate-500">Time</th>
              <th className="px-2 py-1.5 text-right font-medium text-slate-500">Demand</th>
              <th className="px-2 py-1.5 text-right font-medium text-slate-500">Supply</th>
              <th className="px-2 py-1.5 text-right font-medium text-slate-500">Gap</th>
              <th className="px-2 py-1.5 text-right font-medium text-slate-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 15).map((item, i) => {
              const gap = (item.demand_mw || 0) - (item.supply_mw || 0);
              const hasDeficit = gap > 0;
              return (
                <tr key={i} className="border-b border-slate-700/30">
                  <td className="px-2 py-1 text-slate-300">
                    {item.timestamp
                      ? new Date(item.timestamp).toLocaleString("en-US", {
                          timeZone: "Asia/Dhaka",
                          hour: "2-digit",
                          minute: "2-digit",
                          hour12: false,
                        })
                      : "N/A"}
                  </td>
                  <td className="px-2 py-1 text-right text-cyan-400">
                    {item.demand_mw?.toFixed(0) || "N/A"}
                  </td>
                  <td className="px-2 py-1 text-right text-emerald-400">
                    {item.supply_mw?.toFixed(0) || "N/A"}
                  </td>
                  <td className={`px-2 py-1 text-right ${hasDeficit ? "text-amber-400" : "text-slate-400"}`}>
                    {gap > 0 ? `+${gap.toFixed(0)}` : gap.toFixed(0)}
                  </td>
                  <td className="px-2 py-1 text-right">
                    <span
                      className={`rounded px-1 py-0.5 text-[8px] ${
                        hasDeficit
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-emerald-500/20 text-emerald-400"
                      }`}
                    >
                      {hasDeficit ? "DEFICIT" : "OK"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {data.length > 15 && (
        <div className="border-t border-slate-700/30 px-2 py-1 text-center text-[9px] text-slate-600">
          Showing 15 of {data.length} records
        </div>
      )}
    </div>
  );
}

export default function HistoricalAnalytics() {
  const { data, error, loading, refresh } =
    usePolling<GridHistoryResponse>({
      url: API_ENDPOINTS.GRID_HISTORY,
      intervalMs: 300000,
    });

  if (loading && !data) return <LoadingSkeleton lines={3} />;
  if (error) {
    return (
      <ErrorBoundary>
        <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
          <h3 className="text-xs font-semibold text-slate-200">Historical Analytics</h3>
          <div className="rounded-lg border border-red-500/20 bg-red-500/8 p-3">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  const historyData = data?.data || [];
  const totalRecords = data?.total || 0;
  const rawRecords = totalRecords;
  const independentObs = historyData.length;
  const duplicateRate = rawRecords > 0 ? 1 - independentObs / rawRecords : 0;

  const coverageHours = (() => {
    if (historyData.length < 2) return 0;
    const timestamps = historyData
      .map((d) => d.timestamp ? new Date(d.timestamp).getTime() : null)
      .filter((t): t is number => t !== null)
      .sort((a, b) => a - b);
    if (timestamps.length < 2) return 0;
    const spanMs = timestamps[timestamps.length - 1] - timestamps[0];
    return spanMs / (1000 * 60 * 60);
  })();

  return (
    <div className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse-slow" />
          <h3 className="text-xs font-semibold text-slate-200">
            Historical Analytics
          </h3>
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300"
          aria-label="Refresh historical data"
        >
          Refresh
        </button>
      </div>

      <DataQualityIndicator
        rawRecords={rawRecords}
        independentObs={independentObs}
        duplicateRate={duplicateRate}
        coverageHours={coverageHours}
      />

      <DemandChart data={historyData} />

      <DataTable data={historyData} />
    </div>
  );
}
