"use client";

interface RefreshButtonProps {
  onClick: () => void;
  loading?: boolean;
  variant?: "light" | "dark";
}

function RefreshButton({
  onClick,
  loading = false,
  variant = "dark",
}: RefreshButtonProps) {
  const baseClasses =
    "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium shadow-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50";

  const variantClasses =
    variant === "dark"
      ? "border border-slate-600 bg-slate-700 text-slate-200 hover:bg-slate-600"
      : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50";

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`${baseClasses} ${variantClasses}`}
    >
      <span
        className={`text-base leading-none ${loading ? "animate-spin" : ""}`}
      >
        ↻
      </span>
      Refresh
    </button>
  );
}

export { RefreshButton };
export default RefreshButton;
