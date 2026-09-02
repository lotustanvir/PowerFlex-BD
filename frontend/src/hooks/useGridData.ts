"use client";

import { usePolling } from "@/hooks/usePolling";
import type { GridLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";

const GRID_URL = `${API_BASE}/api/grid/live`;
const POLL_INTERVAL = 60000; // 1 minute

/**
 * Shared hook for Grid Live data.
 * Used by NationalOverview, EnergyMix, and GridIntelligence
 * to avoid triplicate polling of the same endpoint.
 */
export function useGridData() {
  return usePolling<GridLiveResponse>({
    url: GRID_URL,
    intervalMs: POLL_INTERVAL,
  });
}
