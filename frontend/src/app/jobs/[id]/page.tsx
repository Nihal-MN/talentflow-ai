"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, MethodBadge, StageBadge } from "@/components/ui/Badge";
import { Button, LinkButton } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { ErrorState, InlineError, LoadingBlock } from "@/components/ui/States";
import { formatDate, formatDateTime } from "@/lib/format";
import type { Requirement } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = Number(params.id);

  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const { data: job, error, loading, reload } = useApi(() => api.jobs.get(jobId), [jobId]);

  async function changeStatus(status: string) {
    setBusy(true);
    setActionError(null);
    try {
      await api.jobs.update(jobId, { status });
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not update the job.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteJob() {
    if (!window.confirm("Delete this job? Applications in its pipeline will be removed too.")) return;
    setBusy(true);
    try {
      await api.jobs.remove(jobId);
      router.push("/jobs");
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not delete the job.");
      setBusy(false);
    }
  }

  if (loading && !job) return <LoadingBlock lines={6} />;
  if (error && !job)
    return (
      <div>
        <PageHeader title="Job" breadcrumb={<Link href="/jobs">← Jobs</Link>} />
        <ErrorState error={error} onRetry={reload} />
      </div>
    );
  if (!job) return null;

  const must = job.requirements.filter((requirement) => requirement.kind === "must_have");
  const preferred = job.requirements.filter((requirement) => requirement.kind === "preferred");

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumb={<Link href="/jobs" className="hover:text-indigo-600">← Jobs</Link>}
        title={job.title}
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            <span>{job.company || "—"}</span>
            {job.location ? <span>· {job.location}</span> : null}
            {job.seniority ? <span>· {job.seniority} level</span> : null}
            {job.domain ? <span>· {job.domain}</span> : null}
            <MethodBadge method={job.extraction_method} />
          </span>
        }
        action={
          <>
            <LinkButton href={`/matching?job=${job.id}`} size="sm">
              Match candidates
            </LinkButton>
            <select
              aria-label="Job status"
              value={job.status}
              disabled={busy}
              onChange={(event) => changeStatus(event.target.value)}
              className="rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300"
            >
              <option value="open">Open</option>
              <option value="paused">Paused</option>
              <option value="closed">Closed</option>
            </select>
            <Button variant="danger" size="sm" onClick={deleteJob} disabled={busy}>
              Delete
            </Button>
          </>
        }
      />

      {actionError ? <InlineError message={actionError} /> : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Requirements"
            subtitle={`${must.length} must-have · ${preferred.length} preferred — extracted from the job description`}
          />
          <CardBody className="space-y-6">
            <RequirementGroup title="Must-have" requirements={must} />
            <RequirementGroup title="Preferred" requirements={preferred} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Pipeline"
            subtitle={`${job.applications.length} ${job.applications.length === 1 ? "application" : "applications"}`}
            action={
              <Link href="/pipeline" className="text-xs font-medium text-indigo-600 hover:underline">
                Board →
              </Link>
            }
          />
          <CardBody>
            {job.applications.length === 0 ? (
              <p className="text-sm text-slate-500">
                No candidates added yet. Run matching to find the best fits and add them here.
              </p>
            ) : (
              <ul className="space-y-3">
                {job.applications.map((application) => (
                  <li key={application.id} className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <Link
                        href={`/candidates/${application.candidate_id}`}
                        className="block truncate text-sm font-medium text-slate-800 hover:text-indigo-600"
                      >
                        {application.candidate_name}
                      </Link>
                      <p className="truncate text-xs text-slate-400">
                        updated {formatDateTime(application.updated_at)}
                      </p>
                    </div>
                    <StageBadge stage={application.stage} />
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Job description"
          subtitle={`Source: ${job.source === "upload" ? "uploaded file" : "pasted text"} · created ${formatDate(job.created_at)}`}
        />
        <CardBody>
          <details>
            <summary className="cursor-pointer text-sm font-medium text-indigo-600 hover:underline">
              Show original text
            </summary>
            <pre className="mt-3 max-h-96 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700">
              {job.description_text}
            </pre>
          </details>
        </CardBody>
      </Card>
    </div>
  );
}

function RequirementGroup({ title, requirements }: { title: string; requirements: Requirement[] }) {
  if (requirements.length === 0) {
    return (
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
        <p className="text-sm text-slate-400">None extracted.</p>
      </div>
    );
  }
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <ul className="divide-y divide-slate-100">
        {requirements.map((requirement) => (
          <li key={requirement.id} className="flex flex-wrap items-center gap-2 py-2.5">
            <Badge className="bg-slate-100 text-slate-600 ring-slate-200">{requirement.category}</Badge>
            {requirement.normalized_skill ? (
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                {requirement.normalized_skill}
              </span>
            ) : null}
            {requirement.min_years ? (
              <span className="rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
                {requirement.min_years}+ yrs
              </span>
            ) : null}
            <span className="min-w-0 flex-1 text-sm text-slate-700">{requirement.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
