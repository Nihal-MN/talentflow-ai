"use client";

import Link from "next/link";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, StageBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, InlineError, LoadingBlock } from "@/components/ui/States";
import { formatDateTime } from "@/lib/format";
import type { ScreeningQuestion } from "@/lib/types";

const CATEGORY_STYLES: Record<string, string> = {
  technical: "bg-sky-50 text-sky-700 ring-sky-200",
  gap_probe: "bg-amber-50 text-amber-800 ring-amber-200",
  experience: "bg-violet-50 text-violet-700 ring-violet-200",
  behavioral: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export default function ScreeningPage() {
  const { data, error, loading, reload } = useApi(
    async () => ({
      sets: await api.screening.list(),
      applications: await api.applications.list({}),
    }),
    [],
  );

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<ScreeningQuestion[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const effectiveId = selectedId ?? data?.sets[0]?.application_id ?? data?.applications[0]?.id ?? null;

  const { data: stored, loading: questionsLoading, reload: reloadQuestions } = useApi(
    () => (effectiveId ? api.screening.forApplication(effectiveId) : Promise.resolve([])),
    [effectiveId],
  );

  const shown = questions ?? stored ?? [];

  async function generate() {
    if (!effectiveId) return;
    setBusy(true);
    setActionError(null);
    try {
      const generated = await api.screening.generate(effectiveId);
      setQuestions(generated);
      reloadQuestions();
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not generate questions.");
    } finally {
      setBusy(false);
    }
  }

  if (loading && !data) return <LoadingBlock lines={6} />;
  if (error && !data) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  const selectedApplication = data.applications.find((application) => application.id === effectiveId);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-1">
        <PageHeader
          title="Screening"
          subtitle="Candidate-specific question sets — grounded in the match results, never in protected characteristics."
        />
        <Card>
          <CardHeader title="Question sets" subtitle={`${data.sets.length} stored`} />
          <CardBody className="space-y-2">
            {data.sets.length === 0 ? (
              <p className="text-sm text-slate-500">
                No sets yet. Pick an application on the right and generate the first one.
              </p>
            ) : (
              data.sets.map((set) => (
                <button
                  key={set.application_id}
                  type="button"
                  onClick={() => {
                    setSelectedId(set.application_id);
                    setQuestions(null);
                  }}
                  className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                    effectiveId === set.application_id
                      ? "border-indigo-300 bg-indigo-50/60"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-slate-800">
                      {set.candidate_name}
                    </span>
                    <StageBadge stage={set.stage} />
                  </div>
                  <p className="truncate text-xs text-slate-500">{set.job_title}</p>
                  <p className="mt-0.5 text-[11px] text-slate-400">
                    {set.question_count} questions · {set.source} ·{" "}
                    {set.created_at ? formatDateTime(set.created_at) : "—"}
                  </p>
                </button>
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <div className="space-y-6 lg:col-span-2">
        <Card>
          <CardBody className="flex flex-wrap items-center gap-3">
            <label htmlFor="application-select" className="text-sm font-medium text-slate-700">
              Application:
            </label>
            <select
              id="application-select"
              value={effectiveId ?? ""}
              onChange={(event) => {
                setSelectedId(Number(event.target.value));
                setQuestions(null);
              }}
              className="min-w-72 rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300"
            >
              {data.applications.length === 0 ? (
                <option value="">No applications yet</option>
              ) : (
                data.applications.map((application) => (
                  <option key={application.id} value={application.id}>
                    {application.candidate.full_name} — {application.job.title} ({application.stage})
                  </option>
                ))
              )}
            </select>
            <Button size="sm" onClick={generate} loading={busy} disabled={!effectiveId}>
              {shown.length > 0 ? "Regenerate" : "Generate questions"}
            </Button>
            {selectedApplication ? (
              <Link
                href={`/candidates/${selectedApplication.candidate_id}`}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                Open candidate →
              </Link>
            ) : null}
          </CardBody>
        </Card>

        {actionError ? <InlineError message={actionError} /> : null}

        {data.applications.length === 0 ? (
          <EmptyState
            title="No applications yet"
            description="Add candidates to a job pipeline first — screening questions are generated per application."
          />
        ) : questionsLoading && shown.length === 0 ? (
          <LoadingBlock lines={5} />
        ) : shown.length === 0 ? (
          <EmptyState
            title="No questions for this application"
            description="Generate a set — it will probe the strongest matches, the missing must-haves, and seniority-calibrated behaviors."
          />
        ) : (
          <Card>
            <CardHeader
              title="Questions"
              subtitle={`${shown.length} questions · generated by ${shown[0]?.source === "mock" ? "deterministic mock rules" : "OpenAI"}`}
            />
            <CardBody>
              <ul className="space-y-3">
                {shown.map((question) => (
                  <li key={question.id} className="rounded-lg bg-slate-50 px-3 py-3">
                    <div className="mb-1 flex items-center gap-2">
                      <Badge
                        className={
                          CATEGORY_STYLES[question.category] ??
                          "bg-slate-100 text-slate-600 ring-slate-200"
                        }
                      >
                        {question.category.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-800">{question.question}</p>
                    {question.rationale ? (
                      <p className="mt-1 text-xs italic text-slate-500">{question.rationale}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
