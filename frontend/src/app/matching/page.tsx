"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { MatchCard } from "@/components/matching/MatchCard";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { LinkButton } from "@/components/ui/Button";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/ui/States";
import { formatDate } from "@/lib/format";

function MatchingInner() {
  const searchParams = useSearchParams();
  const jobParam = searchParams.get("job");
  const candidateParam = searchParams.get("candidate");

  const { data: jobs, error: jobsError, loading: jobsLoading, reload: reloadJobs } = useApi(
    () => api.jobs.list(),
    [],
  );
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

  // Selection: explicit user choice wins; otherwise fall back to ?job= or the
  // first job. Derived during render — no state-syncing effect needed.
  const jobId = selectedJobId ?? (jobParam ? Number(jobParam) : (jobs?.[0]?.id ?? null));

  const { data: matches, error, loading, reload } = useApi(
    () => (jobId ? api.matching.forJob(jobId, { limit: 25 }) : Promise.resolve([])),
    [jobId],
  );

  const focusCandidate = candidateParam ? Number(candidateParam) : null;

  if (jobsLoading && !jobs) return <LoadingBlock lines={6} />;
  if (jobsError && !jobs) return <ErrorState error={jobsError} onRetry={reloadJobs} />;

  if (!jobs || jobs.length === 0) {
    return (
      <EmptyState
        title="No jobs to match against yet"
        description="Create a job first — matching ranks every candidate against its extracted requirements."
        action={<LinkButton href="/jobs/new" size="sm">Create a job</LinkButton>}
      />
    );
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardBody className="flex flex-wrap items-center gap-3">
          <label htmlFor="job-select" className="text-sm font-medium text-slate-700">
            Match for job:
          </label>
          <select
            id="job-select"
            value={jobId ?? ""}
            onChange={(event) => setSelectedJobId(Number(event.target.value))}
            className="min-w-72 rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-indigo-600"
          >
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} — {job.company || "—"} ({job.status})
              </option>
            ))}
          </select>
          {jobId ? (
            <Link href={`/jobs/${jobId}`} className="text-xs font-medium text-indigo-600 hover:underline">
              Job details →
            </Link>
          ) : null}
          <span className="ml-auto text-xs text-slate-400">
            Ranking: composite score, then must-have coverage — never a black box
          </span>
        </CardBody>
      </Card>

      {loading && !matches ? (
        <LoadingBlock lines={8} />
      ) : error && !matches ? (
        <ErrorState error={error} onRetry={reload} />
      ) : matches && matches.length === 0 ? (
        <EmptyState
          title="No candidates in the pool yet"
          description="Upload resumes (or run the demo seed) and matching will rank them against this job's requirements."
          action={<LinkButton href="/candidates" size="sm">Upload resumes</LinkButton>}
        />
      ) : matches ? (
        <>
          <p className="text-xs text-slate-500">
            {matches.length} candidate{matches.length === 1 ? "" : "s"} evaluated on{" "}
            {formatDate(new Date().toISOString())} — every status below is auditable
            (met / partial / missing) with quoted evidence.
          </p>
          <div className="space-y-4">
            {matches.map((match) => (
              <MatchCard
                key={match.candidate_id}
                match={match}
                focus={focusCandidate === match.candidate_id}
                onPipelineChange={reload}
              />
            ))}
          </div>
        </>
      ) : null}

      <Card>
        <CardHeader title="How matching works" subtitle="The four layers — documented, not mysterious" />
        <CardBody>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm text-slate-600">
            <li>
              <strong>Deterministic requirement evaluation</strong> — each requirement gets
              met / partial / missing / unknown with a written reason.
            </li>
            <li>
              <strong>Normalized skill matching</strong> — aliases collapse to canonical skills;
              related-but-different skills earn partial credit only.
            </li>
            <li>
              <strong>Semantic similarity</strong> — a supporting signal, shown per requirement and
              overall; it never overrides a deterministic miss.
            </li>
            <li>
              <strong>Evidence extraction</strong> — quotes come verbatim from the candidate&apos;s own
              resume text.
            </li>
          </ol>
          <p className="mt-3 text-xs text-slate-400">
            No protected characteristics are used or inferred. AI assists; the recruiter decides.
            See RESPONSIBLE_AI.md in the repository.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

export default function MatchingPage() {
  return (
    <div>
      <PageHeader
        title="Matching"
        subtitle="Ranked, fully explained candidate matches for a job — coverage, gaps and quoted evidence for every requirement."
      />
      <Suspense fallback={<LoadingBlock lines={6} />}>
        <MatchingInner />
      </Suspense>
    </div>
  );
}
