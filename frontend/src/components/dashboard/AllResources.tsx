"use client";

import { usePolling } from "@/hooks/usePolling";
import type { ResourcesLiveResponse } from "@/lib/types";
import { API_BASE } from "@/lib/api";
import DataBadge from "@/components/ui/DataBadge";
import StatusIndicator from "@/components/ui/StatusIndicator";
import RefreshButton from "@/components/ui/RefreshButton";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
const POLL_INTERVAL = 60000;

const RESOURCE_ORDER = [
  "solar",
  "wind",
  "hydro",
  "biomass",
  "waste",
  "gas",
  "liquid_fuel",
  "coal",
  "nuclear",
] as const;

const RESOURCE_LABELS: Record<string, string> = {
  solar: "Solar",
  wind: "Wind",
  hydro: "Hydro",
  biomass: "Biomass",
  waste: "Waste",
  gas: "Gas",
  liquid_fuel: "Liquid Fuel",
  coal: "Coal",
  nuclear: "Nuclear",
};

function ResourceCard({
  resource,
  item,
}: {
  resource: string;
  item: {
    generation_mw: number | null;
    installed_capacity_mw: number | null;
    resource_status: string;
    source_metadata: { source: string; data_classification: string };
    note: string;
  };
}) {
  const isNuclear = resource === "nuclear";

  const generationDisplay =
    item.generation_mw === null
      ? isNuclear
        ? "Generation: Not available"
        : "N/A"
      : `${item.generation_mw} MW`;

  const capacityDisplay =
    item.installed_capacity_mw === null
      ? "N/A"
      : `${item.installed_capacity_mw} MW`;

  const statusDisplay = isNuclear && item.resource_status === "UNDER_COMMISSIONING"
    ? "UNDER_COMMISSIONING"
    : item.resource_status;

  const classification =
    resource === "battery" || resource === "flexible_demand"
      ? "PROTOTYPE"
      : item.source_metadata.data_classification;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4 transition-shadow hover:shadow-md">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold text-white">
          {RESOURCE_LABELS[resource] ?? resource}
        </h3>
        <DataBadge classification={classification} />
      </div>

      <dl className="space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-400">Generation</dt>
          <dd className="font-medium text-white">{generationDisplay}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400">Installed Capacity</dt>
          <dd className="font-medium text-white">{capacityDisplay}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400">Status</dt>
          <dd className="font-medium text-white">{statusDisplay}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400">Source</dt>
          <dd className="font-medium text-white">
            {item.source_metadata.source || "N/A"}
          </dd>
        </div>
      </dl>

      {item.note && (
        <p className="mt-3 rounded-md bg-slate-900/40 p-2 text-xs text-slate-400">
          {item.note}
        </p>
      )}
    </div>
  );
}

export default function AllResources() {
  const { data, error, loading, lastUpdated, refresh } =
    usePolling<ResourcesLiveResponse>({
      url: `${API_BASE}/api/resources/live`,
      intervalMs: POLL_INTERVAL,
    });

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            Bangladesh Electricity Resources
          </h2>
          <p className="text-sm text-slate-400">
            {data ? `${data.resource_count} resources tracked` : "Loading..."}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <StatusIndicator
            live={!!data}
            lastUpdated={lastUpdated}
          />
          <RefreshButton onClick={refresh} loading={loading} variant="dark" />
        </div>
      </div>

      {error && !data && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm font-medium text-red-400">
            Failed to load resources: {error}
          </p>
          <button
            onClick={refresh}
            className="mt-2 text-sm font-medium text-red-400 underline hover:text-red-300"
          >
            Retry
          </button>
        </div>
      )}

      {loading && !data && <LoadingSkeleton lines={6} />}

      {data && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {RESOURCE_ORDER.map((key) => {
            const item = data.resources[key];
            if (!item) return null;
            return <ResourceCard key={key} resource={key} item={item} />;
          })}
        </div>
      )}
    </section>
  );
}
