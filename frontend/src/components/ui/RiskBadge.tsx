"use client";

const RISK_CONFIG: Record<string, { text: string; bg: string; border: string }> = {
  LOW: { text: "text-emerald-400", bg: "bg-emerald-500/12", border: "border-emerald-500/25" },
  MODERATE: { text: "text-amber-400", bg: "bg-amber-500/12", border: "border-amber-500/25" },
  ELEVATED: { text: "text-orange-400", bg: "bg-orange-500/12", border: "border-orange-500/25" },
  HIGH: { text: "text-red-400", bg: "bg-red-500/12", border: "border-red-500/25" },
  CRITICAL: { text: "text-red-300", bg: "bg-red-500/15", border: "border-red-500/30" },
};

function RiskBadge({ level, className = "" }: { level: string; className?: string }) {
  const config = RISK_CONFIG[level] || { text: "text-slate-400", bg: "bg-slate-500/12", border: "border-slate-500/25" };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${config.text} ${config.bg} ${config.border} ${className}`}
      role="status"
      aria-label={`Risk level: ${level}`}
    >
      {level}
    </span>
  );
}

export { RiskBadge };
export default RiskBadge;
