"use client";

function LiveIndicator({
  status,
  lastUpdated,
  label,
}: {
  status: "live" | "cached" | "delayed" | "degraded" | "unavailable" | "error";
  lastUpdated?: Date | null;
  label?: string;
}) {
  const config = {
    live: { dot: "bg-emerald-400", text: "text-emerald-400", ping: true, label: "LIVE" },
    cached: { dot: "bg-blue-400", text: "text-blue-400", ping: false, label: "CACHED" },
    delayed: { dot: "bg-amber-400", text: "text-amber-400", ping: false, label: "DELAYED" },
    degraded: { dot: "bg-orange-400", text: "text-orange-400", ping: false, label: "DEGRADED" },
    unavailable: { dot: "bg-slate-500", text: "text-slate-500", ping: false, label: "UNAVAILABLE" },
    error: { dot: "bg-red-400", text: "text-red-400", ping: false, label: "ERROR" },
  };

  const c = config[status] || config.unavailable;
  const displayLabel = label || c.label;

  return (
    <div className="inline-flex items-center gap-1.5" role="status" aria-label={`Status: ${displayLabel}`}>
      <span className="relative flex h-2 w-2">
        {c.ping && (
          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${c.dot}`} />
        )}
        <span className={`relative inline-flex h-2 w-2 rounded-full ${c.dot}`} />
      </span>
      <span className={`text-[10px] font-semibold uppercase tracking-wider ${c.text}`}>
        {displayLabel}
      </span>
      {lastUpdated && (
        <span className="text-[9px] text-slate-600">
          {lastUpdated.toLocaleTimeString("en-US", {
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

export { LiveIndicator };
export default LiveIndicator;
