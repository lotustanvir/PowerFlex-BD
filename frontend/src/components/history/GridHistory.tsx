"use client";

import { useState, useEffect, useCallback } from "react";
import { usePolling } from "@/hooks/usePolling";
import type { GridHistoryResponse } from "@/lib/types";
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

export default function GridHistory() {
  const [page, setPage] = useState(0);
  const [data, setData] = useState<GridHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = page * PAGE_SIZE;
      const res = await fetch(
        `${API_BASE}/api/grid/history?limit=${PAGE_SIZE}&offset=${offset}`,
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
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Grid Snapshots
        </h3>
        {data && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {data.total} total records
          </span>
        )}
      </div>

      {loading && !data && <LoadingSkeleton lines={8} />}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
          <p className="text-sm text-red-700 dark:text-red-300">
            Failed to load grid history: {error}
          </p>
          <button
            onClick={fetchData}
            className="mt-2 text-sm font-medium text-red-600 underline hover:text-red-800 dark:text-red-400"
          >
            Retry
          </button>
        </div>
      )}

      {data && data.data.length === 0 && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center dark:border-gray-700 dark:bg-gray-800">
          <p className="text-gray-500 dark:text-gray-400">No grid snapshots recorded yet.</p>
        </div>
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Timestamp</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Demand</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Supply</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Deficit</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Load Shed</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Status</th>
                  <th className="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.data.map((row) => (
                  <tr key={row.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{formatDate(row.timestamp)}</td>
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{fmtMw(row.demand_mw)}</td>
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{fmtMw(row.supply_mw)}</td>
                    <td className={`px-4 py-3 ${row.deficit_mw && row.deficit_mw > 0 ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"}`}>
                      {fmtMw(row.deficit_mw)}
                    </td>
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{fmtMw(row.load_shedding_mw)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        row.grid_status === "STRESSED" || row.grid_status === "CRITICAL"
                          ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                          : "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                      }`}>
                        {row.grid_status || "N/A"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        row.risk_level === "HIGH" || row.risk_level === "CRITICAL"
                          ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                          : row.risk_level === "MODERATE"
                          ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                          : "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
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
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, data.total)} of {data.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
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
