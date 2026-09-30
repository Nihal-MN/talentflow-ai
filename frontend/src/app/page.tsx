"use client";

import Link from "next/link";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, StageBadge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { LinkButton } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { ProgressBar, StatCard } from "@/components/ui/StatCard";
import { ADVANCE_STAGES, STAGE_LABELS, formatDateTime } from "@/lib/format";
import type { Application, Health, Activity } from "@/lib/types";
import type { Stage } from "@/lib/types";

async function loadDashboard() {
  const [health, board, activity] = await Promise.all([
    api.health.full(),
    api.applications.board(),
    api.applications.activity(8),
  ]);
  return { health, board, activity };
}

export default function DashboardPage() {
  const { data, error, loading, reload } = useApi(loadDashboard, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Live recruiting overview — every number below is computed from the database, nothing is hard-coded."
        action={
          <>
            <LinkButton href="/jobs/new" size="sm">
              Create job
            </LinkButton>
            <LinkButton href="/candidates" variant="secondary" size="sm">
              Upload resumes
            </LinkButton>
          </>
        }
      />

      {loading && !data ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="skeleton h-24" />
          ))}
        </div>
      ) : error && !data ? (
        <ErrorState error={error} onRetry={reload} />
      ) : data ? (
        <DashboardContent health={data.health} board={data.board} activity={data.activity} />
      ) : null}
    </div>
  );
}

function DashboardContent({
  health,
  board,
  activity,
}: {
  health: Health;
  board: Record<Stage, Application[]>;
  activity: Activity[];
}) {
  const totals = ADVANCE_STAGES.map((stage) => ({
    stage,
    count: (board[stage] ?? []).length,
  }));
  const maxCount = Math.max(1, ...totals.map((entry) => entry.count));
  const rejected = (board.REJECTED ?? []).length;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Open jobs"
          value={health.counts.open_jobs}
          hint={`${health.counts.jobs} total`}
          accent="indigo"
        />
        <StatCard label="Candidates" value={health.counts.candidates} hint="in the talent pool" />
        <StatCard
          label="Applications"
          value={health.counts.applications}
          hint="across all pipelines"
          accent="violet"
        />
        <StatCard
          label="AI mode"
          value={health.ai.provider === "mock" ? "Mock" : "OpenAI"}
          hint={health.ai.model}
          accent={health.ai.provider === "mock" ? "amber" : "emerald"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader
            title="Pipeline snapshot"
            subtitle={`${health.counts.applications} applications in play`}
            action={
              <Link href="/pipeline" className="text-xs font-medium text-indigo-600 hover:underline">
                Open board →
              </Link>
            }
          />
          <CardBody className="space-y-3">
            {health.counts.applications === 0 ? (
              <EmptyState
                title="No candidates in the pipeline yet"
                description="Add candidates to a job from the matching page to see the funnel build up."
                action={<LinkButton href="/matching" size="sm">Run matching</LinkButton>}
              />
            ) : (
              totals.map(({ stage, count }) => (
                <div key={stage} className="flex items-center gap-3">
                  <span className="w-24 text-xs font-medium text-slate-600">
                    {STAGE_LABELS[stage]}
                  </span>
                  <div className="flex-1">
                    <ProgressBar
                      value={count}
                      max={maxCount}
                      tone={
                        stage === "HIRED"
                          ? "bg-emerald-500"
                          : stage === "OFFER"
                            ? "bg-indigo-500"
                            : "bg-sky-500"
                      }
                    />
                  </div>
                  <span className="w-8 text-right text-xs font-semibold text-slate-700">{count}</span>
                </div>
              ))
            )}
            {rejected > 0 ? (
              <p className="pt-1 text-xs text-slate-500">
                {rejected} rejected {rejected === 1 ? "candidate" : "candidates"} (not shown above)
              </p>
            ) : null}
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Recent activity" subtitle="Stage changes, newest first" />
          <CardBody>
            {activity.length === 0 ? (
              <p className="text-sm text-slate-500">No pipeline activity yet.</p>
            ) : (
              <ul className="space-y-3">
                {activity.map((event, index) => (
                  <li key={`${event.application_id}-${index}`} className="flex items-start gap-3">
                    <div className="mt-1">
                      <StageBadge stage={event.to_stage} />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm text-slate-800">
                        <Link
                          href={`/candidates/${event.candidate_id}`}
                          className="font-medium hover:text-indigo-600"
                        >
                          {event.candidate_name}
                        </Link>{" "}
                        <span className="text-slate-500">
                          {event.from_stage ? `→ ${event.to_stage}` : "added to"}
                        </span>{" "}
                        <Link href={`/jobs/${event.job_id}`} className="text-slate-500 hover:text-indigo-600">
                          {event.job_title}
                        </Link>
                      </p>
                      <p className="text-xs text-slate-500">{formatDateTime(event.at)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Badge className="bg-emerald-50 text-emerald-700 ring-emerald-200">
              API {health.status}
            </Badge>
            <Badge className="bg-slate-100 text-slate-700 ring-slate-200">
              DB: {health.database.dialect}
            </Badge>
            <span className="text-xs text-slate-500">
              v{health.version} · {new Date(health.time).toLocaleString("en-GB")}
            </span>
          </div>
          <Link href="/health" className="text-xs font-medium text-indigo-600 hover:underline">
            System health →
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}
