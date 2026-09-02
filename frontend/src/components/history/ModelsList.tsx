"use client";

import { useState, useEffect, useCallback } from "react";
import type { ModelRegistryResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

const PAGE_SIZE = 20;

function formatDate(iso: string | null): string {
  if (!iso) return "N/A";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function fmtNum(v: number | null | undefined, decimals = 4): string {
  if (v == null) return "N/A";
  return v.toFixed(decimals);
}

export default function ModelsList() {
  const [page, setPage] = useState(0);
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);
  const [data, setData] = useState<ModelRegistryResponse | null>(null);
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
      if (activeFilter !== null) {
        params.set("is_active", String(activeFilter));
      }

      const res = await fetch(
        `${API_BASE}/api/models/history?${params.toString()}`,
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
  }, [page, activeFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-slate-100">
          Model Registry
        </h3>
        {data && (
          <span className="text-sm text-slate-400">
            {data.total} registered models
          </span>
        )}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        <button
          onClick={() => { setActiveFilter(null); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            activeFilter === null
              ? "bg-blue-600 text-white"
              : "border border-slate-600 bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          All
        </button>
        <button
          onClick={() => { setActiveFilter(true); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            activeFilter === true
              ? "bg-emerald-600 text-white"
              : "border border-slate-600 bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          Active
        </button>
        <button
          onClick={() => { setActiveFilter(false); setPage(0); }}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
            activeFilter === false
              ? "bg-slate-600 text-white"
              : "border border-slate-600 bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          Inactive
        </button>
      </div>

      {loading && !data && <LoadingSkeleton lines={6} />}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm text-red-400">
            Failed to load model registry: {error}
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
          <p className="text-slate-400">No models registered yet.</p>
        </div>
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 font-medium text-slate-300">Type</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Trained At</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Samples</th>
                  <th className="px-4 py-3 font-medium text-slate-300">MAE</th>
                  <th className="px-4 py-3 font-medium text-slate-300">RMSE</th>
                  <th className="px-4 py-3 font-medium text-slate-300">R²</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {data.data.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-full bg-purple-500/20 px-2 py-1 text-xs font-medium text-purple-400">
                        {row.model_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-100">{formatDate(row.trained_at)}</td>
                    <td className="px-4 py-3 text-slate-100">{row.training_samples?.toLocaleString() || "N/A"}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtNum(row.mae)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtNum(row.rmse)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtNum(row.r2)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        row.is_active
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-slate-700 text-slate-300"
                      }`}>
                        {row.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
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
