"use client";

import { useState, useEffect, useCallback } from "react";
import type { LoadShieldHistoryResponse } from "@/lib/types";
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

function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

export default function LoadShieldHistory() {
  const [page, setPage] = useState(0);
  const [data, setData] = useState<LoadShieldHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = page * PAGE_SIZE;
      const res = await fetch(
        `${API_BASE}/api/loadshield/history?limit=${PAGE_SIZE}&offset=${offset}`,
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
  }, [page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100">
          LoadShield Dispatches
        </h3>
        {data && (
          <span className="text-sm text-slate-400">
            {data.total} total records
          </span>
        )}
      </div>

      {loading && !data && <LoadingSkeleton lines={8} />}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm text-red-400">
            Failed to load dispatch history: {error}
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
          <p className="text-slate-400">No dispatches recorded yet.</p>
        </div>
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 font-medium text-slate-300">Timestamp</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Demand</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Supply</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Deficit</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Solar</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Wind</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Battery</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Status</th>
                  <th className="px-4 py-3 font-medium text-slate-300">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {data.data.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 text-slate-100">{formatDate(row.timestamp)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.demand_mw)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.supply_mw)}</td>
                    <td className={`px-4 py-3 ${row.deficit_mw && row.deficit_mw > 0 ? "text-red-400" : "text-slate-100"}`}>
                      {fmtMw(row.deficit_mw)}
                    </td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.solar_mw)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.wind_mw)}</td>
                    <td className="px-4 py-3 text-slate-100">{fmtMw(row.battery_mw)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        row.status === "DEFICIT_COVERED"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : row.status === "SUPPLY_SUFFICIENT"
                          ? "bg-blue-500/20 text-blue-400"
                          : "bg-amber-500/20 text-amber-400"
                      }`}>
                        {row.status || "N/A"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        row.risk_level === "HIGH" || row.risk_level === "CRITICAL"
                          ? "bg-red-500/20 text-red-400"
                          : row.risk_level === "MODERATE"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-emerald-500/20 text-emerald-400"
                      }`}>
                        {row.risk_level || "N/A"}
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
