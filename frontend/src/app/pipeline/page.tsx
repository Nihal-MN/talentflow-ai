"use client";

import Link from "next/link";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { StageControls } from "@/components/pipeline/StageControls";
import { Badge } from "@/components/ui/Badge";
import { Card, PageHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, InlineError, LoadingBlock } from "@/components/ui/States";
import { BOARD_STAGES, STAGE_LABELS, formatDateTime } from "@/lib/format";
import type { Application, Stage } from "@/lib/types";

export default function PipelinePage() {
  const { data: jobs } = useApi(() => api.jobs.list(), []);
  const [jobFilter, setJobFilter] = useState<number | "all">("all");
  const { data: board, error, loading, reload } = useApi(
    () => api.applications.board(jobFilter === "all" ? {} : { job_id: jobFilter }),
    [jobFilter],
  );
  const [actionError, setActionError] = useState<string | null>(null);

  async function move(application: Application, toStage: Stage, note?: string) {
    setActionError(null);
    try {
      await api.applications.moveStage(application.id, { to_stage: toStage, note });
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not move the stage.");
    }
  }

  const total = board
    ? Object.values(board).reduce((sum, applications) => sum + applications.length, 0)
    : 0;

  return (
    <div>
      <PageHeader
        title="Pipeline"
        subtitle="Every move is recorded in an audit trail — NEW through HIRED, with REJECTED as an off-ramp."
        action={
          <select
            aria-label="Filter by job"
            value={jobFilter}
            onChange={(event) =>
              setJobFilter(event.target.value === "all" ? "all" : Number(event.target.value))
            }
            className="rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300"
          >
            <option value="all">All jobs</option>
            {(jobs ?? []).map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        }
      />

      {actionError ? (
        <div className="mb-4">
          <InlineError message={actionError} />
        </div>
      ) : null}

      {loading && !board ? (
        <LoadingBlock lines={6} />
      ) : error && !board ? (
        <ErrorState error={error} onRetry={reload} />
      ) : total === 0 ? (
        <EmptyState
          title="The pipeline is empty"
          description="Run matching for a job and add candidates to see them flow through the stages here."
        />
      ) : board ? (
        <div className="scroll-thin -mx-2 flex snap-x gap-3 overflow-x-auto px-2 pb-4">
          {BOARD_STAGES.map((stage) => {
            const applications = board[stage] ?? [];
            return (
              <section
                key={stage}
                aria-label={`${STAGE_LABELS[stage]} column`}
                className={`flex w-64 shrink-0 snap-start flex-col rounded-xl border bg-slate-50/80 ${
                  stage === "REJECTED" ? "border-rose-100" : "border-slate-200"
                }`}
              >
                <header className="flex items-center justify-between px-3 py-2.5">
                  <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                    {STAGE_LABELS[stage]}
                  </h2>
                  <Badge className="bg-white text-slate-500 ring-slate-200">{applications.length}</Badge>
                </header>
                <div className="scroll-thin flex max-h-[70vh] flex-col gap-2 overflow-y-auto px-2 pb-3">
                  {applications.length === 0 ? (
                    <p className="px-1 py-2 text-xs text-slate-500">No candidates</p>
                  ) : (
                    applications.map((application) => (
                      <Card key={application.id} className="p-3">
                        <Link
                          href={`/candidates/${application.candidate_id}`}
                          className="block truncate text-sm font-medium text-slate-800 hover:text-indigo-600"
                        >
                          {application.candidate.full_name}
                        </Link>
                        <p className="truncate text-xs text-slate-600">{application.job.title}</p>
                        <p className="mt-0.5 text-[11px] text-slate-500">
                          updated {formatDateTime(application.updated_at)}
                        </p>
                        <div className="mt-2">
                          <StageControls
                            stage={application.stage}
                            compact
                            onMove={(toStage, note) => move(application, toStage, note)}
                          />
                        </div>
                      </Card>
                    ))
                  )}
                </div>
              </section>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
