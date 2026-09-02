"use client";

function ErrorState({
  message = "Something went wrong",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/8 p-4" role="alert">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/20">
            <svg className="h-3 w-3 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </span>
          <p className="text-xs text-red-400">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 text-[10px] font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

export { ErrorState };
export default ErrorState;
