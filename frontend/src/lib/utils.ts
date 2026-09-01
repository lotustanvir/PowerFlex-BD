export function fmtMw(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return `${v.toLocaleString()} MW`;
}

export function fmtNum(v: number | null | undefined): string {
  if (v == null) return "N/A";
  return v.toLocaleString();
}

export function fmtStr(v: unknown): string {
  if (v == null) return "N/A";
  return String(v);
}
