"use client";

import { usePolling } from "@/hooks/usePolling";
import type { ResourceItem } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

interface NuclearResponse {
  project: string;
  module: string;
  resource: ResourceItem;
}

export default function NuclearDetail() {
  const { data, loading, error, lastUpdated, refresh } =
    usePolling<NuclearResponse>({
      url: `${API_BASE}/api/resources/nuclear`,
      intervalMs: 300000,
    });

  if (loading && !data) return <LoadingSkeleton lines={4} />;
  if (error && !data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">Failed to load nuclear data.</p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
        <button onClick={refresh} className="mt-4 text-sm text-emerald-400 hover:underline">
          Retry
        </button>
      </div>
    );
  }
  if (!data) return null;

  const { resource } = data;

  return (
    <section className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Nuclear — Rooppur Power Plant</h2>
        <div className="flex items-center gap-2">
          <DataBadge classification={resource.resource_status || "DATA_UNAVAILABLE"} />
          <RefreshButton onClick={refresh} loading={loading} />
        </div>
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-400">Last updated: {lastUpdated.toLocaleString()}</p>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase tracking-wide">Generation</span>
          <p className="mt-1 text-2xl font-bold text-white">
            {resource.generation_mw != null ? `${resource.generation_mw} MW` : "Not available"}
          </p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase tracking-wide">Installed Capacity</span>
          <p className="mt-1 text-2xl font-bold text-blue-400">
            {resource.installed_capacity_mw != null ? `${resource.installed_capacity_mw} MW` : "N/A"}
          </p>
        </div>
      </div>

      {resource.resource_status === "UNDER_COMMISSIONING" && (
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
          <p className="font-medium text-yellow-300">Status: UNDER COMMISSIONING</p>
          <p className="mt-1 text-sm text-yellow-200/80">
            This plant is currently being commissioned and is not yet generating power.
          </p>
        </div>
      )}

      <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
        <span className="text-xs text-slate-400 uppercase tracking-wide mb-1 block">Source</span>
        <p className="text-white">{resource.source_metadata?.source || "N/A"}</p>
      </div>

      {resource.note && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase tracking-wide mb-1 block">Note</span>
          <p className="text-sm text-slate-300">{resource.note}</p>
        </div>
      )}
    </section>
  );
}
