"use client";

function SectionHeader({
  children,
  action,
}: {
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-500">
        {children}
      </h2>
      {action && <div>{action}</div>}
    </div>
  );
}

export { SectionHeader };
export default SectionHeader;
