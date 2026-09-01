"use client";

const colorMap: Record<string, string> = {
  OFFICIAL_PGCB: "bg-green-100 text-green-800",
  LIVE: "bg-blue-100 text-blue-800",
  STALE: "bg-yellow-100 text-yellow-800",
  MODEL_FORECAST: "bg-yellow-100 text-yellow-800",
  CALCULATED_FROM_OFFICIAL_DATA: "bg-purple-100 text-purple-800",
  STATIC_DOCUMENTED_DATA: "bg-gray-100 text-gray-800",
  DATA_UNAVAILABLE: "bg-red-100 text-red-800",
  PROTOTYPE: "bg-orange-100 text-orange-800",
  NOT_CONNECTED: "bg-red-100 text-red-800",
  PLANNED: "bg-indigo-100 text-indigo-800",
};

function DataBadge({ classification }: { classification: string }) {
  const colors = colorMap[classification] ?? "bg-gray-100 text-gray-600";

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colors}`}
    >
      {classification.replace(/_/g, " ")}
    </span>
  );
}

export { DataBadge };
export default DataBadge;
