import type { ReactNode } from "react";

import type { RequirementStatus, Stage } from "@/lib/types";
import { STAGE_LABELS, STAGE_STYLES, STATUS_STYLES, TAG_COLORS } from "@/lib/format";

export function Badge({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${className}`}
    >
      {children}
    </span>
  );
}

export function StageBadge({ stage }: { stage: Stage | string }) {
  const key = (stage as Stage) in STAGE_STYLES ? (stage as Stage) : "NEW";
  return (
    <Badge className={STAGE_STYLES[key]}>
      {STAGE_LABELS[key] ?? stage}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: RequirementStatus }) {
  const style = STATUS_STYLES[status];
  return (
    <Badge className={style.className}>
      <span aria-hidden className={`size-1.5 rounded-full ${style.dot}`} />
      {style.label}
    </Badge>
  );
}

export function TagBadge({ name, color = "slate" }: { name: string; color?: string }) {
  return <Badge className={TAG_COLORS[color] ?? TAG_COLORS.slate}>{name}</Badge>;
}

export function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      {children}
    </span>
  );
}

export function MethodBadge({ method }: { method: string }) {
  const isMock = method === "mock";
  return (
    <Badge
      className={isMock ? "bg-violet-50 text-violet-700 ring-violet-200" : "bg-sky-50 text-sky-700 ring-sky-200"}
    >
      {isMock ? "mock AI" : method === "openai" ? "OpenAI" : method}
    </Badge>
  );
}
