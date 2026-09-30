"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, MethodBadge, StageBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { ErrorState, InlineError, LoadingBlock } from "@/components/ui/States";
import {
  CertificationsList,
  EducationList,
  ExperienceTimeline,
  ResumeTextCard,
  SkillChips,
  SummaryBlock,
} from "@/components/candidates/ProfileSections";
import { NotesPanel, TagsEditor } from "@/components/candidates/NotesAndTags";
import { ScreeningPanel } from "@/components/candidates/ScreeningPanel";
import { MatchedJobsPanel } from "@/components/candidates/MatchedJobsPanel";
import { StageControls } from "@/components/pipeline/StageControls";
import { formatDate, formatYears, initials } from "@/lib/format";
import type { Stage } from "@/lib/types";

export default function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const candidateId = Number(params.id);

  const { data: candidate, error, loading, reload } = useApi(
    () => api.candidates.get(candidateId),
    [candidateId],
  );
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function deleteCandidate() {
    if (!window.confirm("Delete this candidate? Their applications and notes are removed too.")) return;
    setBusy(true);
    try {
      await api.candidates.remove(candidateId);
      router.push("/candidates");
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not delete the candidate.");
      setBusy(false);
    }
  }

  async function moveStage(applicationId: number, toStage: Stage, note?: string) {
    setActionError(null);
    try {
      await api.applications.moveStage(applicationId, { to_stage: toStage, note });
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not move the stage.");
    }
  }

  if (loading && !candidate) return <LoadingBlock lines={8} />;
  if (error && !candidate)
    return (
      <div>
        <PageHeader title="Candidate" breadcrumb={<Link href="/candidates">← Candidates</Link>} />
        <ErrorState error={error} onRetry={reload} />
      </div>
    );
  if (!candidate) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumb={<Link href="/candidates" className="hover:text-indigo-600">← Candidates</Link>}
        title={
          <span className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
              {initials(candidate.full_name)}
            </span>
            {candidate.full_name}
          </span>
        }
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            <span>{candidate.headline ?? "—"}</span>
            {candidate.location ? <span>· {candidate.location}</span> : null}
            <span>· {formatYears(candidate.years_experience)} experience</span>
            <MethodBadge method={candidate.extraction_method} />
          </span>
        }
        action={
          <>
            {candidate.email ? (
              <a
                href={`mailto:${candidate.email}`}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                {candidate.email}
              </a>
            ) : null}
            {candidate.linkedin_url ? (
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                LinkedIn
              </a>
            ) : null}
            <Button variant="danger" size="sm" onClick={deleteCandidate} disabled={busy}>
              Delete
            </Button>
          </>
        }
      />

      {actionError ? <InlineError message={actionError} /> : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader title="Summary" />
            <CardBody>
              <SummaryBlock summary={candidate.summary} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Skills"
              subtitle={`${candidate.skills.length} extracted · click a skill to see its evidence line`}
            />
            <CardBody>
              <SkillChips skills={candidate.skills} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Experience" />
            <CardBody>
              <ExperienceTimeline experiences={candidate.experiences} />
            </CardBody>
          </Card>

          <div className="grid gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader title="Education" />
              <CardBody>
                <EducationList educations={candidate.educations} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title="Certifications" />
              <CardBody>
                <CertificationsList certifications={candidate.certifications} />
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardBody>
              <ResumeTextCard text={candidate.resume_text} filename={candidate.resume_filename} />
              <p className="mt-3 text-[11px] text-slate-500">
                Added {formatDate(candidate.created_at)} · parsed by {candidate.extraction_model ?? candidate.extraction_method}
              </p>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Tags" />
            <CardBody>
              <TagsEditor candidateId={candidateId} tags={candidate.tags} onChange={reload} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Pipeline" subtitle="Stages & audit-trailed moves" />
            <CardBody className="space-y-4">
              {candidate.applications.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Not in any pipeline yet.{" "}
                  <Link href="/matching" className="text-indigo-600 hover:underline">
                    Find a matching job →
                  </Link>
                </p>
              ) : (
                candidate.applications.map((application) => (
                  <div key={application.id} className="rounded-lg border border-slate-200 p-3">
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <Link
                        href={`/jobs/${application.job_id}`}
                        className="truncate text-sm font-medium text-slate-800 hover:text-indigo-600"
                      >
                        {application.job_title}
                      </Link>
                      <StageBadge stage={application.stage} />
                    </div>
                    <StageControls
                      stage={application.stage}
                      onMove={(toStage, note) => moveStage(application.id, toStage, note)}
                    />
                  </div>
                ))
              )}
            </CardBody>
          </Card>

          <MatchedJobsPanel candidateId={candidateId} />

          <Card>
            <CardHeader
              title="Screening questions"
              subtitle="Candidate-specific, grounded in match results"
              action={
                <Badge className="bg-violet-50 text-violet-700 ring-violet-200">AI-assisted</Badge>
              }
            />
            <CardBody>
              <ScreeningPanel applications={candidate.applications} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Recruiter notes" subtitle="Persisted with author + timestamp" />
            <CardBody>
              <NotesPanel candidateId={candidateId} notes={candidate.notes} onChange={reload} />
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
