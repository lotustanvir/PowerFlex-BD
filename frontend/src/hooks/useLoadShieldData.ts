"use client";

import { usePolling } from "@/hooks/usePolling";
import type { LoadShieldResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";

const LOADSHIELD_URL = `${API_BASE}/api/loadshield/live`;
const POLL_INTERVAL = 120000; // 2 minutes

/**
 * Shared hook for LoadShield data.
 * Both LoadShield and NineZoneAnalysis components use this hook
 * to avoid duplicate API calls.
 */
export function useLoadShieldData() {
  return usePolling<LoadShieldResponse>({
    url: LOADSHIELD_URL,
    intervalMs: POLL_INTERVAL,
  });
}
