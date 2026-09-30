/** Formatting + display helpers shared across the UI. */

import type { Stage, RequirementStatus } from "@/lib/types";

export const STAGES: Stage[] = [
  "NEW",
  "SCREENING",
  "SHORTLISTED",
  "INTERVIEW",
  "OFFER",
  "HIRED",
  "REJECTED",
];

/** Board columns in workflow order (REJECTED shown last). */
export const BOARD_STAGES: Stage[] = STAGES;

/** The "advance" order — REJECTED is a terminal offramp, not a step. */
export const ADVANCE_STAGES: Stage[] = ["NEW", "SCREENING", "SHORTLISTED", "INTERVIEW", "OFFER", "HIRED"];

export const STAGE_LABELS: Record<Stage, string> = {
  NEW: "New",
  SCREENING: "Screening",
  SHORTLISTED: "Shortlisted",
  INTERVIEW: "Interview",
  OFFER: "Offer",
  HIRED: "Hired",
  REJECTED: "Rejected",
};

export const STAGE_STYLES: Record<Stage, string> = {
  NEW: "bg-slate-100 text-slate-700 ring-slate-200",
  SCREENING: "bg-sky-50 text-sky-700 ring-sky-200",
  SHORTLISTED: "bg-violet-50 text-violet-700 ring-violet-200",
  INTERVIEW: "bg-amber-50 text-amber-800 ring-amber-200",
  OFFER: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  HIRED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  REJECTED: "bg-rose-50 text-rose-700 ring-rose-200",
};

export const STATUS_STYLES: Record<RequirementStatus, { label: string; className: string; dot: string }> = {
  met: { label: "Met", className: "bg-emerald-50 text-emerald-700 ring-emerald-200", dot: "bg-emerald-500" },
  partial: { label: "Partial", className: "bg-amber-50 text-amber-800 ring-amber-200", dot: "bg-amber-500" },
  missing: { label: "Missing", className: "bg-rose-50 text-rose-700 ring-rose-200", dot: "bg-rose-500" },
  unknown: { label: "Unknown", className: "bg-slate-100 text-slate-600 ring-slate-200", dot: "bg-slate-400" },
  advisory: { label: "Signal", className: "bg-violet-50 text-violet-700 ring-violet-200", dot: "bg-violet-400" },
};

export const TAG_COLORS: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  rose: "bg-rose-50 text-rose-700 ring-rose-200",
  violet: "bg-violet-50 text-violet-700 ring-violet-200",
  sky: "bg-sky-50 text-sky-700 ring-sky-200",
  teal: "bg-teal-50 text-teal-700 ring-teal-200",
};

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMonth(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { month: "short", year: "numeric" });
}

export function formatYears(years: number | null | undefined): string {
  if (years === null || years === undefined) return "—";
  return `${years % 1 === 0 ? years : years.toFixed(1)} yrs`;
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return `${score.toFixed(1)}`;
}

export function scoreTone(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-slate-500";
  if (score >= 75) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-rose-600";
}

export function scoreBar(score: number | null | undefined): string {
  if (score === null || score === undefined) return "bg-slate-300";
  if (score >= 75) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-rose-500";
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function percent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export const COMPONENT_LABELS: Record<string, string> = {
  must_have: "Must-have coverage",
  preferred: "Preferred coverage",
  experience: "Experience alignment",
  domain: "Domain alignment",
};
