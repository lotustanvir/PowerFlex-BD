"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { API_ENDPOINTS } from "@/lib/api";
import type { DecisionSupportResponse } from "@/lib/types";

interface DecisionSupportContextValue {
  data: DecisionSupportResponse | null;
  error: string | null;
  loading: boolean;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

const DecisionSupportContext =
  createContext<DecisionSupportContextValue | null>(null);

export function useDecisionSupport(): DecisionSupportContextValue {
  const ctx = useContext(DecisionSupportContext);
  if (!ctx) {
    throw new Error(
      "useDecisionSupport must be used within a DecisionSupportProvider"
    );
  }
  return ctx;
}

export function DecisionSupportProvider({
  children,
  intervalMs = 300000,
}: {
  children: ReactNode;
  intervalMs?: number;
}) {
  const [data, setData] = useState<DecisionSupportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch(API_ENDPOINTS.V3_DECISION_SUPPORT, {
        signal: abortRef.current.signal,
        headers: { Accept: "application/json" },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const raw = await response.json();
      setData(raw as DecisionSupportResponse);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Fetch failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(fetchData, intervalMs);

    return () => {
      abortRef.current?.abort();
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData, intervalMs]);

  return (
    <DecisionSupportContext.Provider
      value={{ data, error, loading, lastUpdated, refresh }}
    >
      {children}
    </DecisionSupportContext.Provider>
  );
}
