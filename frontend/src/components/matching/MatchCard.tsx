"use client";

import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { Badge, StageBadge, StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { InlineError } from "@/components/ui/States";
import {
  COMPONENT_LABELS,
  formatScore,
  percent,
  scoreBar,
  scoreTone,
} from "@/lib/format";
import type { Evidence, MatchResult, RequirementEvaluation } from "@/lib/types";

export function ScoreBreakdown({ match }: { match: MatchResult }) {
  const components = Object.entries(match.components).filter(([, value]) => value !== null);
  return (
    <div className="space-y-2">
      {components.map(([name, value]) => (
        <div key={name} className="flex items-center gap-2">
          <span className="w-36 text-xs text-slate-500">
            {COMPONENT_LABELS[name] ?? name}
            {match.weights_used[name] !== undefined ? (
              <span className="text-slate-400"> ×{match.weights_used[name].toFixed(2)}</span>
            ) : null}
          </span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-400"
              style={{ width: `${(value ?? 0) * 100}%` }}
            />
          </div>
          <span className="w-10 text-right text-xs font-medium text-slate-600">
            {percent(value)}
          </span>
        </div>
      ))}
      <p className="pt-1 font-mono text-[11px] leading-relaxed text-slate-500">{match.formula}</p>
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return null;
  return (
    <ul className="mt-1.5 space-y-1.5">
      {evidence.map((item, index) => (
        <li
          key={index}
          className={`rounded-md border-l-2 px-2.5 py-1.5 text-xs leading-relaxed ${
            item.match_type === "semantic"
              ? "border-violet-300 bg-violet-50/60 text-slate-700"
              : item.match_type === "computed"
                ? "border-sky-300 bg-sky-50/60 text-slate-700"
                : "border-slate-300 bg-slate-50 text-slate-700"
          }`}
        >
          <span className="mr-1.5 rounded bg-white px-1 py-0.5 font-mono text-[10px] uppercase text-slate-400 ring-1 ring-slate-200">
            {item.match_type}
          </span>
          “{item.snippet}”
          {item.detail ? <span className="ml-1 text-slate-400">({item.detail})</span> : null}
        </li>
      ))}
    </ul>
  );
}

function RequirementRow({ evaluation }: { evaluation: RequirementEvaluation }) {
  const [open, setOpen] = useState(false);
  const hasDetail = evaluation.evidence.length > 0 || evaluation.reason.length > 0;
  return (
    <li className="py-2">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-start gap-2 text-left"
      >
        <span className="mt-0.5">
          <StatusBadge status={evaluation.status} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm text-slate-800">
            {evaluation.skill ? (
              <span className="mr-1.5 rounded bg-indigo-50 px-1.5 py-0.5 font-mono text-xs font-medium text-indigo-700">
                {evaluation.skill}
              </span>
            ) : null}
            {evaluation.label}
          </span>
        </span>
        {hasDetail ? (
          <span aria-hidden className="mt-0.5 text-xs text-slate-400">
            {open ? "▾" : "▸"}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="ml-1 mt-1 border-l-2 border-slate-100 pl-4">
          <p className="text-xs leading-relaxed text-slate-500">{evaluation.reason}</p>
          {evaluation.similarity !== null ? (
            <p className="mt-1 text-xs text-slate-400">
              Semantic similarity to profile: {evaluation.similarity.toFixed(2)}
            </p>
          ) : null}
          <EvidenceList evidence={evaluation.evidence} />
        </div>
      ) : null}
    </li>
  );
}

export function MatchCard({
  match,
  focus = false,
  onPipelineChange,
}: {
  match: MatchResult;
  focus?: boolean;
  onPipelineChange?: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const must = match.requirements.filter((requirement) => requirement.kind === "must_have");
  const preferred = match.requirements.filter((requirement) => requirement.kind === "preferred");
  const mustShown = showAll ? must : must.slice(0, 6);

  async function addToPipeline() {
    setAdding(true);
    setError(null);
    try {
      await api.applications.create({ candidate_id: match.candidate_id, job_id: match.job_id });
      onPipelineChange?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to the pipeline.");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div
      id={`match-${match.candidate_id}`}
      className={`rounded-xl border bg-white shadow-sm ${
        focus ? "border-indigo-400 ring-2 ring-indigo-100" : "border-slate-200"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">{match.candidate_name}</h3>
            {match.stage ? <StageBadge stage={match.stage} /> : null}
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            {match.coverage.must_have.met}/{match.coverage.must_have.total} must-haves met ·{" "}
            {match.coverage.must_have.partial} partial · {match.coverage.must_have.missing} missing
            {match.semantic_similarity !== null ? (
              <> · text similarity {match.semantic_similarity.toFixed(2)}</>
            ) : null}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className={`text-2xl font-semibold tabular-nums ${scoreTone(match.composite_score)}`}>
              {formatScore(match.composite_score)}
              <span className="text-xs font-normal text-slate-400">/100</span>
            </p>
            <div className="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${scoreBar(match.composite_score)}`}
                style={{ width: `${match.composite_score ?? 0}%` }}
              />
            </div>
          </div>
          {match.application_id ? (
            <Badge className="bg-slate-100 text-slate-600 ring-slate-200">in pipeline</Badge>
          ) : (
            <Button size="sm" onClick={addToPipeline} loading={adding}>
              Add to pipeline
            </Button>
          )}
        </div>
      </div>

      {error ? (
        <div className="px-5 pt-3">
          <InlineError message={error} />
        </div>
      ) : null}

      <div className="grid gap-5 px-5 py-4 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            How this score is computed
          </p>
          <ScoreBreakdown match={match} />
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Must-have requirements
          </p>
          <ul className="divide-y divide-slate-100">
            {mustShown.map((requirement) => (
              <RequirementRow key={requirement.requirement_id} evaluation={requirement} />
            ))}
          </ul>
          {must.length > 6 ? (
            <button
              type="button"
              onClick={() => setShowAll((value) => !value)}
              className="mt-2 text-xs font-medium text-indigo-600 hover:underline"
            >
              {showAll ? "Show fewer" : `Show all ${must.length} must-haves`}
            </button>
          ) : null}
          {preferred.length > 0 ? (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs font-medium text-slate-500 hover:text-slate-700">
                Preferred requirements ({preferred.length})
              </summary>
              <ul className="mt-1 divide-y divide-slate-100">
                {preferred.map((requirement) => (
                  <RequirementRow key={requirement.requirement_id} evaluation={requirement} />
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      </div>

      <div className="border-t border-slate-100 px-5 py-2.5">
        <p className="text-[11px] text-slate-400">
          Engine {match.engine_version} · generated {new Date(match.generated_at).toLocaleString("en-GB")} ·
          evidence quotes come from the candidate&apos;s own resume — the decision stays with you.
        </p>
      </div>
    </div>
  );
}
