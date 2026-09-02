"use client";

import { usePolling } from "@/hooks/usePolling";
import type { WasteLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { DataBadge } from "@/components/ui/DataBadge";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

export default function WasteToEnergy() {
  const { data, loading, error, lastUpdated, refresh } =
    usePolling<WasteLiveResponse>({
      url: `${API_BASE}/api/resources/waste/live`,
      intervalMs: 300000,
    });

  if (loading && !data) return <LoadingSkeleton lines={6} />;
  if (error && !data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">Failed to load waste-to-energy data.</p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
        <button onClick={refresh} className="mt-4 text-sm text-emerald-400 hover:underline">
          Retry
        </button>
      </div>
    );
  }
  if (!data) return null;

  const { explanation, national_summary, projects, zone_allocation } = data;
  const zoneEntries = zone_allocation ? Object.entries(zone_allocation) : [];

  return (
    <section className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Waste-to-Energy — Bangladesh Intelligence</h2>
          <DataBadge classification={data.data_classification || "OFFICIAL_PROJECT_DATA"} />
        </div>
        <RefreshButton onClick={refresh} loading={loading} variant="dark" />
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-400">Last updated: {lastUpdated.toLocaleString()}</p>
      )}

      <p className="text-sm text-slate-300">{explanation}</p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase">Current Generation</span>
          <p className="mt-1 text-2xl font-bold text-green-400">{fmtMw(national_summary.total_operational_mw)}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase">Calculated Potential</span>
          <p className="mt-1 text-2xl font-bold text-blue-400">{fmtMw(national_summary.calculated_potential_mw)}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase">Planned Capacity</span>
          <p className="mt-1 text-2xl font-bold text-amber-400">{fmtMw(national_summary.total_planned_mw)}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase">Dispatchable</span>
          <p className="mt-1 text-2xl font-bold text-purple-400">{fmtMw(national_summary.calculated_dispatchable_mw)}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <span className="text-xs text-slate-400 uppercase">Daily Waste</span>
          <p className="mt-1 text-2xl font-bold text-orange-400">
            {national_summary.total_daily_waste_tonnes != null
              ? `${national_summary.total_daily_waste_tonnes.toLocaleString()} tonnes`
              : "N/A"}
          </p>
        </div>
      </div>

      {projects && projects.length > 0 && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-sm font-semibold text-white">Projects</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-800">
                <tr>
                  <th className="text-left p-3 text-slate-400">Name</th>
                  <th className="text-left p-3 text-slate-400">Location</th>
                  <th className="text-left p-3 text-slate-400">Capacity</th>
                  <th className="text-left p-3 text-slate-400">Status</th>
                  <th className="text-left p-3 text-slate-400">Technology</th>
                  <th className="text-left p-3 text-slate-400">Expected COD</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project, i) => (
                  <tr key={i} className="border-t border-slate-700/50">
                    <td className="p-3 text-white">{project.project_name}</td>
                    <td className="p-3 text-slate-300">{project.location.site || project.location.district}</td>
                    <td className="p-3 text-slate-300">{fmtMw(project.installed_capacity_mw)}</td>
                    <td className="p-3">
                      <DataBadge classification={project.status === "OPERATIONAL" ? "LIVE" : "PROTOTYPE"} />
                    </td>
                    <td className="p-3 text-slate-300">{project.technology}</td>
                    <td className="p-3 text-slate-300">{project.expected_cod ?? "TBD"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {zoneEntries.length > 0 && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">Zone Allocation</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {zoneEntries.map(([zone, info], i) => (
              <div key={i} className="rounded-lg border border-slate-700/50 bg-slate-900/50 p-3">
                <div className="text-white font-medium">{zone}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {typeof info === "object" && info !== null
                    ? JSON.stringify(info)
                    : String(info)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
