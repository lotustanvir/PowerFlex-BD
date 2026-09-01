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
      <span className="text-sm font-medium text-gray-700">
        {label ?? (live ? "LIVE" : "OFFLINE")}
      </span>
      {lastUpdated && (
        <span className="text-xs text-gray-400">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}

export { StatusIndicator };
export default StatusIndicator;
