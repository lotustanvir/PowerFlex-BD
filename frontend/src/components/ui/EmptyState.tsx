"use client";

function EmptyState({
  title = "No data available",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-700/30 bg-slate-900/30 p-6 text-center">
      <p className="text-sm font-medium text-slate-400">{title}</p>
      {description && (
        <p className="mt-1 text-xs text-slate-500">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

export { EmptyState };
export default EmptyState;
