"use client";

import { usePolling } from "@/hooks/usePolling";
import type { SolarLiveResponse, WindLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import { fmtMw } from "@/lib/utils";
import DataBadge from "@/components/ui/DataBadge";
import { LiveIndicator } from "@/components/ui/LiveIndicator";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

function RenewableCard({
  title,
  icon,
  color,
  generation,
  generationLabel,
  bestZone,
  bestZoneDetail,
  forecastHours,
  status,
  classification,
  dataAvailable,
}: {
  title: string;
  icon: string;
  color: string;
  generation: number | null | undefined;
  generationLabel: string;
  bestZone: string | null | undefined;
  bestZoneDetail: string | null | undefined;
  forecastHours: number | undefined;
  status: string | undefined;
  classification: string;
  dataAvailable: boolean;
}) {
  return (
    <div className="space-y-2 rounded-lg bg-slate-900/40 p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-sm" aria-hidden="true">{icon}</span>
          <h3 className="text-[11px] font-semibold text-white">{title}</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <DataBadge classification={classification} />
          <LiveIndicator status={dataAvailable ? "live" : "unavailable"} />
        </div>
      </div>

      {!dataAvailable && (
        <div className="rounded border border-amber-500/20 bg-amber-500/8 p-2">
          <p className="text-[10px] text-amber-400">Data unavailable</p>
        </div>
      )}

      {dataAvailable && (
        <div className="space-y-1.5">
          <div>
            <span className="text-[9px] font-medium uppercase tracking-wider text-slate-500">
              {generationLabel}
            </span>
            <p className={`text-base font-bold ${color}`}>
              {fmtMw(generation)}
            </p>
          </div>

          {bestZone && (
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wider text-slate-500">
                Best Zone
              </span>
              <p className="text-[11px] font-medium text-white">{bestZone}</p>
              {bestZoneDetail && (
                <p className="text-[10px] text-slate-400">{bestZoneDetail}</p>
              )}
            </div>
          )}

          <div className="flex items-center gap-3 text-[10px] text-slate-500">
            {forecastHours != null && (
              <span>Forecast: {forecastHours}h</span>
            )}
            {status && <span>Status: {status}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

export default function RenewableStatus() {
  const { data: solarData, loading: solarLoading, error: solarError, refresh: refreshSolar } =
    usePolling<SolarLiveResponse>({
      url: `${API_BASE}/api/solar/live`,
      intervalMs: 300000,
    });

  const { data: windData, loading: windLoading, error: windError, refresh: refreshWind } =
    usePolling<WindLiveResponse>({
      url: `${API_BASE}/api/wind/live`,
      intervalMs: 300000,
    });

  const solarAvailable = !solarError && !!solarData;
  const windAvailable = !windError && !!windData;

  const isLoading = (solarLoading && !solarData) || (windLoading && !windData);

  return (
    <section aria-label="Renewable Energy Status" className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Renewable Status</h2>
        <button
          onClick={() => { refreshSolar(); refreshWind(); }}
          className="text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
          disabled={solarLoading || windLoading}
          aria-label="Refresh renewable data"
        >
          Refresh
        </button>
      </div>

      {isLoading && <LoadingSkeleton lines={3} />}

      <div className="space-y-2">
        <RenewableCard
          title="Solar Energy"
          icon="☀️"
          color="text-amber-400"
          generation={solarData?.best_opportunity?.predicted_generation_mw_per_1mw}
          generationLabel="Best Zone (per 1 MW installed)"
          bestZone={solarData?.best_forecast_zone?.zone}
          bestZoneDetail={
            solarData?.best_forecast_zone?.expected_energy_mwh_per_1mw_24h != null
              ? `${solarData.best_forecast_zone.expected_energy_mwh_per_1mw_24h.toFixed(2)} MWh/1MW (24h)`
              : undefined
          }
          forecastHours={solarData?.forecast_hours}
          status={solarData?.status}
          classification="FORECAST"
          dataAvailable={solarAvailable}
        />

        <RenewableCard
          title="Wind Energy"
          icon="💨"
          color="text-cyan-400"
          generation={windData?.best_opportunity?.predicted_generation_mw_per_1mw}
          generationLabel="Best Zone (per 1 MW installed)"
          bestZone={windData?.best_forecast_zone?.zone}
          bestZoneDetail={
            windData?.best_forecast_zone?.modeled_capacity_factor_pct != null
              ? `Capacity factor: ${windData.best_forecast_zone.modeled_capacity_factor_pct.toFixed(1)}%`
              : undefined
          }
          forecastHours={windData?.forecast_hours}
          status={windData?.status}
          classification="CALCULATED"
          dataAvailable={windAvailable}
        />
      </div>
    </section>
  );
}
