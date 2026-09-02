"use client";

import { usePolling } from "@/hooks/usePolling";
import type { BiomassLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import DataBadge from "@/components/ui/DataBadge";
import RefreshButton from "@/components/ui/RefreshButton";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";

function formatNumber(value: number | null): string {
  if (value == null) return "N/A";
  return value.toLocaleString();
}

function MetricCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: number | null;
  unit?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-4">
      <p className="text-sm font-medium text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold text-white">
        {formatNumber(value)}
        {unit && value != null && (
          <span className="ml-1 text-sm font-normal text-slate-400">
            {unit}
          </span>
        )}
      </p>
    </div>
  );
}

export default function BiomassDetail() {
  const { data, error, loading, lastUpdated, refresh } =
    usePolling<BiomassLiveResponse>({
      url: `${API_BASE}/api/resources/biomass/live`,
      intervalMs: 300000,
    });

  const ns = data?.national_summary;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-white">
          Biomass Energy — Bangladesh Potential
        </h2>
        <RefreshButton onClick={refresh} loading={loading && !data} variant="dark" />
        <DataBadge classification="CALCULATED_FROM_OFFICIAL_DATA" />
      </div>

      {loading && !data && <LoadingSkeleton lines={6} />}

      {error && !data && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm font-medium text-red-400">
            Failed to load biomass data: {error}
          </p>
          <button
            onClick={refresh}
            className="mt-2 text-sm font-medium text-red-400 underline hover:text-red-300"
          >
            Retry
          </button>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          {data.explanation && (
            <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
              <p className="text-sm text-blue-300">
                {data.explanation}
              </p>
            </div>
          )}

          {ns && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-slate-300">
                National Summary
              </h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                <MetricCard
                  label="Crop Residue"
                  value={ns.crop_residue_tonnes_year ?? null}
                  unit="tonnes/year"
                />
                <MetricCard
                  label="Animal Manure"
                  value={ns.animal_manure_tonnes_year ?? null}
                  unit="tonnes/year"
                />
                <MetricCard
                  label="Organic Waste"
                  value={ns.organic_waste_tonnes_year ?? null}
                  unit="tonnes/year"
                />
                <MetricCard
                  label="Biogas"
                  value={ns.biogas_m3_year ?? null}
                  unit="m³/year"
                />
                <MetricCard
                  label="Electricity Potential"
                  value={ns.electricity_potential_mwh_year ?? null}
                  unit="MWh/year"
                />
                <MetricCard
                  label="Average Potential"
                  value={ns.average_potential_mw ?? null}
                  unit="MW"
                />
                <MetricCard
                  label="Total Dispatchable"
                  value={ns.total_dispatchable_mw ?? null}
                  unit="MW"
                />
              </div>
            </div>
          )}

          {data.divisions && data.divisions.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-slate-300">
                Division Breakdown
              </h3>
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="min-w-full divide-y divide-slate-700">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                        Division
                      </th>
                      <th className="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                        PowerFlex Zone
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Crop Residue (t/yr)
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Animal Manure (t/yr)
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Organic Waste (t/yr)
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Electricity (MWh/yr)
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Avg MW
                      </th>
                      <th className="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                        Dispatchable MW
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700 bg-slate-900">
                    {data.divisions.map((d) => (
                      <tr key={d.division} className="hover:bg-slate-800">
                        <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-white">
                          {d.division}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-sm text-slate-400">
                          {d.powerflex_zone}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.crop_residue_tonnes_year)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.animal_manure_tonnes_year)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.organic_waste_tonnes_year)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.electricity_potential_mwh_year)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.average_potential_mw)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-right text-sm text-white">
                          {formatNumber(d.dispatchable_mw)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {data.sources && data.sources.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-slate-300">
                Sources
              </h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-400">
                {data.sources.map((src, i) => (
                  <li key={i}>
                    {typeof src === "object" && src !== null ? (
                      <>
                        {"name" in src ? String(src.name) : ""}
                        {"url" in src ? (
                          <> — <a href={String(src.url)} target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-400">{String(src.url)}</a></>
                        ) : null}
                      </>
                    ) : (
                      String(src)
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.retrieved_at && (
            <p className="text-xs text-slate-500">
              Retrieved: {data.retrieved_at}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
