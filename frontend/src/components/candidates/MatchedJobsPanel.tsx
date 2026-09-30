"use client";

import Link from "next/link";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { LoadingBlock } from "@/components/ui/States";
import { formatScore, scoreBar, scoreTone } from "@/lib/format";

/** Top open jobs for a candidate, ranked by the explainable matching engine. */
export function MatchedJobsPanel({ candidateId }: { candidateId: number }) {
  const { data, loading, error } = useApi(() => api.matching.forCandidate(candidateId, 3), [candidateId]);

  return (
    <Card>
      <CardHeader
        title="Best-fit jobs"
        subtitle="Ranked by the transparent matching engine"
        action={
          <Link href="/matching" className="text-xs font-medium text-indigo-600 hover:underline">
            Matching →
          </Link>
        }
      />
      <CardBody>
        {loading && !data ? (
          <LoadingBlock lines={2} />
        ) : error ? (
          <p className="text-sm text-slate-500">Could not load matches.</p>
        ) : !data || data.length === 0 ? (
          <p className="text-sm text-slate-500">No open jobs to match against yet.</p>
        ) : (
          <ul className="space-y-3">
            {data.map((match) => (
              <li key={match.job_id}>
                <div className="flex items-center justify-between gap-2">
                  <Link
                    href={`/matching?job=${match.job_id}&candidate=${candidateId}`}
                    className="truncate text-sm font-medium text-slate-800 hover:text-indigo-600"
                  >
                    {match.job_title}
                  </Link>
                  <span className={`text-sm font-semibold ${scoreTone(match.composite_score)}`}>
                    {formatScore(match.composite_score)}
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${scoreBar(match.composite_score)}`}
                    style={{ width: `${match.composite_score ?? 0}%` }}
                  />
                </div>
                <p className="mt-0.5 text-[11px] text-slate-500">
                  {match.coverage.must_have.met}/{match.coverage.must_have.total} must-haves met
                  {match.stage ? ` · in pipeline: ${match.stage}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
