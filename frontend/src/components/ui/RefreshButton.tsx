"use client";

function RefreshButton({
  onClick,
  loading = false,
}: {
  onClick: () => void;
  loading?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
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
