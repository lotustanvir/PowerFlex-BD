"use client";

function StatusIndicator({
  live,
  label,
  lastUpdated,
}: {
  live: boolean;
  label?: string;
  lastUpdated?: Date | null;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {live && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 bg-green-400" />
        )}
        <span
          className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
            live ? "bg-green-500" : "bg-red-500"
          }`}
        />
      </span>
      <span className="text-[10px] font-medium text-slate-400">
        {label ?? (live ? "LIVE" : "OFFLINE")}
      </span>
      {lastUpdated && (
        <span className="text-[10px] text-slate-600">
          {lastUpdated.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Dhaka" })}
        </span>
      )}
    </div>
  );
}

export { StatusIndicator };
export default StatusIndicator;
