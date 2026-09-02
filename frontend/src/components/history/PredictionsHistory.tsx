"use client";

import { useState, useEffect, useCallback } from "react";
import type { PredictionsHistoryResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

const PAGE_SIZE = 20;
const MODEL_TYPES = ["", "solar", "wind", "demand"];
const ZONES = ["", "Dhaka", "Chittagong", "Khulna", "Rajshahi", "Comilla", "Mymensingh", "Sylhet", "Barishal", "Rangpur"];

function formatDate(iso: string | null): string {
  if (!iso) return "N/A";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

export default function PredictionsHistory() {
  const [page, setPage] = useState(0);
  const [modelType, setModelType] = useState("");
  const [zone, setZone] = useState("");
  const [data, setData] = useState<PredictionsHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = page * PAGE_SIZE;
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
      });
      if (modelType) params.set("model_type", modelType);
      if (zone) params.set("zone", zone);

      const res = await fetch(
        `${API_BASE}/api/predictions/history?${params.toString()}`,
        { headers: { Accept: "application/json" } }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fetch failed");
    } finally {
      setLoading(false);
    }
  }, [page, modelType, zone]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-slate-100">
          AI Predictions
        </h3>
        {data && (
          <span className="text-sm text-slate-400">
            {data.total} total records
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-300">
            Model Type
          </label>
          <select
            value={modelType}
            onChange={(e) => { setModelType(e.target.value); setPage(0); }}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-100"
          >
            <option value="">All</option>
            {MODEL_TYPES.filter(Boolean).map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-300">
            Zone
          </label>
          <select
            value={zone}
            onChange={(e) => { setZone(e.target.value); setPage(0); }}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-100"
          >
            <option value="">All</option>
            {ZONES.filter(Boolean).map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && !data && <LoadingSkeleton lines={8} />}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm text-red-400">
            Failed to load predictions: {error}
          </p>
          <button
            onClick={fetchData}
            className="mt-2 text-sm font-medium text-red-400 underline hover:text-red-300"
          >
            Retry
          </button>
        </div>
      )}

      {data && data.data.length === 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-8 text-center">
          <p className="text-slate-400">No predictions recorded yet.</p>
        </div>
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 font-medium text-slate-300">Timestamp</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Model</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Zone</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Predicted</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Actual</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Version</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {data.data.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 text-slate-100">{formatDate(row.timestamp)}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-full bg-blue-500/20 px-2 py-1 text-xs font-medium text-blue-400">
                        {row.model_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-100">{row.zone || "N/A"}</td>
                    <td className="px-4 py-3 font-medium text-slate-100">{fmtMw(row.predicted_mw)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.actual_mw)}</td>
                    <td className="px-4 py-3 text-slate-400">{row.model_version || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">
              Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, data.total)} of {data.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
