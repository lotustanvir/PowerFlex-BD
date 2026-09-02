"use client";

const colorMap: Record<string, string> = {
  OFFICIAL_PGCB: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
  LIVE: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
  STALE: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  MODEL_FORECAST: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  CALCULATED_FROM_OFFICIAL_DATA: "bg-purple-500/15 text-purple-400 border border-purple-500/30",
  STATIC_DOCUMENTED_DATA: "bg-slate-500/15 text-slate-400 border border-slate-500/30",
  DATA_UNAVAILABLE: "bg-red-500/15 text-red-400 border border-red-500/30",
  PROTOTYPE: "bg-orange-500/15 text-orange-400 border border-orange-500/30",
  NOT_CONNECTED: "bg-red-500/15 text-red-400 border border-red-500/30",
  PLANNED: "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30",
  WAITING_FOR_GRID_DATA: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  DATA_INCOMPLETE: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  FORECAST: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
  CALCULATED: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
};

function DataBadge({ classification }: { classification: string }) {
  const colors = colorMap[classification] ?? "bg-slate-500/15 text-slate-400 border border-slate-500/30";

  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${colors}`}
      title={classification.replace(/_/g, " ")}
    >
      {classification.replace(/_/g, " ")}
    </span>
  );
}

export { DataBadge };
export default DataBadge;
