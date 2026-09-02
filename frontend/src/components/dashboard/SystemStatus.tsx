"use client";

import { useState, useEffect, useCallback, useRef } from "react";

type SystemStatusLevel = "LIVE" | "DEGRADED" | "OFFLINE";

interface SystemStatusResult {
  level: SystemStatusLevel;
  label: string;
  detail: string;
  lastCheck: Date | null;
  retry: () => Promise<void>;
}

const STATUS_CONFIG: Record<SystemStatusLevel, { color: string; bg: string; border: string }> = {
  LIVE: { color: "text-emerald-400", bg: "bg-emerald-500/12", border: "border-emerald-500/25" },
  DEGRADED: { color: "text-amber-400", bg: "bg-amber-500/12", border: "border-amber-500/25" },
  OFFLINE: { color: "text-red-400", bg: "bg-red-500/12", border: "border-red-500/25" },
};

function classifyStatus(healthOk: boolean, gridOk: boolean, loadshieldOk: boolean): SystemStatusLevel {
  if (healthOk && gridOk && loadshieldOk) return "LIVE";
  if (healthOk || gridOk || loadshieldOk) return "DEGRADED";
  return "OFFLINE";
}

export function useSystemStatus(): SystemStatusResult {
  const [level, setLevel] = useState<SystemStatusLevel>("OFFLINE");
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [detail, setDetail] = useState("Checking connectivity...");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const check = useCallback(async () => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const [healthRes, gridRes, loadshieldRes] = await Promise.allSettled([
        fetch(`${API_BASE}/health`, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        }),
        fetch(`${API_BASE}/api/grid/live`, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        }),
        fetch(`${API_BASE}/api/loadshield/live`, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        }),
      ]);

      const healthOk = healthRes.status === "fulfilled" && healthRes.value.ok;
      const gridOk = gridRes.status === "fulfilled" && gridRes.value.ok;
      const loadshieldOk = loadshieldRes.status === "fulfilled" && loadshieldRes.value.ok;

      const newLevel = classifyStatus(healthOk, gridOk, loadshieldOk);
      setLevel(newLevel);
      setLastCheck(new Date());

      const parts: string[] = [];
      if (healthOk) parts.push("health");
      if (gridOk) parts.push("grid");
      if (loadshieldOk) parts.push("loadshield");
      setDetail(parts.length > 0 ? `${parts.join(", ")} connected` : "All endpoints unreachable");
    } catch {
      setLevel("OFFLINE");
      setLastCheck(new Date());
      setDetail("Backend unreachable");
    } finally {
      clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    check();
    intervalRef.current = setInterval(check, 30000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [check]);

  return {
    level,
    label: level,
    detail,
    lastCheck,
    retry: check,
  };
}

export function SystemStatusBadge({ status }: { status: SystemStatusResult }) {
  const config = STATUS_CONFIG[status.level];

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 ${config.bg} ${config.border}`}
      role="status"
      aria-label={`System status: ${status.level}`}
    >
      <span className="relative flex h-2 w-2">
        {status.level === "LIVE" && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 bg-emerald-400" />
        )}
        <span
          className={`relative inline-flex h-2 w-2 rounded-full ${
            status.level === "LIVE" ? "bg-emerald-400" : status.level === "DEGRADED" ? "bg-amber-400" : "bg-red-400"
          }`}
        />
      </span>
      <span className={`text-[10px] font-semibold ${config.color}`}>
        {status.label}
      </span>
      {status.lastCheck && (
        <span className="text-[9px] text-slate-500">
          {status.lastCheck.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
            timeZone: "Asia/Dhaka",
          })}
        </span>
      )}
    </div>
  );
}
