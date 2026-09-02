"use client";

import { useState } from "react";
import { usePolling } from "@/hooks/usePolling";
import { API_ENDPOINTS } from "@/lib/api";
import type { LocationSearchResponse, LocationCandidate } from "@/lib/types";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function LocationIntelligence() {
  const [technology, setTechnology] = useState<string>("");
  const [selectedLocation, setSelectedLocation] = useState<LocationCandidate | null>(null);

  const url = technology
    ? `${API_ENDPOINTS.V3_LOCATION_SEARCH}?technology=${technology}`
    : API_ENDPOINTS.V3_LOCATION_SEARCH;

  const { data, error, loading, refresh } = usePolling<LocationSearchResponse>({
    url,
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

  const candidates = data?.candidates || [];

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">
          Location Intelligence
        </h3>
        <div className="flex items-center gap-2">
          <select
            value={technology}
            onChange={(e) => setTechnology(e.target.value)}
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-slate-300"
          >
            <option value="">All Technologies</option>
            <option value="SOLAR">Solar</option>
            <option value="WIND">Wind</option>
          </select>
          <button
            onClick={refresh}
            className="text-xs text-emerald-400 hover:text-emerald-300"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="mb-4 text-xs text-slate-500">
        {data?.candidate_count || 0} candidate locations found
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {candidates.map((candidate, idx) => (
          <div
            key={`${candidate.latitude}-${candidate.longitude}`}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedLocation?.latitude === candidate.latitude &&
              selectedLocation?.longitude === candidate.longitude
                ? "border-emerald-500 bg-emerald-500/10"
                : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
            }`}
            onClick={() => setSelectedLocation(candidate)}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-200">
                  {candidate.name}
                </p>
                <p className="text-xs text-slate-500">
                  {candidate.latitude.toFixed(4)}, {candidate.longitude.toFixed(4)}
                </p>
              </div>
              <div className="text-right">
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                  candidate.technology === "SOLAR"
                    ? "bg-yellow-500/20 text-yellow-400"
                    : "bg-cyan-500/20 text-cyan-400"
                }`}>
                  {candidate.technology}
                </span>
              </div>
            </div>
            {candidate.grid_information && (
              <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                <span>Grid: {candidate.grid_information.substation}</span>
                <span>{candidate.grid_information.distance_km} km</span>
                <span>{candidate.grid_information.voltage_kv} kV</span>
                <span className={
                  candidate.grid_information.grid_proximity === "EXCELLENT"
                    ? "text-emerald-400"
                    : candidate.grid_information.grid_proximity === "GOOD"
                    ? "text-blue-400"
                    : "text-amber-400"
                }>
                  {candidate.grid_information.grid_proximity}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {candidates.length === 0 && (
        <div className="text-center py-8 text-slate-500">
          No candidates found. Try a different technology filter.
        </div>
      )}
    </div>
  );
}
