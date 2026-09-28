import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  accent = "slate",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: "slate" | "indigo" | "emerald" | "amber" | "violet";
}) {
  const accents: Record<string, string> = {
    slate: "border-slate-200",
    indigo: "border-indigo-200",
    emerald: "border-emerald-200",
    amber: "border-amber-200",
    violet: "border-violet-200",
  };
  return (
    <div className={`rounded-xl border bg-white px-5 py-4 shadow-sm ${accents[accent]}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function ProgressBar({
  value,
  max = 100,
  tone = "bg-indigo-500",
  label,
}: {
  value: number;
  max?: number;
  tone?: string;
  label?: string;
}) {
  const pct = max <= 0 ? 0 : Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      {label ? <p className="mt-1 text-[11px] text-slate-500">{label}</p> : null}
    </div>
  );
}
