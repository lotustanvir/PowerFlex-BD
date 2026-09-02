"use client";

import { useGridData } from "@/hooks/useGridData";
import { LiveIndicator } from "@/components/ui/LiveIndicator";
import DataBadge from "@/components/ui/DataBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

function DataRow({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-[10px] text-slate-500">{label}</span>
      <span className={`text-[11px] font-medium ${accent ? "text-white" : "text-slate-300"}`}>
        {value}
      </span>
    </div>
  );
}

export default function GridIntelligence() {
  const { data, loading, error, lastUpdated, refresh } = useGridData();

  const snapshot = data?.grid_snapshot;

  if (loading && !data) {
    return (
      <section aria-label="Grid Intelligence" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Grid Intelligence</h2>
        <LoadingSkeleton lines={4} />
      </section>
    );
  }

  if (error && !data) {
    return (
      <section aria-label="Grid Intelligence" className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-white">Grid Intelligence</h2>
        <ErrorState message={`Grid intelligence unavailable: ${error}`} onRetry={refresh} />
      </section>
    );
  }

  return (
    <section aria-label="Grid Intelligence" className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white">Grid Intelligence</h2>
          <LiveIndicator status={data?.live ? "live" : "delayed"} lastUpdated={lastUpdated} />
        </div>
        <button
          onClick={refresh}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
          disabled={loading}
          aria-label="Refresh grid data"
        >
          Refresh
        </button>
      </div>

      <div className="flex items-center gap-2">
        <DataBadge classification={data?.data_classification || "DATA_UNAVAILABLE"} />
        {data?.grid_status && (
          <span className="rounded-full bg-slate-700/50 px-2 py-0.5 text-[10px] text-slate-300">
            {data.grid_status}
          </span>
        )}
      </div>

      {snapshot ? (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <DataRow label="Frequency" value={snapshot.frequency_hz != null ? `${snapshot.frequency_hz} Hz` : "N/A"} />
            <DataRow label="Classification" value={snapshot.data_classification || "N/A"} accent />
            <DataRow label="Timestamp" value={snapshot.timestamp || "N/A"} />
            {lastUpdated && (
              <DataRow label="Fetched" value={lastUpdated.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Dhaka" })} />
            )}
          </div>

          {snapshot.data_availability && Object.keys(snapshot.data_availability).length > 0 && (
            <div className="flex flex-wrap gap-1 border-t border-slate-700/30 pt-2">
              {Object.entries(snapshot.data_availability).map(([k, v]) => (
                <span key={k} className="rounded bg-slate-900/60 px-1.5 py-0.5 text-[9px] text-slate-500">
                  {k}: {v}
                </span>
              ))}
            </div>
          )}

          {snapshot.remarks && (
            <div className="rounded-lg bg-slate-900/40 p-2">
              <p className="text-[10px] leading-relaxed text-slate-500">{snapshot.remarks}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 p-3 text-center">
          <p className="text-[11px] text-amber-400">No grid snapshot available</p>
        </div>
      )}
    </section>
  );
}
